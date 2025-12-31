"""
测试配置文件 - pytest fixtures
"""
import os
import sys
import pytest
import tempfile
from pathlib import Path
from typing import Generator

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_upload_dir(tmp_path: Path) -> Generator[str, None, None]:
    """
    创建临时上传目录
    """
    upload_dir = tmp_path / "upload"
    upload_dir.mkdir(exist_ok=True)
    yield str(upload_dir)


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Generator[str, None, None]:
    """
    创建临时数据库路径
    """
    db_path = tmp_path / "test.db"
    yield str(db_path)


@pytest.fixture
def sample_image_file(tmp_path: Path) -> Generator[Path, None, None]:
    """
    创建示例图片文件
    """
    image_path = tmp_path / "sample.png"
    # 创建一个最小的 PNG 文件
    import struct
    with open(image_path, "wb") as f:
        # PNG 文件头
        f.write(b'\x89PNG\r\n\x1a\n')
        # IHDR chunk
        width_height = struct.pack('>II', 10, 10)
        f.write(b'\x00\x00\x00\rIHDR' + width_height + b'\x08\x02\x00\x00\x00')
        # IDAT chunk (空数据)
        f.write(b'\x00\x00\x00\x0eIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\x0d\n-\xb4')
        # IEND chunk
        f.write(b'\x00\x00\x00\x00IEND\xaeB`\x82')
    yield image_path


@pytest.fixture
def sample_pdf_file(tmp_path: Path) -> Generator[Path, None, None]:
    """
    创建示例 PDF 文件
    """
    pdf_path = tmp_path / "sample.pdf"
    # 创建一个最小的 PDF 文件
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Count 1
/Kids [3 0 R]
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
190
%%EOF
"""
    with open(pdf_path, "wb") as f:
        f.write(pdf_content)
    yield pdf_path


@pytest.fixture
def sample_markdown_content() -> str:
    """
    示例 Markdown 内容
    """
    return """# 项目介绍

这是一个 AI PPT 生成系统。

## 功能特点

1. 自动生成大纲
2. 智能生成描述
3. AI 生成配图

![示例图片](https://example.com/image.png)

## 总结

通过 AI 技术，快速创建专业 PPT。
"""


@pytest.fixture
def sample_outline_data():
    """
    示例大纲数据
    """
    return [
        {
            "title": "第一部分：项目背景",
            "pages": [
                {"title": "项目起源", "description": "介绍项目为什么会诞生"},
                {"title": "市场分析", "description": "当前市场状况和需求分析"}
            ]
        },
        {
            "title": "第二部分：技术方案",
            "pages": [
                {"title": "技术架构", "description": "系统整体架构设计"},
                {"title": "核心功能", "description": "主要功能模块介绍"}
            ]
        }
    ]


@pytest.fixture
def sample_description_data():
    """
    示例描述数据
    """
    return {
        "text": "本页面介绍了项目的核心功能，包括AI生成大纲、智能内容创作和图片生成等特性。",
        "text_content": [
            "AI生成大纲",
            "智能内容创作",
            "图片生成"
        ],
        "generated_at": "2024-01-01T00:00:00"
    }


@pytest.fixture
def mock_env_vars():
    """
    Mock 环境变量
    """
    original_env = os.environ.copy()
    os.environ.update({
        "DASHSCOPE_API_KEY": "test_api_key",
        "UPLOAD_FOLDER": "/tmp/test_upload",
        "LOG_LEVEL": "DEBUG"
    })
    yield
    # 恢复原始环境变量
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_ai_response():
    """
    Mock AI 服务响应
    """
    def _mock_response(text: str):
        return text

    return _mock_response
