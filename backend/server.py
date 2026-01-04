"""
作为 AI 服务的中间层
"""

import os
import re
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
from pytz import timezone
from dotenv import load_dotenv

from plugin_manager import plugin_manager

config_path = Path(__file__).parent / 'config.env'
load_dotenv(config_path)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 配置常量
DEBUG_MODE = os.getenv('DebugMode', 'false').lower() == 'true'
SHOW_VCP_OUTPUT = os.getenv('ShowVCP', 'false').lower() == 'true'
PORT = int(os.getenv('PORT', 6005))
API_KEY = os.getenv('API_Key')
API_URL = os.getenv('API_URL')
SERVER_KEY = os.getenv('Key')

DEBUG_LOG_DIR = Path(__file__).parent / 'DebugLog'

# 表情包缓存
cached_emoji_lists: Dict[str, str] = {}

# 加载系统提示词转换规则
detectors = []
for key in os.environ:
    if re.match(r'^Detector\d+$', key):
        index = key[8:]  # 移除 'Detector' 前缀
        output_key = f'Detector_Output{index}'
        if os.getenv(output_key):
            detectors.append({
                'detector': os.getenv(key),
                'output': os.getenv(output_key)
            })

if detectors:
    logger.info(f"共加载了 {len(detectors)} 条系统提示词转换规则")
else:
    logger.info('未加载任何系统提示词转换规则')

# 加载全局上下文转换规则
super_detectors = []
for key in os.environ:
    if re.match(r'^SuperDetector\d+$', key):
        index = key[13:]  # 移除 'SuperDetector' 前缀
        output_key = f'SuperDetector_Output{index}'
        if os.getenv(output_key):
            super_detectors.append({
                'detector': os.getenv(key),
                'output': os.getenv(output_key)
            })

if super_detectors:
    logger.info(f"共加载了 {len(super_detectors)} 条全局上下文转换规则")
else:
    logger.info('未加载任何全局上下文转换规则')


# ==================== 工具函数 ====================

async def ensure_debug_log_dir():
    """确保调试日志目录存在"""
    if DEBUG_MODE:
        DEBUG_LOG_DIR.mkdir(parents=True, exist_ok=True)


async def write_debug_log(filename_prefix: str, data: Any):
    """写入调试日志"""
    if DEBUG_MODE:
        await ensure_debug_log_dir()
        now = datetime.now()
        timestamp = now.strftime('%Y%m%d_%H%M%S_%f')
        filename = f"{filename_prefix}-{timestamp}.txt"
        filepath = DEBUG_LOG_DIR / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json.dumps(data, indent=2, ensure_ascii=False))
            logger.info(f"[DebugLog] 已记录日志: {filename}")
        except Exception as e:
            logger.error(f"写入调试日志失败: {filepath}, 错误: {e}")


def get_current_time(format_str: str = '%Y年%m月%d日', tz: str = 'Asia/Shanghai') -> str:
    """获取当前时间"""
    now = datetime.now(timezone(tz))
    return now.strftime(format_str)


# ==================== 变量替换系统 ====================

