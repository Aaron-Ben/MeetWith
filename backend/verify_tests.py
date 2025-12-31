#!/usr/bin/env python3
"""
验证测试代码的脚本 - 不需要 pytest
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

def import_test_modules():
    """导入测试模块以验证语法"""
    print("正在验证测试代码...")

    try:
        # 测试工具模块
        print("1. 测试 validators.py...")
        from app.utils.validators import allowed_file
        print("   ✓ validators.py 导入成功")

        # 测试响应工具
        print("2. 测试 response.py...")
        from app.utils.response import success_response, error_response
        print("   ✓ response.py 导入成功")

        # 测试模型
        print("3. 测试 PPTProject 模型...")
        from app.models.ppt.project import PPTProject
        print("   ✓ PPTProject 模型导入成功")

        print("4. 测试 Page 模型...")
        from app.models.ppt.page import Page
        print("   ✓ Page 模型导入成功")

        # 测试 AI 服务
        print("5. 测试 AIService...")
        from app.services.ppt.ai_service import AIService, ProjectContext
        print("   ✓ AIService 导入成功")

        # 测试任务管理器
        print("6. 测试 TaskManager...")
        from app.services.ppt.task_manager import TaskManager
        print("   ✓ TaskManager 导入成功")

        print("\n" + "="*50)
        print("所有模块导入成功！")
        print("="*50)
        return True

    except ImportError as e:
        print(f"\n✗ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_basic_function_tests():
    """运行基本的功能测试"""
    print("\n运行基本功能测试...")

    try:
        from app.utils.validators import allowed_file

        # 测试 allowed_file
        assert allowed_file("test.png") == True, "PNG 文件测试失败"
        assert allowed_file("test.exe") == False, "EXE 文件测试失败"
        assert allowed_file("document.pdf") == True, "PDF 文件测试失败"
        assert allowed_file("no_extension") == False, "无扩展名测试失败"

        print("  ✓ allowed_file 函数测试通过")

        from app.utils.response import success_response, error_response
        import json

        # 测试 success_response
        resp = success_response(data={"key": "value"}, message="成功")
        data = json.loads(resp.body.decode())
        assert data["message"] == "成功", "success_response 测试失败"
        assert data["data"]["key"] == "value", "success_response 数据测试失败"

        print("  ✓ success_response 函数测试通过")

        # 测试 error_response
        err = error_response(message="错误", status_code=400)
        assert err.status_code == 400, "error_response 状态码测试失败"

        print("  ✓ error_response 函数测试通过")

        print("\n基本功能测试全部通过！")
        return True

    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = True

    # 验证模块导入
    if not import_test_modules():
        success = False

    # 运行基本功能测试
    if not run_basic_function_tests():
        success = False

    # 输出结果
    if success:
        print("\n" + "="*50)
        print("✓ 所有验证通过！测试代码已就绪。")
        print("="*50)
        print("\n要运行完整的测试套件，请执行：")
        print("  pip install -r test-requirements.txt")
        print("  pytest")
        sys.exit(0)
    else:
        print("\n" + "="*50)
        print("✗ 验证失败，请检查错误信息。")
        print("="*50)
        sys.exit(1)
