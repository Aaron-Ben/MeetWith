import os
import sys
import json
import re
from pathlib import Path


def debug_log(message, *args):
    """输出调试日志到 stderr"""
    debug_mode = os.getenv('DebugMode', 'false').lower() == 'true'
    if debug_mode:
        print(f"[DailyNoteManager][Debug] {message}", *args, file=sys.stderr)


def process_daily_notes(input_content):
    """处理日记内容，将其保存为独立的 txt 文件"""
    project_base_path = os.getenv('PROJECT_BASE_PATH')
    if not project_base_path:
        print('[DailyNoteManager] Error: PROJECT_BASE_PATH environment variable is not set.', file=sys.stderr)
        return {'status': 'error', 'error': '无法确定项目主目录。'}

    output_dir = Path(project_base_path) / 'dailynote' / '已整理日记'
    results = []

    try:
        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)

        # 添加调试输出
        debug_log(f'收到的日记内容前100个字符: {input_content[:100]}...')

        lines = input_content.split('\n')
        current_filename = None
        current_content_lines = []

        # 定义文件名模式正则
        filename_pattern = re.compile(r'^(\d{4}\.\d{2}\.\d{2}(?:\.\d+)?)\.txt$')

        def save_current_note():
            """保存当前日记"""
            if current_filename and current_content_lines:
                filename = current_filename.strip()
                # 合并行并去除首尾空白，但保留内部换行
                content = '\n'.join(current_content_lines).strip()

                debug_log(f'准备保存日记: 文件名={filename}, 内容长度={len(content)}')

                if not filename.lower().endswith('.txt') or len(content) == 0:
                    results.append({
                        'status': 'warning',
                        'filename': filename or '未知',
                        'message': f'无效的日记条目格式或内容为空。跳过保存。'
                    })
                    print(f'[DailyNoteManager] 无效的日记条目格式或内容为空。文件名: {filename}, 内容长度: {len(content)}', file=sys.stderr)
                    return

                file_path = output_dir / filename

                try:
                    file_path.write_text(content, encoding='utf-8')
                    results.append({
                        'status': 'success',
                        'filename': filename,
                        'message': f'成功保存日记: {filename}'
                    })
                    print(f'[DailyNoteManager] 成功保存日记: {filename}', file=sys.stderr)
                except Exception as write_error:
                    results.append({
                        'status': 'error',
                        'filename': filename,
                        'message': f'保存日记失败: {filename} - {str(write_error)}'
                    })
                    print(f'[DailyNoteManager] 保存日记失败: {filename}', write_error, file=sys.stderr)

        # 遍历行，查找日记条目
        for line in lines:
            trimmed_line = line.strip()

            # 检查是否匹配文件名模式
            filename_match = filename_pattern.match(trimmed_line)

            if filename_match:
                # 找到新的文件名行，保存之前的日记
                save_current_note()

                # 开始新的日记
                current_filename = trimmed_line
                current_content_lines = []
                debug_log(f'检测到新的日记文件标记: {current_filename}')
            elif current_filename is not None:
                # 如果正在收集日记内容，添加行
                current_content_lines.append(line)

        # 循环结束后保存最后一个日记
        save_current_note()

        # 检查是否处理了任何日记
        if len(results) == 0:
            results.append({
                'status': 'warning',
                'message': '在命令块中未找到有效的日记条目。请检查AI输出格式。'
            })
            print('[DailyNoteManager] 在命令块中未找到有效的日记条目。请检查AI输出格式。', file=sys.stderr)

    except Exception as dir_error:
        results.append({
            'status': 'error',
            'message': f'创建输出目录失败: {output_dir} - {str(dir_error)}'
        })
        print(f'[DailyNoteManager] 创建输出目录失败: {output_dir}', dir_error, file=sys.stderr)
        return {'status': 'error', 'error': f'创建输出目录失败: {output_dir} - {str(dir_error)}'}

    # 确定整体状态并格式化输出
    errors = [r for r in results if r['status'] == 'error']
    warnings = [r for r in results if r['status'] == 'warning']
    successes = [r for r in results if r['status'] == 'success']

    if len(errors) > 0:
        error_messages = '\n'.join([f"{e.get('filename', '未知文件')}: {e['message']}" for e in errors])
        return {'status': 'error', 'error': f'保存日记时发生错误:\n{error_messages}'}
    elif len(results) == 0:
        return {'status': 'warning', 'result': '未找到有效的日记条目进行处理。请检查AI输出格式。'}
    else:
        success_messages = '\n'.join([f"成功保存: {s['filename']}" for s in successes])
        warning_messages = '\n'.join([f"警告: {w['message']}" for w in warnings])
        result_message = success_messages
        if warning_messages:
            result_message += f'\n\n警告:\n{warning_messages}'
        return {'status': 'success', 'result': f'日记处理完成:\n{result_message}'}


def main():
    """主函数"""
    try:
        # 从 stdin 读取输入
        input_data = sys.stdin.read()

        if not input_data:
            print(json.dumps({
                'status': 'error',
                'error': '未收到任何输入数据'
            }, ensure_ascii=False))
            sys.exit(1)

        # 解析 JSON 输入
        parsed_input = json.loads(input_data)
        diary_content = ''

        if parsed_input and isinstance(parsed_input.get('command'), str):
            diary_content = parsed_input['command']
        else:
            print(json.dumps({
                'status': 'error',
                'error': '处理输入数据失败: 无效的输入格式，期望包含 command 字段的 JSON'
            }, ensure_ascii=False))
            sys.exit(1)

        # 处理日记内容
        processing_result = process_daily_notes(diary_content)

        # 确保返回有效的 JSON 格式
        if not processing_result or not isinstance(processing_result, dict):
            processing_result = {
                'status': 'error',
                'error': '处理结果格式无效'
            }

        # 输出结果到 stdout
        print(json.dumps(processing_result, ensure_ascii=False, indent=2))

        # 根据状态设置退出码
        sys.exit(1 if processing_result.get('status') == 'error' else 0)

    except json.JSONDecodeError as parse_error:
        print(f'[DailyNoteManager] Error parsing input JSON: {parse_error}', file=sys.stderr)
        print(json.dumps({
            'status': 'error',
            'error': f'解析输入数据失败: {str(parse_error)}'
        }, ensure_ascii=False))
        sys.exit(1)
    except Exception as e:
        print(f'[DailyNoteManager] Fatal error: {e}', file=sys.stderr)
        print(json.dumps({
            'status': 'error',
            'error': f'处理失败: {str(e)}'
        }, ensure_ascii=False))
        sys.exit(1)


if __name__ == '__main__':
    main()