async def replace_common_variables(text: Any) -> Any:
    """
    替换通用变量占位符
    支持: {{Date}}, {{Time}}, {{Today}}, {{Festival}}, {{VCPWeatherInfo}} 等
    """
    if text is None:
        return ''

    processed_text = str(text)
    now = datetime.now(timezone('Asia/Shanghai'))

    # 时间变量
    date_str = now.strftime('%Y年%m月%d日')
    processed_text = processed_text.replace('{{Date}}', date_str)

    time_str = now.strftime('%H:%M:%S')
    processed_text = processed_text.replace('{{Time}}', time_str)

    today_str = now.strftime('%A')
    processed_text = processed_text.replace('{{Today}}', today_str)

    # 农历日期
    try:
        from zhdate import ZhDate
        lunar = ZhDate.from_datetime(now)
        year_name = lunar.chinesestate.replace('年', '')
        zodiac = lunar.chinese_era[0]  # 生肖
        festival_info = f"{year_name}{zodiac}年{lunar.chinesedate}"
        processed_text = processed_text.replace('{{Festival}}', festival_info)
    except ImportError:
        # 如果没有安装 zhdate，使用简单替换
        processed_text = processed_text.replace('{{Festival}}', date_str)
    except Exception as e:
        logger.warning(f"农历日期转换失败: {e}")
        processed_text = processed_text.replace('{{Festival}}', date_str)

    # Var 开头的环境变量
    for key in os.environ:
        if key.startswith('Var'):
            placeholder = f'{{{{{key}}}}}'
            value = os.getenv(key, '')
            processed_text = processed_text.replace(placeholder, value or f'未配置{key}')

    # EmojiPrompt
    if os.getenv('EmojiPrompt'):
        processed_text = processed_text.replace('{{EmojiPrompt}}', os.getenv('EmojiPrompt'))

    # 插件变量
    weather_info = plugin_manager.get_placeholder_value("{{VCPWeatherInfo}}")
    processed_text = processed_text.replace('{{VCPWeatherInfo}}', weather_info)

    # 单个插件描述
    individual_descriptions = plugin_manager.get_individual_plugin_descriptions()
    for placeholder_key, description in individual_descriptions.items():
        processed_text = processed_text.replace(f'{{{{{placeholder_key}}}}}', description)

    # Port
    if os.getenv('PORT'):
        processed_text = processed_text.replace('{{Port}}', os.getenv('PORT'))

    # Image_Key
    image_key = plugin_manager.get_resolved_plugin_config_value('ImageServer', 'Image_Key')
    if image_key:
        processed_text = processed_text.replace('{{Image_Key}}', image_key)

    # EmojiList
    if '{{EmojiList}}' in processed_text and os.getenv('EmojiList'):
        emoji_list_file = os.getenv('EmojiList')
        emoji_cache_key = emoji_list_file.replace('.txt', '').strip()
        emoji_content = cached_emoji_lists.get(emoji_cache_key)
        if emoji_content is not None:
            processed_text = processed_text.replace('{{EmojiList}}', emoji_content)
        else:
            processed_text = processed_text.replace(
                '{{EmojiList}}',
                f"[名为 {emoji_cache_key} 的表情列表不可用]"
            )

    # 表情包占位符 {{xxx表情包}}
    emoji_pattern = re.compile(r'\{\{(.+?表情包)\}\}')
    for match in emoji_pattern.finditer(processed_text):
        placeholder = match.group(0)
        emoji_name = match.group(1)
        emoji_list = cached_emoji_lists.get(emoji_name)
        if emoji_list:
            processed_text = processed_text.replace(placeholder, emoji_list)
        else:
            processed_text = processed_text.replace(
                placeholder,
                f'{emoji_name}列表不可用'
            )

    # 日记本占位符 {{xxx日记本}}
    diary_pattern = re.compile(r'\{\{(.+?)日记本\}\}')
    processed_characters = set()

    for match in diary_pattern.finditer(processed_text):
        placeholder = match.group(0)
        character_name = match.group(1)

        if character_name in processed_characters:
            continue

        processed_characters.add(character_name)
        diary_dir = Path(__file__).parent / 'dailynote' / character_name
        diary_content = f"[{character_name}日记本内容为空或不存在]"

        try:
            if diary_dir.exists():
                txt_files = sorted(diary_dir.glob('*.txt'))
                if txt_files:
                    file_contents = []
                    for txt_file in txt_files:
                        try:
                            content = txt_file.read_text(encoding='utf-8')
                            file_contents.append(content)
                        except Exception as e:
                            file_contents.append(f"[读取文件 {txt_file.name} 失败]")
                    diary_content = '\n\n---\n\n'.join(file_contents)
        except Exception as e:
            logger.error(f"读取 {character_name} 日记目录出错: {e}")
            diary_content = f"[读取{character_name}日记时出错]"

        processed_text = processed_text.replace(placeholder, diary_content)

    # 系统提示词转换规则
    for rule in detectors:
        detector = rule.get('detector', '')
        output = rule.get('output', '')
        if detector and output:
            processed_text = processed_text.replace(detector, output)

    # 全局上下文转换规则
    for rule in super_detectors:
        detector = rule.get('detector', '')
        output = rule.get('output', '')
        if detector and output:
            processed_text = processed_text.replace(detector, output)

    return processed_text


async def replace_variables_in_messages(messages: List[dict]) -> List[dict]:
    """对消息列表进行变量替换"""
    result = []
    for msg in messages:
        new_msg = msg.copy()

        if isinstance(new_msg.get('content'), str):
            new_msg['content'] = await replace_common_variables(msg['content'])
        elif isinstance(new_msg.get('content'), list):
            new_content = []
            for part in msg['content']:
                new_part = part.copy()
                if part.get('type') == 'text' and isinstance(part.get('text'), str):
                    new_part['text'] = await replace_common_variables(part['text'])
                new_content.append(new_part)
            new_msg['content'] = new_content

        result.append(new_msg)

    return result


# ==================== VCP 协议解析 ====================

def parse_vcp_request(content: str) -> Optional[dict]:
    """
    解析 VCP 工具调用请求
    返回: {'tool_name': str, 'args': dict} 或 None
    """
    start_marker = "<<<[TOOL_REQUEST]>>>"
    end_marker = "<<<[END_TOOL_REQUEST]>>>"

    start_idx = content.find(start_marker)
    if start_idx == -1:
        return None

    end_idx = content.find(end_marker, start_idx)
    if end_idx == -1:
        return None

    request_block = content[start_idx + len(start_marker):end_idx].strip()

    # 解析参数: key:「始」value「末」
    param_pattern = r'([\w_]+)\s*:\s*「始」([\s\S]*?)「末」\s*(?:,)?'

    params = {}
    tool_name = None

    for match in re.finditer(param_pattern, request_block):
        key = match.group(1)
        value = match.group(2).strip()

        if key == 'tool_name':
            tool_name = value
        else:
            params[key] = value

    if tool_name:
        return {'tool_name': tool_name, 'args': params}

    return None


