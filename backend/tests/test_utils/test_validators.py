"""
测试工具函数 - 验证器测试
"""
import pytest

from app.utils.validators import allowed_file
from app.config import Config


class TestAllowedFile:
    """测试 allowed_file 函数"""

    def test_allowed_file_with_png_extension(self):
        """测试允许的 PNG 文件扩展名"""
        assert allowed_file("test.png") is True
        assert allowed_file("image.PNG") is True
        assert allowed_file("photo.png") is True

    def test_allowed_file_with_jpg_extensions(self):
        """测试允许的 JPG/JPEG 文件扩展名"""
        assert allowed_file("test.jpg") is True
        assert allowed_file("test.jpeg") is True
        assert allowed_file("photo.JPG") is True
        assert allowed_file("photo.JPEG") is True

    def test_allowed_file_with_pdf_extension(self):
        """测试允许的 PDF 文件扩展名"""
        assert allowed_file("document.pdf") is True
        assert allowed_file("report.PDF") is True

    def test_allowed_file_with_docx_extension(self):
        """测试允许的 DOCX 文件扩展名"""
        assert allowed_file("document.docx") is True
        assert allowed_file("report.DOCX") is True

    def test_allowed_file_with_pptx_extension(self):
        """测试允许的 PPTX 文件扩展名"""
        assert allowed_file("presentation.pptx") is True
        assert allowed_file("slides.PPTX") is True

    def test_allowed_file_with_txt_extension(self):
        """测试允许的 TXT 文件扩展名"""
        assert allowed_file("notes.txt") is True
        assert allowed_file("readme.TXT") is True

    def test_allowed_file_with_md_extension(self):
        """测试允许的 MD 文件扩展名"""
        assert allowed_file("README.md") is True
        assert allowed_file("notes.MD") is True

    def test_allowed_file_with_gif_extension(self):
        """测试允许的 GIF 文件扩展名"""
        assert allowed_file("animation.gif") is True
        assert allowed_file("image.GIF") is True

    def test_allowed_file_with_webp_extension(self):
        """测试允许的 WebP 文件扩展名"""
        assert allowed_file("image.webp") is True
        assert allowed_file("photo.WEBP") is True

    def test_allowed_file_with_disallowed_extension(self):
        """测试不允许的文件扩展名"""
        assert allowed_file("script.exe") is False
        assert allowed_file("file.zip") is False
        assert allowed_file("archive.tar.gz") is False
        assert allowed_file("code.py") is False
        assert allowed_file("data.json") is False
        assert allowed_file("config.xml") is False

    def test_allowed_file_without_extension(self):
        """测试没有扩展名的文件"""
        assert allowed_file("filename") is False
        assert allowed_file("README") is False
        assert allowed_file("makefile") is False

    def test_allowed_file_with_only_extension(self):
        """测试只有扩展名的文件"""
        assert allowed_file(".gitignore") is False
        assert allowed_file(".env") is False

    def test_allowed_file_with_multiple_dots(self):
        """测试包含多个点的文件名"""
        assert allowed_file("file.name.txt") is True
        assert allowed_file("my.document.pdf") is True
        assert allowed_file("archive.tar.gz") is False

    def test_allowed_file_with_path(self):
        """测试包含路径的文件名"""
        assert allowed_file("path/to/file.png") is True
        assert allowed_file("folder/subfolder/document.pdf") is True
        assert allowed_file("./relative/path/image.jpg") is True
        assert allowed_file("/absolute/path/to/file.txt") is True

    def test_allowed_file_with_custom_extensions(self):
        """测试自定义允许的扩展名集合"""
        custom_extensions = {'pdf', 'docx'}
        assert allowed_file("document.pdf", custom_extensions) is True
        assert allowed_file("report.docx", custom_extensions) is True
        assert allowed_file("image.png", custom_extensions) is False
        assert allowed_file("file.txt", custom_extensions) is False

    def test_allowed_file_with_empty_custom_extensions(self):
        """测试空的自定义扩展名集合"""
        assert allowed_file("test.png", set()) is False
        assert allowed_file("file.txt", set()) is False

    def test_allowed_file_with_empty_filename(self):
        """测试空文件名"""
        assert allowed_file("") is False
        assert allowed_file("   ") is False
        assert allowed_file(None) is False

    def test_allowed_file_with_special_characters(self):
        """测试包含特殊字符的文件名"""
        assert allowed_file("文件.png") is True
        assert allowed_file("файл.pdf") is True
        assert allowed_file("date-2024_01(01).txt") is True
        assert allowed_file("file@name#1.jpg") is True

    def test_allowed_file_case_insensitive(self):
        """测试扩展名大小写不敏感"""
        assert allowed_file("test.PNG") is True
        assert allowed_file("test.Png") is True
        assert allowed_file("test.pNg") is True
        assert allowed_file("test.PDF") is True
        assert allowed_file("test.JPEG") is True


class TestConfigAllowedExtensions:
    """测试 Config.ALLOWED_EXTENSIONS 配置"""

    def test_allowed_extensions_contains_expected_types(self):
        """测试默认允许的扩展名包含预期类型"""
        expected_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'docx', 'pptx', 'txt', 'md'}
        assert Config.ALLOWED_EXTENSIONS == expected_extensions

    def test_allowed_extensions_all_lowercase(self):
        """测试允许的扩展名都是小写"""
        for ext in Config.ALLOWED_EXTENSIONS:
            assert ext == ext.lower()

    def test_allowed_reference_file_extensions_subset(self):
        """测试参考文件扩展名是允许扩展名的子集"""
        for ext in Config.ALLOWED_REFERENCE_FILE_EXTENSIONS:
            assert ext in Config.ALLOWED_EXTENSIONS
