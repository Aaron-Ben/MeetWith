import os
import sys
import json
from pathlib import Path


def debug_log(message, *args):
    """输出调试日志到 stderr"""
    debug_mode = os.getenv('DebugMode', 'false').lower() == 'true'
    if debug_mode:
        print(f"[DailyNoteGet][Debug] {message}", *args, file=sys.stderr)


def get_all_character_diaries():
    """获取所有角色的日记内容"""
    project_base_path = os.getenv('PROJECT_BASE_PATH')
    if project_base_path:
        daily_note_root_path = Path(project_base_path) / 'dailynote'
    else:
        # 回退到相对路径
        daily_note_root_path = Path(__file__).parent.parent.parent / 'dailynote'
    
    all_diaries = {}
    debug_log(f"Starting diary scan in: {daily_note_root_path}")

    try:
        if not daily_note_root_path.exists():
            debug_log(f"Daily note root directory not found at {daily_note_root_path}")
            return '{}'

        character_dirs = [d for d in daily_note_root_path.iterdir() if d.is_dir()]

        for character_dir in character_dirs:
            character_name = character_dir.name
            character_dir_path = daily_note_root_path / character_name
            character_diary_content = ''
            debug_log(f"Scanning directory for character: {character_name}")

            try:
                files = list(character_dir_path.iterdir())
                txt_files = sorted([f for f in files if f.suffix.lower() == '.txt'])
                debug_log(f"Found {len(txt_files)} .txt files for {character_name}")

                if txt_files:
                    file_contents = []
                    for txt_file in txt_files:
                        try:
                            content = txt_file.read_text(encoding='utf-8')
                            debug_log(f"Read content from {txt_file.name} (length: {len(content)})")
                            file_contents.append(content)
                        except Exception as read_err:
                            print(f"[DailyNoteGet] Error reading diary file {txt_file}: {read_err}", file=sys.stderr)
                            file_contents.append(f"[Error reading file: {txt_file.name}]")
                    
                    # 用分隔符合并内容
                    character_diary_content = '\n\n---\n\n'.join(file_contents)
                else:
                    character_diary_content = f"[{character_name}日记本内容为空]"
                    debug_log(f"No .txt files found for {character_name}, setting content to empty marker.")

            except Exception as char_dir_error:
                print(f"[DailyNoteGet] Error reading character directory {character_dir_path}: {char_dir_error}", file=sys.stderr)
                character_diary_content = f"[Error reading {character_name}'s diary directory]"

            all_diaries[character_name] = character_diary_content

        debug_log(f"Finished diary scan. Found diaries for {len(all_diaries)} characters.")

    except Exception as error:
        print(f"[DailyNoteGet] Error reading daily note root directory {daily_note_root_path}: {error}", file=sys.stderr)
        return '{}'

    # 返回 JSON 字符串
    return json.dumps(all_diaries, ensure_ascii=False)


def main():
    """主函数"""
    try:
        result_json_string = get_all_character_diaries()
        print(result_json_string)
        debug_log('Successfully wrote diary JSON to stdout.')
    except Exception as e:
        print(f"[DailyNoteGet] Fatal error during execution: {e}", file=sys.stderr)
        print('{}')
        sys.exit(1)


if __name__ == '__main__':
    main()
