import os
import sys
import json
from pathlib import Path
from datetime import datetime


def debug_log(message, *args):
    """输出调试日志到 stderr"""
    debug_mode = os.getenv('DebugMode', 'false').lower() == 'true'
    if debug_mode:
        print(f"[DailyNoteWrite][Debug] {message}", *args, file=sys.stderr)


def send_output(data):
    """发送输出到 stdout"""
    try:
        json_string = json.dumps(data, ensure_ascii=False)
        print(json_string)
        debug_log('Sent output to stdout:', json_string)
    except Exception as e:
        print(f"[DailyNoteWrite] Error stringifying output: {e}", file=sys.stderr)
        print(json.dumps({"status": "error", "message": "Internal error: Failed to stringify output."}))


def write_diary(maid_name, date_string, content_text):
    """写入日记内容"""
    debug_log(f"Processing diary write for Maid: {maid_name}, Date: {date_string}")
    
    if not maid_name or not date_string or not content_text:
        raise ValueError('Invalid input: Missing Maid, Date, or Content.')

    # 规范化日期格式
    date_part = date_string.replace('-', '.').replace('/', '.')
    
    # 生成时间戳
    now = datetime.now()
    time_string_for_file = now.strftime('%H_%M_%S')

    # 确定目录和文件路径
    project_base_path = os.getenv('PROJECT_BASE_PATH')
    if project_base_path:
        daily_note_root_path = Path(project_base_path) / 'dailynote'
    else:
        daily_note_root_path = Path(__file__).parent.parent.parent / 'dailynote'
    
    dir_path = daily_note_root_path / maid_name
    base_filename = f"{date_part}-{time_string_for_file}"
    final_filename = f"{base_filename}.txt"
    file_path = dir_path / final_filename

    debug_log(f"Target file path: {file_path}")

    # 创建目录并写入文件
    dir_path.mkdir(parents=True, exist_ok=True)
    file_content = f"[{date_part}] - {maid_name}\n{content_text}"
    file_path.write_text(file_content, encoding='utf-8')
    
    debug_log(f"Successfully wrote file (length: {len(file_content)})")
    return str(file_path)


def main():
    """主函数"""
    try:
        # 从 stdin 读取输入
        input_data = sys.stdin.read()
        debug_log('Received stdin data:', input_data)

        if not input_data:
            raise ValueError("No input data received via stdin.")

        diary_data = json.loads(input_data)
        maid_name = diary_data.get('maidName')
        date_string = diary_data.get('dateString')
        content_text = diary_data.get('contentText')

        saved_file_path = write_diary(maid_name, date_string, content_text)
        send_output({
            "status": "success",
            "message": f"Diary saved to {saved_file_path}"
        })

    except Exception as error:
        print(f"[DailyNoteWrite] Error processing request: {error}", file=sys.stderr)
        send_output({
            "status": "error",
            "message": str(error) or "An unknown error occurred."
        })
        sys.exit(1)


if __name__ == '__main__':
    main()
