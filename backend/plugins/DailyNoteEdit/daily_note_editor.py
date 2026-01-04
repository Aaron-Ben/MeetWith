#!/usr/bin/env python3
"""
DailyNoteEditor Plugin
编辑日记文件中的特定内容
"""

import sys
import json
import os
from pathlib import Path
from typing import Dict, Any


def debug_log(message: str, *args):
    """输出调试日志到 stderr"""
    debug_mode = os.environ.get('DebugMode', 'false').lower() == 'true'
    if debug_mode:
        print(f"[DailyNoteEditor][Debug] {message}", *args, file=sys.stderr, flush=True)


def process_edit_request(input_data: str) -> Dict[str, Any]:
    """
    处理日记编辑请求

    Args:
        input_data: JSON 格式的输入数据，包含 target 和 replace 字段

    Returns:
        包含 status 和 result/error 的字典
    """
    debug_log("Received input data:", input_data)

    # 1. 解析输入数据
    try:
        args = json.loads(input_data)
    except json.JSONDecodeError as e:
        return {"status": "error", "error": f"Invalid JSON input: {str(e)}"}

    # 2. 验证输入参数
    target = args.get('target')
    replace = args.get('replace')

    if not isinstance(target, str) or not isinstance(replace, str):
        return {"status": "error", "error": "Invalid arguments: 'target' and 'replace' must be strings."}

    # 安全性检查 1: 目标字段长度不能少于 15 字符
    if len(target) < 15:
        return {
            "status": "error",
            "error": f"Security check failed: 'target' must be at least 15 characters long. Provided length: {len(target)}"
        }

    debug_log(f"Validated input. Target length: {len(target)}")

    # 获取日记根目录路径
    project_base_path = os.environ.get('PROJECT_BASE_PATH')
    if project_base_path:
        daily_note_root = Path(project_base_path) / 'dailynote'
    else:
        # 默认路径：插件目录的祖父目录下的 dailynote
        plugin_dir = Path(__file__).parent
        daily_note_root = plugin_dir.parent.parent / 'dailynote'

    debug_log(f"Daily note root path: {daily_note_root}")

    # 3. 扫描日记文件夹并查找/替换内容
    try:
        if not daily_note_root.exists():
            return {
                "status": "error",
                "error": f"Daily note root directory not found at {daily_note_root}"
            }

        modification_done = False
        modified_file_path = None

        # 遍历所有角色目录
        for character_dir in sorted(daily_note_root.iterdir()):
            if not character_dir.is_dir():
                continue

            character_name = character_dir.name
            debug_log(f"Scanning directory for character: {character_name}")

            try:
                # 获取所有 .txt 文件并排序
                txt_files = sorted(character_dir.glob('*.txt'))
                debug_log(f"Found {len(txt_files)} .txt files for {character_name}")

                for file_path in txt_files:
                    if modification_done:
                        break  # 安全性检查 2: 一次只能修改一个日记内容

                    debug_log(f"Reading file: {file_path}")

                    try:
                        content = file_path.read_text(encoding='utf-8')
                    except IOError as e:
                        print(f"[DailyNoteEditor] Error reading diary file {file_path}: {e}",
                              file=sys.stderr, flush=True)
                        continue

                    # 查找 target 字符串
                    index = content.find(target)

                    if index != -1:
                        debug_log(f"Found target in file: {file_path}")

                        # 执行替换
                        new_content = content[:index] + replace + content[index + len(target):]

                        # 写入修改后的内容
                        try:
                            file_path.write_text(new_content, encoding='utf-8')
                            modification_done = True
                            modified_file_path = str(file_path)
                            debug_log(f"Successfully modified file: {file_path}")
                            break  # 安全性检查 2: 找到并修改第一个匹配项后立即停止
                        except IOError as e:
                            print(f"[DailyNoteEditor] Error writing to diary file {file_path}: {e}",
                                  file=sys.stderr, flush=True)
                            break  # 写入失败也算处理了这个文件，退出内层循环
                    else:
                        debug_log(f"Target not found in file: {file_path}")

            except OSError as e:
                print(f"[DailyNoteEditor] Error reading character directory {character_dir}: {e}",
                      file=sys.stderr, flush=True)
                continue

            if modification_done:
                break  # 安全性检查 2: 找到并修改第一个匹配项后立即停止

        if modification_done:
            return {
                "status": "success",
                "result": f"Successfully edited diary file: {modified_file_path}"
            }
        else:
            return {
                "status": "error",
                "error": "Target content not found in any diary files."
            }

    except Exception as error:
        print(f"[DailyNoteEditor] Unexpected error during processing: {error}",
              file=sys.stderr, flush=True)
        return {
            "status": "error",
            "error": f"An unexpected error occurred: {str(error)}"
        }


def main():
    """主函数：从 stdin 读取输入并处理请求"""
    try:
        # 读取 stdin
        input_data = sys.stdin.read()

        if not input_data.strip():
            output = {
                "status": "error",
                "error": "DailyNoteEditor Plugin Error: No input data received."
            }
            print(json.dumps(output, ensure_ascii=False), file=sys.stdout, flush=True)
            sys.exit(1)
            return

        # 处理请求
        result = process_edit_request(input_data)

        # 输出结果到 stdout
        print(json.dumps(result, ensure_ascii=False), file=sys.stdout, flush=True)

        # 根据状态设置退出码
        sys.exit(0 if result.get('status') == 'success' else 1)

    except Exception as e:
        output = {
            "status": "error",
            "error": f"DailyNoteEditor Plugin Error: {str(e)}"
        }
        print(json.dumps(output, ensure_ascii=False), file=sys.stdout, flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