def parse_multiple_vcp_requests(content: str) -> List[dict]:
    """
    解析多个 VCP 工具调用请求
    返回: [{'tool_name': str, 'args': dict}, ...]
    """
    requests = []
    search_offset = 0

    while True:
        start_marker = "<<<[TOOL_REQUEST]>>>"
        end_marker = "<<<[END_TOOL_REQUEST]>>>"

        start_idx = content.find(start_marker, search_offset)
        if start_idx == -1:
            break

        end_idx = content.find(end_marker, start_idx)
        if end_idx == -1:
            break

        request_block = content[start_idx + len(start_marker):end_idx].strip()

        # 解析参数
        param_pattern = r'([\w_]+)\s*:\s*「始」([\s\S]*?)「末」\s*(?:,)?'

        params = {}
        tool_name = None

        for match in re.finditer(param_pattern, request_block):
            key = match.group(1)
            value = match.group(2).strip()

            if key == 'tool_name':
                tool_name = value
            else:
                params[key] = value

        if tool_name:
            requests.append({'tool_name': tool_name, 'args': params})

        search_offset = end_idx + len(end_marker)

    return requests


# ==================== 日记系统 ====================

async def handle_daily_note(note_block_content: str):
    """
    处理日记内容
    格式:
        Maid: xxx
        Date: xxx
        Content: xxx
    """
    lines = note_block_content.strip().split('\n')
    maid_name = None
    date_string = None
    content_lines = []
    is_content_section = False

    for line in lines:
        trimmed = line.strip()

        if trimmed.startswith('Maid:'):
            maid_name = trimmed[5:].strip()
            is_content_section = False
        elif trimmed.startswith('Date:'):
            date_string = trimmed[5:].strip()
            is_content_section = False
        elif trimmed.startswith('Content:'):
            is_content_section = True
            first_content = trimmed[8:].strip()
            if first_content:
                content_lines.append(first_content)
        elif is_content_section:
            content_lines.append(line)

    content_text = '\n'.join(content_lines).strip()

    if not all([maid_name, date_string, content_text]):
        logger.error(f"[handleDailyNote] 无法完整提取 Maid, Date, 或 Content")
        return

    # 格式化日期
    date_part = date_string.replace('.', '.').replace('-', '.')

    now = datetime.now()
    time_string = now.strftime('%H_%M_%S')

    dir_path = Path(__file__).parent / 'dailynote' / maid_name
    filename = f"{date_part}-{time_string}.txt"
    filepath = dir_path / filename

    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"[{date_part}] - {maid_name}\n{content_text}")
        logger.info(f"[handleDailyNote] 日记文件写入成功: {filepath}")
    except Exception as e:
        logger.error(f"[handleDailyNote] 处理日记文件时出错: {e}")


async def handle_diary_from_ai_response(response_text: str):
    """从 AI 响应中提取和处理日记"""
    if not response_text or not response_text.strip():
        return

    full_ai_response_text = ''

    # 判断是否为 SSE 格式
    lines = response_text.strip().split('\n')
    looks_like_sse = any(line.startswith('data: ') for line in lines)

    if looks_like_sse:
        # 解析 SSE 格式
        sse_content = ''
        for line in lines:
            if line.startswith('data: '):
                json_data = line[5:].strip()
                if json_data == '[DONE]':
                    continue
                try:
                    parsed = json.loads(json_data)
                    content_chunk = (
                        parsed.get('choices', [{}])[0].get('delta', {}).get('content') or
                        parsed.get('choices', [{}])[0].get('message', {}).get('content') or
                        ''
                    )
                    if content_chunk:
                        sse_content += content_chunk
                except json.JSONDecodeError:
                    pass
        full_ai_response_text = sse_content
    else:
        # 尝试解析为 JSON
        try:
            parsed = json.loads(response_text)
            full_ai_response_text = parsed.get('choices', [{}])[0].get('message', {}).get('content') or ''
        except json.JSONDecodeError:
            full_ai_response_text = response_text

    if not full_ai_response_text.strip():
        return

    # 提取日记内容
    diary_pattern = re.compile(r'<<<DailyNoteStart>>>(.*?)<<<DailyNoteEnd>>>', re.DOTALL)
    match = diary_pattern.search(full_ai_response_text)

    if match:
        note_content = match.group(1).strip()
        logger.info('[DailyNote Check] 找到结构化日记')
        await handle_daily_note(note_content)


# ==================== 表情包系统 ====================

async def update_and_load_emoji_list(agent_name: str, dir_path: Path, file_path: Path) -> str:
    """更新并加载表情包列表"""
    print(f"尝试更新 {agent_name} 表情包列表...")

    try:
        image_files = []
        if dir_path.exists():
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.JPG', '*.JPEG', '*.PNG', '*.GIF']:
                image_files.extend(dir_path.glob(ext))

        new_list = '|'.join([f.name for f in image_files])

        file_path.write_text(new_list, encoding='utf-8')
        print(f"{agent_name} 表情包列表已更新并写入 {file_path}")
        return new_list

    except Exception as e:
        error_msg = f"更新 {agent_name} 表情包列表时出错: {e}"
        print(error_msg)
        return error_msg


