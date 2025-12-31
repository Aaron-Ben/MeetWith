"""
测试工具函数 - 响应工具测试
"""
import json
import pytest
from fastapi.responses import JSONResponse

from app.utils.response import success_response, error_response, bad_request_response


class TestSuccessResponse:
    """测试 success_response 函数"""

    def test_success_response_default_values(self):
        """测试默认参数的成功响应"""
        response = success_response()
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200

        data = json.loads(response.body.decode())
        assert data["message"] == "Success"
        assert data["data"] is None

    def test_success_response_with_data(self):
        """测试带数据的成功响应"""
        test_data = {"id": "123", "name": "测试项目"}
        response = success_response(data=test_data)

        assert response.status_code == 200
        data = json.loads(response.body.decode())
        assert data["data"] == test_data
        assert data["message"] == "Success"

    def test_success_response_with_message(self):
        """测试带消息的成功响应"""
        response = success_response(message="创建成功")
        data = json.loads(response.body.decode())
        assert data["message"] == "创建成功"

    def test_success_response_with_custom_status_code(self):
        """测试自定义状态码的成功响应"""
        response = success_response(status_code=201)
        assert response.status_code == 201

    def test_success_response_with_all_parameters(self):
        """测试所有参数的成功响应"""
        test_data = {"project_id": "abc123"}
        response = success_response(
            data=test_data,
            message="项目创建成功",
            status_code=201
        )

        assert response.status_code == 201
        data = json.loads(response.body.decode())
        assert data["data"] == test_data
        assert data["message"] == "项目创建成功"

    def test_success_response_with_list_data(self):
        """测试列表数据的成功响应"""
        test_data = [1, 2, 3, 4, 5]
        response = success_response(data=test_data)
        data = json.loads(response.body.decode())
        assert data["data"] == test_data

    def test_success_response_with_nested_data(self):
        """测试嵌套数据的成功响应"""
        test_data = {
            "project": {
                "id": "123",
                "pages": [
                    {"id": "1", "title": "页面1"},
                    {"id": "2", "title": "页面2"}
                ]
            }
        }
        response = success_response(data=test_data)
        data = json.loads(response.body.decode())
        assert data["data"] == test_data

    def test_success_response_with_empty_dict(self):
        """测试空字典数据的成功响应"""
        response = success_response(data={})
        data = json.loads(response.body.decode())
        assert data["data"] == {}

    def test_success_response_with_none_data(self):
        """测试 None 数据的成功响应"""
        response = success_response(data=None)
        data = json.loads(response.body.decode())
        assert data["data"] is None


class TestErrorResponse:
    """测试 error_response 函数"""

    def test_error_response_default_values(self):
        """测试默认参数的错误响应"""
        response = error_response()
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400

        data = json.loads(response.body.decode())
        assert data["message"] == "Error"
        assert data["data"] is None

    def test_error_response_with_message(self):
        """测试带消息的错误响应"""
        response = error_response(message="参数错误")
        data = json.loads(response.body.decode())
        assert data["message"] == "参数错误"

    def test_error_response_with_data(self):
        """测试带数据的错误响应"""
        test_data = {"field": "title", "error": "必填字段"}
        response = error_response(data=test_data)
        data = json.loads(response.body.decode())
        assert data["data"] == test_data

    def test_error_response_with_custom_status_code(self):
        """测试自定义状态码的错误响应"""
        response = error_response(status_code=404)
        assert response.status_code == 404

        response = error_response(status_code=500)
        assert response.status_code == 500

    def test_error_response_with_all_parameters(self):
        """测试所有参数的错误响应"""
        test_data = {"details": "项目未找到"}
        response = error_response(
            message="未找到资源",
            data=test_data,
            status_code=404
        )

        assert response.status_code == 404
        data = json.loads(response.body.decode())
        assert data["message"] == "未找到资源"
        assert data["data"] == test_data

    def test_error_response_common_http_codes(self):
        """测试常见 HTTP 状态码"""
        # 400 Bad Request
        response = error_response(status_code=400)
        assert response.status_code == 400

        # 401 Unauthorized
        response = error_response(status_code=401)
        assert response.status_code == 401

        # 403 Forbidden
        response = error_response(status_code=403)
        assert response.status_code == 403

        # 404 Not Found
        response = error_response(status_code=404)
        assert response.status_code == 404

        # 500 Internal Server Error
        response = error_response(status_code=500)
        assert response.status_code == 500

        # 503 Service Unavailable
        response = error_response(status_code=503)
        assert response.status_code == 503


class TestBadRequestResponse:
    """测试 bad_request_response 函数"""

    def test_bad_request_response_default_values(self):
        """测试默认参数的 bad request 响应"""
        response = bad_request_response()
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400

        data = json.loads(response.body.decode())
        assert data["message"] == "参数缺失"
        assert data["data"] is None

    def test_bad_request_response_with_custom_message(self):
        """测试自定义消息的 bad request 响应"""
        response = bad_request_response(message="标题不能为空")
        data = json.loads(response.body.decode())
        assert data["message"] == "标题不能为空"

    def test_bad_request_response_with_data(self):
        """测试带数据的 bad request 响应"""
        test_data = {"missing_fields": ["title", "content"]}
        response = bad_request_response(
            message="缺少必填字段",
            data=test_data
        )
        data = json.loads(response.body.decode())
        assert data["message"] == "缺少必填字段"
        assert data["data"] == test_data

    def test_bad_request_response_is_400_by_default(self):
        """测试 bad request 默认状态码为 400"""
        response = bad_request_response()
        assert response.status_code == 400

    def test_bad_request_response_custom_status_code(self):
        """测试自定义状态码的 bad request 响应"""
        response = bad_request_response(status_code=422)
        assert response.status_code == 422


class TestResponseIntegration:
    """测试响应工具的集成使用"""

    def test_success_and_error_response_structure_consistency(self):
        """测试成功和错误响应结构的一致性"""
        success = success_response(data={"id": "123"}, message="成功")
        error = error_response(data={"error": "失败"}, message="错误")

        success_data = json.loads(success.body.decode())
        error_data = json.loads(error.body.decode())

        # 两者都应有 message 和 data 字段
        assert "message" in success_data
        assert "data" in success_data
        assert "message" in error_data
        assert "data" in error_data

    def test_response_encoding_chinese_characters(self):
        """测试响应中中文字符的正确编码"""
        chinese_message = "操作成功完成"
        response = success_response(message=chinese_message)
        data = json.loads(response.body.decode())
        assert data["message"] == chinese_message

    def test_response_with_special_characters(self):
        """测试包含特殊字符的响应"""
        special_message = "Error: <script>alert('test')</script>"
        response = error_response(message=special_message)
        data = json.loads(response.body.decode())
        assert data["message"] == special_message

    def test_response_with_unicode_emoji(self):
        """测试包含 Unicode 表情的响应"""
        emoji_message = "创建成功"
        response = success_response(message=emoji_message)
        data = json.loads(response.body.decode())
        assert data["message"] == emoji_message
