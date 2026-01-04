"""
UrlFetch Plugin
获取指定 URL 的网页内容，并进行简单的去广告和清理处理
"""

import sys
import json
import re
from typing import Dict, Any
from urllib.parse import urlparse
from html.parser import HTMLParser

# 尝试导入 requests 库
try:
    import requests
    from requests.exceptions import RequestException, Timeout as RequestsTimeout
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    RequestException = Exception
    RequestsTimeout = Exception


class TextExtractor(HTMLParser):
    """HTML 文本提取器，去除广告和无关内容"""

    def __init__(self):
        super().__init__()
        self.result = []
        self.skip_tags = {'script', 'style', 'iframe', 'ins', 'nav', 'aside', 'footer', 'noscript'}
        self.skip_classes = {'ads', 'advertisement', 'banner', 'popup'}
        self.skip = False
        self.skip_depth = 0
        self.in_content_tag = False
        self.content_tags = {'article', 'main', 'section'}
        self.has_main_content = False
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        self.current_tag = tag

        # 检查是否需要跳过此标签
        if tag in self.skip_tags:
            self.skip = True
            self.skip_depth = 1
            return

        # 检查 class 和 id 属性中是否包含广告关键词
        class_attr = attrs_dict.get('class', '')
        id_attr = attrs_dict.get('id', '')

        if any(keyword in class_attr.lower() for keyword in ['ads', 'advertisement', 'banner', 'popup']):
            self.skip = True
            self.skip_depth = 1
            return

        if any(keyword in id_attr.lower() for keyword in ['ads', 'advertisement', 'banner', 'popup']):
            self.skip = True
            self.skip_depth = 1
            return

        # 检查 aria-hidden
        if attrs_dict.get('aria-hidden') == 'true':
            self.skip = True
            self.skip_depth = 1
            return

        # 检查是否在主要内容标签中
        if tag in self.content_tags:
            self.in_content_tag = True
            self.has_main_content = True

    def handle_endtag(self, tag):
        if self.skip:
            self.skip_depth -= 1
            if self.skip_depth <= 0:
                self.skip = False
                self.skip_depth = 0

        if tag in self.content_tags:
            self.in_content_tag = False

        self.current_tag = None

    def handle_data(self, data):
        if self.skip:
            return

        text = data.strip()
        if text:
            self.result.append(text)

    def get_text(self) -> str:
        """获取清理后的文本"""
        text = ' '.join(self.result)

        # 清理多余的空白
        text = re.sub(r'\s+', ' ', text)
        text = text.split('\n')
        text = [line.strip() for line in text]
        text = [line for line in text if line]
        text = '\n'.join(text)

        return text


def clean_html(html_content: str) -> str:
    """清理 HTML 内容，提取主要文本"""
    parser = TextExtractor()

    try:
        parser.feed(html_content)
    except Exception:
        # 如果解析失败，返回简单的文本提取
        text = re.sub(r'<[^>]+>', ' ', html_content)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    return parser.get_text()


def process_url_fetch(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """处理 URL 获取请求"""
    url = input_data.get('url')

    if not url:
        return {
            'status': 'error',
            'error': '缺少必需的参数: url'
        }

    # 验证 URL 格式
    if not url.startswith('http://') and not url.startswith('https://'):
        return {
            'status': 'error',
            'error': '无效的 URL 格式。URL 必须以 http:// 或 https:// 开头。'
        }

    if not HAS_REQUESTS:
        return {
            'status': 'error',
            'error': '缺少必需的 Python 库: requests。请安装: pip install requests'
        }

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 RooAIUrlFetchPlugin/0.1.0'
        }

        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            return {
                'status': 'error',
                'error': f'请求失败，状态码: {response.status_code}'
            }

        content_type = response.headers.get('content-type', '')

        if not content_type or 'text/html' not in content_type:
            return {
                'status': 'error',
                'error': f'不支持的内容类型: {content_type}. 只支持 text/html。'
            }

        # 清理 HTML 内容
        cleaned_text = clean_html(response.text)

        if not cleaned_text.strip():
            return {
                'status': 'success',
                'result': '成功获取网页，但提取到的文本内容为空或只包含空白字符。'
            }

        # 限制结果长度（防止过长的响应）
        max_length = 10000
        if len(cleaned_text) > max_length:
            cleaned_text = cleaned_text[:max_length] + '\n\n[内容已截断，超过最大长度限制]'

        return {
            'status': 'success',
            'result': cleaned_text
        }

    except RequestsTimeout:
        return {
            'status': 'error',
            'error': '请求超时（15秒），请稍后重试。'
        }
    except RequestException as e:
        return {
            'status': 'error',
            'error': f'请求错误: {str(e)}'
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': f'UrlFetch 错误: {str(e)}'
        }


def main():
    """主函数"""
    try:
        # 从 stdin 读取输入
        input_data = sys.stdin.read()

        if not input_data.strip():
            print(json.dumps({
                'status': 'error',
                'error': '未从 stdin 接收到输入数据。'
            }, ensure_ascii=False))
            sys.exit(1)

        # 解析 JSON 输入
        try:
            parsed_input = json.loads(input_data)
        except json.JSONDecodeError as e:
            print(json.dumps({
                'status': 'error',
                'error': f'无效的 JSON 输入: {str(e)}'
            }, ensure_ascii=False))
            sys.exit(1)

        # 处理 URL 获取请求
        result = process_url_fetch(parsed_input)

        # 输出结果到 stdout
        print(json.dumps(result, ensure_ascii=False, indent=2))

        # 根据状态设置退出码
        sys.exit(0 if result.get('status') == 'success' else 1)

    except Exception as e:
        print(json.dumps({
            'status': 'error',
            'error': f'未处理的插件错误: {str(e)}'
        }, ensure_ascii=False))
        sys.exit(1)


if __name__ == '__main__':
    main()