async def initialize_emoji_lists():
    """初始化表情包列表"""
    print('开始初始化表情包列表...')

    image_dir = Path(__file__).parent / 'image'

    try:
        if not image_dir.exists():
            print(f"警告: image 目录 {image_dir} 不存在")
            return

        entries = [e for e in image_dir.iterdir() if e.is_dir()]
        emoji_dirs = [e for e in entries if e.name.endswith('表情包')]

        if not emoji_dirs:
            print(f"警告: 在 {image_dir} 目录下未找到任何以 '表情包' 结尾的文件夹")
            return

        print(f"找到 {len(emoji_dirs)} 个表情包目录，开始加载...")

        for emoji_dir in emoji_dirs:
            emoji_name = emoji_dir.name
            txt_file = Path(__file__).parent / f'{emoji_name}.txt'

            try:
                content = await update_and_load_emoji_list(emoji_name, emoji_dir, txt_file)
                cached_emoji_lists[emoji_name] = content
            except Exception as e:
                print(f"加载 {emoji_name} 列表时出错: {e}")
                cached_emoji_lists[emoji_name] = f'{emoji_name}列表加载失败'

        print('所有表情包列表加载完成。')

    except Exception as e:
        print(f"读取 image 目录 {image_dir} 时出错: {e}")

    print('表情包列表初始化结束。')


# ==================== FastAPI 应用 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info('开始加载插件...')
    await plugin_manager.load_plugins()
    logger.info('插件加载完成。')

    plugin_manager.set_project_base_path(str(Path(__file__).parent))

    logger.info('开始初始化服务类插件...')
    # 注意: initialize_services 需要 app 实例，在路由设置后再调用
    logger.info('服务类插件初始化完成。')

    logger.info('开始初始化静态插件...')
    await plugin_manager.initialize_static_plugins()
    logger.info('静态插件初始化完成。')

    await initialize_emoji_lists()

    yield

    # 关闭时
    logger.info('Initiating graceful shutdown...')
    await plugin_manager.shutdown_all_plugins()
    logger.info('Graceful shutdown complete.')


app = FastAPI(lifespan=lifespan)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """请求日志中间件"""
    logger.info(f"Received {request.method} request for {request.url.path} from {request.client.host}")
    return await call_next(request)


# ==================== 路由 ====================

