import logging
from typing import Optional
import requests

from markitdown import MarkItDown

logger = logging.getLogger(__name__)


class FileParser:

    def __init__(self,
        mineru_token: str,
        mineru_api_base: str = "https://mineru.net"):
        
        self.mineru_token = mineru_token
        self.mineru_api_base = mineru_api_base
        self.get_upload_url_api = f"{mineru_api_base}/api/v4/file-urls/batch"
        self.get_result_api_template = f"{mineru_api_base}/api/v4/extract-results/batch/{{}}"
    
    def _parse_file(self, file_path: str, filename: str) -> None:

        # 正确的提取文件后缀
        file_ext = filename.rsplit(".", 1)[1].lower() if "." in filename else None

        if file_ext in ['txt', 'md', 'markdown']:
            logger.info(f"正在解析文本文件: {filename}")
            return self._parse_text_file(file_path, filename)

        if file_ext in ['xlsx', 'xls', 'csv']:
            logger.info(f"正在解析电子表格文件: {filename}")
            return self._parse_excel_file(file_path, filename)

        logger.info(f"文件 {filename} 较复杂，交给 MinerU 处理...")

        # 步骤1: 向 MinerU 注册任务，获取任务ID + 上传地址
        batch_id, upload_url, error = self._get_upload_url(filename)
        if error:
            logger.error(f"Failed to get upload url: {error}")
            return

        logger.info(f"Got batch_id: {batch_id}, upload_url: {upload_url}")
    
        # 步骤2: 将大文件上传到 MinerU
        error = self._upload_file(file_path, upload_url)
        if error:
            logger.error(f"Failed to upload file: {error}")
            return

        logger.info("upload file success")

        # 步骤3: 异步等待 MinerU 处理完，直到有ZIP结果可下载
        markdown_content, extract_id, error = self._poll_result(batch_id)
        if error:
            logger.error(f"Failed to get result: {error}")
            return

        logger.info("get result success")

        # 步骤4: 将 MinerU 生成的 makedown 进行加工，这里主要是对于图片描述的处理




    def _parse_text_file(self, file_path: str, filename: str) -> str:

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return content

    def _parse_excel_file(self, file_path: str, filename: str) -> str:
        """
        表格转化为markdown 文件
        """
        md = MarkItDown()
        result = md.convert(file_path)
        markdown_content = result.text_content

        return markdown_content


    def _get_upload_url(self, filename: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """
        获取上传地址和任务ID
        """

        # https://mineru.net/apiManage/docs 得到请求事例
        header = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.mineru_token}"
        }

        data = {
            "files": [{"name": filename}],
            "model_version": "vlm"
        }

        response = requests.post(
            self._get_upload_url,
            headers=header,
            json = data,
            timeout = 30
        )

        response.raise_for_status()
        result = response.json()

        # 官方文档，成功时 code 为 0
        if result.get("code") != 0:
            logger.error(f"Failed to get upload url: {result.get('message')}")
            return None, None, result.get("message")

        # 当前任务的id
        # 入口地址
        batch_id = result["data"]["batch_id"]
        upload_url = result["data"]["upload_url"][0]
        return batch_id, upload_url, None

    def _upload_file(self, file_path: str, upload_url: str) -> Optional[str]:
        """
        上传文件到 MinerU
        """
        with open(file_path, 'rb') as f:
            response = requests.put(
                upload_url,
                data=f,
                headers={"Authorization": None},
                timeout=100
            )
            response.raise_for_status()
        return None