@app.get("/")
async def root():
    """根路径"""
    return {"message": "VCPToolBox Server (Python)"}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    处理聊天完成请求
    这是核心功能，处理图片预处理、变量替换、工具调用等
    """
    try:
        original_body = await request.json()
        await write_debug_log('LogInput', original_body)

        # ==================== 1. 图片预处理 ====================
        should_process_images = True

        if 'messages' in original_body:
            for msg in original_body['messages']:
                content = msg.get('content', '')
                found_placeholder = False

                if isinstance(content, str) and '{{ShowBase64}}' in content:
                    found_placeholder = True
                    msg['content'] = content.replace('{{ShowBase64}}', '')
                elif isinstance(content, list):
                    for part in content:
                        if part.get('type') == 'text' and '{{ShowBase64}}' in part.get('text', ''):
                            found_placeholder = True
                            part['text'] = part['text'].replace('{{ShowBase64}}', '')

                if found_placeholder:
                    should_process_images = False
                    logger.info('[Server] Image processing disabled by {{ShowBase64}} placeholder')
                    break

        if should_process_images:
            logger.info('[Server] Image processing enabled, calling ImageProcessor plugin...')
            try:
                original_body['messages'] = await plugin_manager.execute_message_preprocessor(
                    "ImageProcessor", original_body['messages']
                )
                logger.info('[Server] ImageProcessor plugin finished.')
            except Exception as e:
                logger.error(f'[Server] Error executing ImageProcessor plugin: {e}')

        # ==================== 2. 变量替换 ====================
        if 'messages' in original_body:
            original_body['messages'] = await replace_variables_in_messages(original_body['messages'])

        await write_debug_log('LogOutputAfterProcessing', original_body)

        # ==================== 3. 调用 AI API ====================
        is_streaming = original_body.get('stream', False)

        async with httpx.AsyncClient(timeout=300.0) as client:
            ai_response = await client.post(
                f"{API_URL}/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {API_KEY}",
                    "User-Agent": request.headers.get("user-agent", "VCPToolBox/1.0"),
                    "Accept": "text/event-stream" if is_streaming else "application/json",
                },
                json=original_body
            )

        # ==================== 4. 处理响应 ====================
        if is_streaming:
            # 流式响应处理
            return await handle_streaming_response(ai_response, original_body, request)
        else:
            # 非流式响应处理
            return await handle_non_streaming_response(ai_response, original_body, request)

    except Exception as e:
        logger.error(f'处理请求时出错: {e}')
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error", "details": str(e)}
        )


async def handle_streaming_response(ai_response: httpx.Response, original_body: dict, request: Request):
    """
    处理流式 AI 响应
    支持: 检测工具调用，执行插件，进行第二次 AI 调用
    """
    async def generate_stream():
        """内部生成器函数，产生流式响应"""
        # 收集完整的流式响应内容
        full_content = ''
        line_buffer = ''

        # 第一阶段: 转发原始流式响应
        async for chunk in ai_response.aiter_bytes():
            chunk_str = chunk.decode('utf-8', errors='ignore')
            full_content += chunk_str
            line_buffer += chunk_str

            # 按行分割处理
            lines = line_buffer.split('\n')
            line_buffer = lines.pop()  # 保留最后一行（可能不完整）

            # 转发完整的行
            for line in lines:
                if line.strip() and line.strip() != 'data: [DONE]':
                    yield f'{line}\n'
                elif line.strip() == '':
                    yield '\n'

        # 处理剩余的 buffer
        if line_buffer.strip() and line_buffer.strip() != 'data: [DONE]':
            yield f'{line_buffer}\n'

        # 从 SSE 数据中提取实际内容
        sse_content = ''
        for line in full_content.split('\n'):
            if line.startswith('data: '):
                json_data = line[5:].strip()
                if json_data == '[DONE]':
                    continue
                try:
                    parsed = json.loads(json_data)
                    content_chunk = parsed.get('choices', [{}])[0].get('delta', {}).get('content') or ''
                    if content_chunk:
                        sse_content += content_chunk
                except json.JSONDecodeError:
                    pass

        logger.info(f'[PluginCall] AI First Full Response Text: {sse_content[:200]}...')

        # 检查是否有工具调用
        vcp_request = parse_vcp_request(sse_content)
        needs_second_ai_call = vcp_request is not None

        if needs_second_ai_call:
            # 有工具调用，需要执行并返回第二次 AI 调用
            yield 'data: [TOOL_CALL_DETECTED]\n\n'

            # 准备第二次调用的消息
            messages_for_next_call = original_body.get('messages', []).copy()
            messages_for_next_call.append({'role': 'assistant', 'content': sse_content})

            tool_name = vcp_request['tool_name']
            tool_args = vcp_request['args']

            try:
                logger.info(f"[PluginCall] Executing tool: {tool_name} with args: {tool_args}")
                plugin_result = await plugin_manager.process_tool_call(tool_name, tool_args)

                if plugin_result is not None:
                    message_content = f"来自工具 \"{tool_name}\" 的结果:\n{json.dumps(plugin_result, ensure_ascii=False, indent=2)}"
                else:
                    message_content = f"来自工具 \"{tool_name}\" 的结果:\n插件 {tool_name} 执行完毕，但没有返回明确内容。"

                messages_for_next_call.append({'role': 'user', 'content': message_content})

                # 第二次 AI 调用
                logger.info('[PluginCall] Proceeding with second AI call with tool results')
                await write_debug_log('LogOutputWithPluginCall_BeforeSecondCall', {
                    'messages': messages_for_next_call,
                    'originalRequestBody': original_body
                })

                async with httpx.AsyncClient(timeout=300.0) as client:
                    second_response = await client.post(
                        f"{API_URL}/v1/chat/completions",
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {API_KEY}",
                            "User-Agent": request.headers.get("user-agent", "VCPToolBox/1.0"),
                            "Accept": "text/event-stream",
                        },
                        json={**original_body, 'messages': messages_for_next_call}
                    )

                # 流式转发第二次 AI 响应
                second_full_text = ''
                async for chunk in second_response.aiter_bytes():
                    chunk_str = chunk.decode('utf-8', errors='ignore')
                    second_full_text += chunk_str
                    yield chunk_str

                yield 'data: [DONE]\n\n'

                # 处理日记
                await handle_diary_from_ai_response(second_full_text)

            except Exception as e:
                logger.error(f'[PluginCall] Error during tool execution or second AI call: {e}')
                import traceback
                traceback.print_exc()
                yield f"data: {{'error': '{str(e)}'}}\n\n"
                yield 'data: [DONE]\n\n'
                await handle_diary_from_ai_response(full_content)
        else:
            # 没有工具调用，结束流
            yield 'data: [DONE]\n\n'
            # 处理日记
            await handle_diary_from_ai_response(full_content)

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


async def handle_non_streaming_response(
    ai_response: httpx.Response,
    original_body: dict,
    request: Request
):
    """处理非流式 AI 响应（支持多轮工具调用）"""
    response_text = ai_response.content.decode('utf-8')
    await write_debug_log('LogFirstAIResponse', response_text)

    try:
        response_json = json.loads(response_text)
        full_content_from_ai = response_json.get('choices', [{}])[0].get('message', {}).get('content', '')
    except json.JSONDecodeError:
        full_content_from_ai = response_text

    # 检查是否有工具调用
    vcp_requests = parse_multiple_vcp_requests(full_content_from_ai)

    if not vcp_requests:
        # 没有工具调用，直接返回
        await handle_diary_from_ai_response(response_text)
        return Response(content=ai_response.content, media_type="application/json")

    # 处理多轮工具调用
    max_recursion = 5
    conversation_history = []
    current_ai_content = full_content_from_ai
    current_messages = original_body.get('messages', []).copy()

    for recursion_depth in range(max_recursion):
        # 添加 AI 响应到历史
        conversation_history.append({'type': 'ai', 'content': current_ai_content})

        # 检查当前 AI 响应中的工具调用
        vcp_requests = parse_multiple_vcp_requests(current_ai_content)

        if not vcp_requests:
            # 没有更多工具调用，退出循环
            break

        # 添加 AI 响应到消息历史
        current_messages.append({'role': 'assistant', 'content': current_ai_content})

        # 执行所有工具调用
        tool_results = []
        for tool_request in vcp_requests:
            tool_name = tool_request['tool_name']
            tool_args = tool_request['args']

            try:
                logger.info(f"[Multi-Tool] Executing tool: {tool_name} with args: {tool_args}")
                plugin_result = await plugin_manager.process_tool_call(tool_name, tool_args)

                if SHOW_VCP_OUTPUT:
                    conversation_history.append({
                        'type': 'vcp',
                        'content': f"工具 {tool_name} 调用结果:\n{plugin_result}"
                    })

                tool_results.append(f"来自工具 \"{tool_name}\" 的结果:\n{plugin_result}")

            except Exception as e:
                logger.error(f"[Multi-Tool] Error executing plugin {tool_name}: {e}")
                error_msg = f"执行插件 {tool_name} 时发生错误：{str(e)}"
                if SHOW_VCP_OUTPUT:
                    conversation_history.append({'type': 'vcp', 'content': error_msg})
                tool_results.append(error_msg)

        # 添加工具结果到消息历史
        combined_results = "\n\n---\n\n".join(tool_results)
        current_messages.append({'role': 'user', 'content': combined_results})

        # 调用下一轮 AI
        logger.info("[Multi-Tool] Fetching next AI response after processing tools")

        async with httpx.AsyncClient(timeout=300.0) as client:
            next_response = await client.post(
                f"{API_URL}/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {API_KEY}",
                },
                json={**original_body, 'messages': current_messages, 'stream': False}
            )

        next_response_text = next_response.content.decode('utf-8')

        try:
            next_response_json = json.loads(next_response_text)
            current_ai_content = next_response_json.get('choices', [{}])[0].get('message', {}).get('content', '')
        except json.JSONDecodeError:
            current_ai_content = next_response_text

    # 构建最终响应
    final_content = ''
    for item in conversation_history:
        if item['type'] == 'ai':
            final_content += item['content']
        elif item['type'] == 'vcp' and SHOW_VCP_OUTPUT:
            final_content += f"\n<<<[VCP_RESULT]>>>\n{item['content']}\n<<<[END_VCP_RESULT]>>>\n"

    # 添加最后的 AI 响应
    final_content += current_ai_content

    # 构建响应 JSON
    try:
        final_json = json.loads(response_text)
        if not final_json.get('choices'):
            final_json['choices'] = [{}]
        final_json['choices'][0]['message']['content'] = final_content
        final_json['choices'][0]['finish_reason'] = 'stop'
    except json.JSONDecodeError:
        final_json = {
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": final_content
                },
                "finish_reason": "stop"
            }]
        }

    await handle_diary_from_ai_response(response_text)

    return JSONResponse(content=final_json)


# ==================== Admin API 路由 ====================

BASE_DIR = Path(__file__).parent
PLUGIN_DIR = BASE_DIR / 'plugins'
MANIFEST_FILE = 'plugin-manifest.json'
BLOCKED_EXTENSION = '.block'


@app.get("/admin_api/config/main")
async def get_main_config():
    """获取主配置文件内容（过滤敏感信息）"""
    try:
        config_path = BASE_DIR / 'config.env'
        content = config_path.read_text(encoding='utf-8')
        # 过滤敏感信息
        filtered_lines = []
        for line in content.split('\n'):
            if not re.match(r'^\s*(AdminPassword|AdminUsername)\s*=', line, re.IGNORECASE):
                filtered_lines.append(line)
        filtered_content = '\n'.join(filtered_lines)
        return {'content': filtered_content}
    except Exception as e:
        logger.error('Error reading main config for admin panel:', e)
        raise HTTPException(status_code=500, detail=f'Failed to read main config file: {str(e)}')


@app.get("/admin_api/config/main/raw")
async def get_main_config_raw():
    """获取原始主配置文件内容"""
    try:
        config_path = BASE_DIR / 'config.env'
        content = config_path.read_text(encoding='utf-8')
        return {'content': content}
    except Exception as e:
        logger.error('Error reading raw main config for admin panel:', e)
        raise HTTPException(status_code=500, detail=f'Failed to read raw main config file: {str(e)}')


@app.post("/admin_api/config/main")
async def save_main_config(request: Request):
    """保存主配置文件内容"""
    try:
        body = await request.json()
        content = body.get('content')
        if not isinstance(content, str):
            raise HTTPException(status_code=400, detail='Invalid content format. String expected.')

        config_path = BASE_DIR / 'config.env'
        config_path.write_text(content, encoding='utf-8')
        return {'message': '主配置已成功保存。更改可能需要重启服务才能完全生效。'}
    except HTTPException:
        raise
    except Exception as e:
        logger.error('Error writing main config for admin panel:', e)
        raise HTTPException(status_code=500, detail=f'Failed to write main config file: {str(e)}')


@app.get("/admin_api/plugins")
async def list_plugins():
    """获取插件列表及其状态"""
    try:
        plugin_data_list = []

        if not PLUGIN_DIR.exists():
            return []

        for folder in PLUGIN_DIR.iterdir():
            if folder.is_dir():
                plugin_path = folder
                manifest_path = plugin_path / MANIFEST_FILE
                blocked_manifest_path = manifest_path.with_suffix(manifest_path.suffix + BLOCKED_EXTENSION)

                manifest = None
                is_enabled = False
                config_env_content = None

                # 尝试读取启用的 manifest
                try:
                    manifest_content = manifest_path.read_text(encoding='utf-8')
                    manifest = json.loads(manifest_content)
                    is_enabled = True
                except FileNotFoundError:
                    # 尝试读取禁用的 manifest
                    try:
                        manifest_content = blocked_manifest_path.read_text(encoding='utf-8')
                        manifest = json.loads(manifest_content)
                        is_enabled = False
                    except FileNotFoundError:
                        continue
                    except json.JSONDecodeError:
                        logger.warning(f'[AdminPanel] Invalid JSON in blocked manifest for {folder.name}')
                        continue
                except json.JSONDecodeError:
                    logger.warning(f'[AdminPanel] Invalid JSON in manifest for {folder.name}')
                    continue

                # 尝试读取插件配置
                try:
                    plugin_config_path = plugin_path / 'config.env'
                    config_env_content = plugin_config_path.read_text(encoding='utf-8')
                except FileNotFoundError:
                    pass
                except Exception as e:
                    logger.warning(f'[AdminPanel] Error reading config.env for {folder.name}: {e}')

                if manifest and manifest.get('name'):
                    plugin_data_list.append({
                        'name': manifest['name'],
                        'manifest': manifest,
                        'enabled': is_enabled,
                        'configEnvContent': config_env_content
                    })

        return plugin_data_list
    except Exception as e:
        logger.error('[AdminPanel] Error listing plugins:', e)
        raise HTTPException(status_code=500, detail=f'Failed to list plugins: {str(e)}')


@app.post("/admin_api/plugins/{plugin_name}/toggle")
async def toggle_plugin(plugin_name: str, request: Request):
    """切换插件启用/禁用状态"""
    try:
        body = await request.json()
        enable = body.get('enable')
        if not isinstance(enable, bool):
            raise HTTPException(status_code=400, detail='Invalid request body. Expected { enable: boolean }.')

        # 查找插件文件夹
        target_plugin_path = None
        current_manifest_path = None
        current_blocked_path = None
        found_manifest = None

        if not PLUGIN_DIR.exists():
            raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found.")

        for folder in PLUGIN_DIR.iterdir():
            if not folder.is_dir():
                continue

            potential_manifest_path = folder / MANIFEST_FILE
            potential_blocked_path = potential_manifest_path.with_suffix(
                potential_manifest_path.suffix + BLOCKED_EXTENSION
            )

            manifest_content = None
            is_currently_enabled = False

            # 尝试读取启用的 manifest
            try:
                manifest_content = potential_manifest_path.read_text(encoding='utf-8')
                is_currently_enabled = True
                current_manifest_path = potential_manifest_path
                current_blocked_path = potential_blocked_path
            except FileNotFoundError:
                # 尝试读取禁用的 manifest
                try:
                    manifest_content = potential_blocked_path.read_text(encoding='utf-8')
                    is_currently_enabled = False
                    current_manifest_path = potential_manifest_path
                    current_blocked_path = potential_blocked_path
                except FileNotFoundError:
                    continue

            try:
                manifest = json.loads(manifest_content)
                if manifest.get('name') == plugin_name:
                    target_plugin_path = folder
                    found_manifest = manifest
                    break
            except json.JSONDecodeError:
                continue

        if not target_plugin_path or not found_manifest:
            raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found.")

        manifest_path = current_manifest_path
        blocked_manifest_path = current_blocked_path

        if enable:
            # 启用：将 .block 重命名为 .json
            try:
                if blocked_manifest_path.exists():
                    blocked_manifest_path.rename(manifest_path)
                return {'message': f'插件 {plugin_name} 已启用。请注意，更改可能需要重启服务才能完全生效。'}
            except FileNotFoundError:
                # 已经是启用状态
                if manifest_path.exists():
                    return {'message': f'插件 {plugin_name} 已经是启用状态。'}
                raise HTTPException(
                    status_code=500,
                    detail=f'无法启用插件 {plugin_name}。找不到 manifest 文件。'
                )
        else:
            # 禁用：将 .json 重命名为 .block
            try:
                if manifest_path.exists():
                    manifest_path.rename(blocked_manifest_path)
                return {'message': f'插件 {plugin_name} 已禁用。请注意，更改可能需要重启服务才能完全生效。'}
            except FileNotFoundError:
                # 已经是禁用状态
                if blocked_manifest_path.exists():
                    return {'message': f'插件 {plugin_name} 已经是禁用状态。'}
                raise HTTPException(
                    status_code=500,
                    detail=f'无法禁用插件 {plugin_name}。找不到 manifest 文件。'
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'[AdminPanel] Error toggling plugin {plugin_name}:', e)
        raise HTTPException(status_code=500, detail=f'处理插件状态切换时出错: {str(e)}')


@app.post("/admin_api/plugins/{plugin_name}/description")
async def update_plugin_description(plugin_name: str, request: Request):
    """更新插件描述"""
    try:
        body = await request.json()
        description = body.get('description')
        if not isinstance(description, str):
            raise HTTPException(status_code=400, detail='Invalid request body. Expected { description: string }.')

        # 查找插件
        target_manifest_path = None
        manifest = None

        if not PLUGIN_DIR.exists():
            raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found.")

        for folder in PLUGIN_DIR.iterdir():
            if not folder.is_dir():
                continue

            potential_manifest_path = folder / MANIFEST_FILE
            potential_blocked_path = potential_manifest_path.with_suffix(
                potential_manifest_path.suffix + BLOCKED_EXTENSION
            )

            current_path = None
            manifest_content = None

            # 尝试读取启用的 manifest
            try:
                manifest_content = potential_manifest_path.read_text(encoding='utf-8')
                current_path = potential_manifest_path
            except FileNotFoundError:
                # 尝试读取禁用的 manifest
                try:
                    manifest_content = potential_blocked_path.read_text(encoding='utf-8')
                    current_path = potential_blocked_path
                except FileNotFoundError:
                    continue

            try:
                parsed_manifest = json.loads(manifest_content)
                if parsed_manifest.get('name') == plugin_name:
                    target_manifest_path = current_path
                    manifest = parsed_manifest
                    break
            except json.JSONDecodeError:
                continue

        if not target_manifest_path or not manifest:
            raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' or its manifest file not found.")

        # 更新描述
        manifest['description'] = description
        target_manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')

        return {'message': f'插件 {plugin_name} 的描述已更新。'}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'[AdminPanel] Error updating description for plugin {plugin_name}:', e)
        raise HTTPException(status_code=500, detail=f'更新插件描述时出错: {str(e)}')


@app.post("/admin_api/plugins/{plugin_name}/config")
async def save_plugin_config(plugin_name: str, request: Request):
    """保存插件配置"""
    try:
        body = await request.json()
        content = body.get('content')
        if not isinstance(content, str):
            raise HTTPException(status_code=400, detail='Invalid content format. String expected.')

        # 查找插件文件夹
        target_plugin_path = None

        if not PLUGIN_DIR.exists():
            raise HTTPException(status_code=404, detail=f"Plugin folder for '{plugin_name}' not found.")

        for folder in PLUGIN_DIR.iterdir():
            if not folder.is_dir():
                continue

            potential_manifest_path = folder / MANIFEST_FILE
            potential_blocked_path = potential_manifest_path.with_suffix(
                potential_manifest_path.suffix + BLOCKED_EXTENSION
            )

            manifest_content = None
            try:
                manifest_content = potential_manifest_path.read_text(encoding='utf-8')
            except FileNotFoundError:
                try:
                    manifest_content = potential_blocked_path.read_text(encoding='utf-8')
                except FileNotFoundError:
                    continue

            try:
                manifest = json.loads(manifest_content)
                if manifest.get('name') == plugin_name:
                    target_plugin_path = folder
                    break
            except json.JSONDecodeError:
                continue

        if not target_plugin_path:
            raise HTTPException(status_code=404, detail=f"Plugin folder for '{plugin_name}' not found.")

        config_path = target_plugin_path / 'config.env'
        config_path.write_text(content, encoding='utf-8')

        return {'message': f'插件 {plugin_name} 的配置已保存。更改可能需要重启插件或服务才能生效。'}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'[AdminPanel] Error writing config.env for plugin {plugin_name}:', e)
        raise HTTPException(status_code=500, detail=f'保存插件配置时出错: {str(e)}')


# ==================== 启动服务器 ====================

if __name__ == "__main__":
    import uvicorn

    # 在启动后初始化服务插件
    @app.on_event("startup")
    async def startup_event():
        """启动事件"""
        await ensure_debug_log_dir()

        # 初始化服务插件（需要在 app 创建后调用）
        plugin_manager.initialize_services(app, str(Path(__file__).parent))

    logger.info(f"中间层服务器正在监听端口 {PORT}")
    logger.info(f"API 服务器地址: {API_URL}")

    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
