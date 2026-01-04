import re
import json
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException

# 配置日志
logger = logging.getLogger(__name__)

# ==================== Admin API 路由 ====================

BASE_DIR = Path(__file__).parent.parent
PLUGIN_DIR = BASE_DIR / 'plugins'
DAILY_NOTE_ROOT = BASE_DIR / 'dailynote'
MANIFEST_FILE = 'plugin-manifest.json'
BLOCKED_EXTENSION = '.block'
PREVIEW_LENGTH = 100


def register_routes(app: FastAPI):
    """Register all admin routes with the FastAPI app"""

    @app.get("/admin_api/config/main")
    async def get_main_config():
        """获取主配置文件内容（过滤敏感信息）"""
        try:
            config_path = BASE_DIR / 'config.env'
            content = config_path.read_text(encoding='utf-8')
            # 过滤敏感信息
            filtered_lines = []
            for line in content.split('\n'):
                if not re.match(r'^\s*(AdminPassword|AdminUsername)\s*=', line, re.IGNORECASE):
                    filtered_lines.append(line)
            filtered_content = '\n'.join(filtered_lines)
            return {'content': filtered_content}
        except Exception as e:
            logger.error('Error reading main config for admin panel:', e)
            raise HTTPException(status_code=500, detail=f'Failed to read main config file: {str(e)}')

    @app.get("/admin_api/config/main/raw")
    async def get_main_config_raw():
        """获取原始主配置文件内容"""
        try:
            config_path = BASE_DIR / 'config.env'
            content = config_path.read_text(encoding='utf-8')
            return {'content': content}
        except Exception as e:
            logger.error('Error reading raw main config for admin panel:', e)
            raise HTTPException(status_code=500, detail=f'Failed to read raw main config file: {str(e)}')

    @app.post("/admin_api/config/main")
    async def save_main_config(request: Request):
        """保存主配置文件内容"""
        try:
            body = await request.json()
            content = body.get('content')
            if not isinstance(content, str):
                raise HTTPException(status_code=400, detail='Invalid content format. String expected.')

            config_path = BASE_DIR / 'config.env'
            config_path.write_text(content, encoding='utf-8')
            return {'message': '主配置已成功保存。更改可能需要重启服务才能完全生效。'}
        except HTTPException:
            raise
        except Exception as e:
            logger.error('Error writing main config for admin panel:', e)
            raise HTTPException(status_code=500, detail=f'Failed to write main config file: {str(e)}')

    @app.get("/admin_api/plugins")
    async def list_plugins():
        """获取插件列表及其状态"""
        try:
            plugin_data_list = []

            if not PLUGIN_DIR.exists():
                return []

            for folder in PLUGIN_DIR.iterdir():
                if folder.is_dir():
                    plugin_path = folder
                    manifest_path = plugin_path / MANIFEST_FILE
                    blocked_manifest_path = manifest_path.with_suffix(manifest_path.suffix + BLOCKED_EXTENSION)

                    manifest = None
                    is_enabled = False
                    config_env_content = None

                    # 尝试读取启用的 manifest
                    try:
                        manifest_content = manifest_path.read_text(encoding='utf-8')
                        manifest = json.loads(manifest_content)
                        is_enabled = True
                    except FileNotFoundError:
                        # 尝试读取禁用的 manifest
                        try:
                            manifest_content = blocked_manifest_path.read_text(encoding='utf-8')
                            manifest = json.loads(manifest_content)
                            is_enabled = False
                        except FileNotFoundError:
                            continue
                        except json.JSONDecodeError:
                            logger.warning(f'[AdminPanel] Invalid JSON in blocked manifest for {folder.name}')
                            continue
                    except json.JSONDecodeError:
                        logger.warning(f'[AdminPanel] Invalid JSON in manifest for {folder.name}')
                        continue

                    # 尝试读取插件配置
                    try:
                        plugin_config_path = plugin_path / 'config.env'
                        config_env_content = plugin_config_path.read_text(encoding='utf-8')
                    except FileNotFoundError:
                        pass
                    except Exception as e:
                        logger.warning(f'[AdminPanel] Error reading config.env for {folder.name}: {e}')

                    if manifest and manifest.get('name'):
                        plugin_data_list.append({
                            'name': manifest['name'],
                            'manifest': manifest,
                            'enabled': is_enabled,
                            'configEnvContent': config_env_content
                        })

            return plugin_data_list
        except Exception as e:
            logger.error('[AdminPanel] Error listing plugins:', e)
            raise HTTPException(status_code=500, detail=f'Failed to list plugins: {str(e)}')

    @app.post("/admin_api/plugins/{plugin_name}/toggle")
    async def toggle_plugin(plugin_name: str, request: Request):
        """切换插件启用/禁用状态"""
        try:
            body = await request.json()
            enable = body.get('enable')
            if not isinstance(enable, bool):
                raise HTTPException(status_code=400, detail='Invalid request body. Expected { enable: boolean }.')

            # 查找插件文件夹
            target_plugin_path = None
            current_manifest_path = None
            current_blocked_path = None
            found_manifest = None

            if not PLUGIN_DIR.exists():
                raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found.")

            for folder in PLUGIN_DIR.iterdir():
                if not folder.is_dir():
                    continue

                potential_manifest_path = folder / MANIFEST_FILE
                potential_blocked_path = potential_manifest_path.with_suffix(
                    potential_manifest_path.suffix + BLOCKED_EXTENSION
                )

                manifest_content = None

                # 尝试读取启用的 manifest
                try:
                    manifest_content = potential_manifest_path.read_text(encoding='utf-8')
                    current_manifest_path = potential_manifest_path
                    current_blocked_path = potential_blocked_path
                except FileNotFoundError:
                    # 尝试读取禁用的 manifest
                    try:
                        manifest_content = potential_blocked_path.read_text(encoding='utf-8')
                        current_manifest_path = potential_manifest_path
                        current_blocked_path = potential_blocked_path
                    except FileNotFoundError:
                        continue

                try:
                    manifest = json.loads(manifest_content)
                    if manifest.get('name') == plugin_name:
                        target_plugin_path = folder
                        found_manifest = manifest
                        break
                except json.JSONDecodeError:
                    continue

            if not target_plugin_path or not found_manifest:
                raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found.")

            manifest_path = current_manifest_path
            blocked_manifest_path = current_blocked_path

            if enable:
                # 启用：将 .block 重命名为 .json
                try:
                    if blocked_manifest_path.exists():
                        blocked_manifest_path.rename(manifest_path)
                    return {'message': f'插件 {plugin_name} 已启用。请注意，更改可能需要重启服务才能完全生效。'}
                except FileNotFoundError:
                    # 已经是启用状态
                    if manifest_path.exists():
                        return {'message': f'插件 {plugin_name} 已经是启用状态。'}
                    raise HTTPException(
                        status_code=500,
                        detail=f'无法启用插件 {plugin_name}。找不到 manifest 文件。'
                    )
            else:
                # 禁用：将 .json 重命名为 .block
                try:
                    if manifest_path.exists():
                        manifest_path.rename(blocked_manifest_path)
                    return {'message': f'插件 {plugin_name} 已禁用。请注意，更改可能需要重启服务才能完全生效。'}
                except FileNotFoundError:
                    # 已经是禁用状态
                    if blocked_manifest_path.exists():
                        return {'message': f'插件 {plugin_name} 已经是禁用状态。'}
                    raise HTTPException(
                        status_code=500,
                        detail=f'无法禁用插件 {plugin_name}。找不到 manifest 文件。'
                    )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f'[AdminPanel] Error toggling plugin {plugin_name}:', e)
            raise HTTPException(status_code=500, detail=f'处理插件状态切换时出错: {str(e)}')

    @app.post("/admin_api/plugins/{plugin_name}/description")
    async def update_plugin_description(plugin_name: str, request: Request):
        """更新插件描述"""
        try:
            body = await request.json()
            description = body.get('description')
            if not isinstance(description, str):
                raise HTTPException(status_code=400, detail='Invalid request body. Expected { description: string }.')

            # 查找插件
            target_manifest_path = None
            manifest = None

            if not PLUGIN_DIR.exists():
                raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found.")

            for folder in PLUGIN_DIR.iterdir():
                if not folder.is_dir():
                    continue

                potential_manifest_path = folder / MANIFEST_FILE
                potential_blocked_path = potential_manifest_path.with_suffix(
                    potential_manifest_path.suffix + BLOCKED_EXTENSION
                )

                current_path = None
                manifest_content = None

                # 尝试读取启用的 manifest
                try:
                    manifest_content = potential_manifest_path.read_text(encoding='utf-8')
                    current_path = potential_manifest_path
                except FileNotFoundError:
                    # 尝试读取禁用的 manifest
                    try:
                        manifest_content = potential_blocked_path.read_text(encoding='utf-8')
                        current_path = potential_blocked_path
                    except FileNotFoundError:
                        continue

                try:
                    parsed_manifest = json.loads(manifest_content)
                    if parsed_manifest.get('name') == plugin_name:
                        target_manifest_path = current_path
                        manifest = parsed_manifest
                        break
                except json.JSONDecodeError:
                    continue

            if not target_manifest_path or not manifest:
                raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' or its manifest file not found.")

            # 更新描述
            manifest['description'] = description
            target_manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')

            return {'message': f'插件 {plugin_name} 的描述已更新。'}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f'[AdminPanel] Error updating description for plugin {plugin_name}:', e)
            raise HTTPException(status_code=500, detail=f'更新插件描述时出错: {str(e)}')

    @app.post("/admin_api/plugins/{plugin_name}/config")
    async def save_plugin_config(plugin_name: str, request: Request):
        """保存插件配置"""
        try:
            body = await request.json()
            content = body.get('content')
            if not isinstance(content, str):
                raise HTTPException(status_code=400, detail='Invalid content format. String expected.')

            # 查找插件文件夹
            target_plugin_path = None

            if not PLUGIN_DIR.exists():
                raise HTTPException(status_code=404, detail=f"Plugin folder for '{plugin_name}' not found.")

            for folder in PLUGIN_DIR.iterdir():
                if not folder.is_dir():
                    continue

                potential_manifest_path = folder / MANIFEST_FILE
                potential_blocked_path = potential_manifest_path.with_suffix(
                    potential_manifest_path.suffix + BLOCKED_EXTENSION
                )

                manifest_content = None
                try:
                    manifest_content = potential_manifest_path.read_text(encoding='utf-8')
                except FileNotFoundError:
                    try:
                        manifest_content = potential_blocked_path.read_text(encoding='utf-8')
                    except FileNotFoundError:
                        continue

                try:
                    manifest = json.loads(manifest_content)
                    if manifest.get('name') == plugin_name:
                        target_plugin_path = folder
                        break
                except json.JSONDecodeError:
                    continue

            if not target_plugin_path:
                raise HTTPException(status_code=404, detail=f"Plugin folder for '{plugin_name}' not found.")

            config_path = target_plugin_path / 'config.env'
            config_path.write_text(content, encoding='utf-8')

            return {'message': f'插件 {plugin_name} 的配置已保存。更改可能需要重启插件或服务才能生效。'}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f'[AdminPanel] Error writing config.env for plugin {plugin_name}:', e)
            raise HTTPException(status_code=500, detail=f'保存插件配置时出错: {str(e)}')

    @app.post("/admin_api/plugins/{plugin_name}/commands/{command_identifier}/description")
    async def update_command_description(plugin_name: str, command_identifier: str, request: Request):
        """更新插件中指定指令的描述"""
        try:
            body = await request.json()
            description = body.get('description')
            if not isinstance(description, str):
                raise HTTPException(status_code=400, detail='Invalid request body. Expected { description: string }.')

            # 查找插件
            target_manifest_path = None
            manifest = None

            if not PLUGIN_DIR.exists():
                raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found.")

            for folder in PLUGIN_DIR.iterdir():
                if not folder.is_dir():
                    continue

                potential_manifest_path = folder / MANIFEST_FILE
                potential_blocked_path = potential_manifest_path.with_suffix(
                    potential_manifest_path.suffix + BLOCKED_EXTENSION
                )

                current_path = None
                manifest_content = None

                # 尝试读取启用的 manifest
                try:
                    manifest_content = potential_manifest_path.read_text(encoding='utf-8')
                    current_path = potential_manifest_path
                except FileNotFoundError:
                    # 尝试读取禁用的 manifest
                    try:
                        manifest_content = potential_blocked_path.read_text(encoding='utf-8')
                        current_path = potential_blocked_path
                    except FileNotFoundError:
                        continue

                try:
                    parsed_manifest = json.loads(manifest_content)
                    if parsed_manifest.get('name') == plugin_name:
                        target_manifest_path = current_path
                        manifest = parsed_manifest
                        break
                except json.JSONDecodeError:
                    continue

            if not target_manifest_path or not manifest:
                raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' or its manifest file not found.")

            # 更新指令描述
            command_updated = False
            if manifest.get('capabilities') and manifest['capabilities'].get('invocationCommands'):
                invocation_commands = manifest['capabilities']['invocationCommands']
                if isinstance(invocation_commands, list):
                    for i, cmd in enumerate(invocation_commands):
                        if cmd.get('commandIdentifier') == command_identifier or cmd.get('command') == command_identifier:
                            invocation_commands[i]['description'] = description
                            command_updated = True
                            break

            if not command_updated:
                raise HTTPException(status_code=404, detail=f"Command '{command_identifier}' not found in plugin '{plugin_name}'.")

            # 保存更新后的 manifest
            target_manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
            return {'message': f"指令 '{command_identifier}' 在插件 '{plugin_name}' 中的描述已更新。"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f'[AdminPanel] Error updating command description for plugin {plugin_name}, command {command_identifier}:', e)
            raise HTTPException(status_code=500, detail=f'更新指令描述时出错: {str(e)}')

    @app.post("/admin_api/server/restart")
    async def restart_server():
        """重启服务器"""
        import asyncio
        import sys

        # 在后台任务中延迟退出，让响应先发送给客户端
        async def delayed_shutdown():
            await asyncio.sleep(1)
            logger.info('[AdminPanel] Received restart command. Shutting down...')
            sys.exit(1)

        asyncio.create_task(delayed_shutdown())
        return {'message': '服务器重启命令已发送。服务器正在关闭，如果由进程管理器（如 PM2）管理，它应该会自动重启。'}

    @app.get("/admin_api/dailynotes/folders")
    async def get_daily_note_folders():
        """获取日记根目录下的所有文件夹（角色列表）"""
        try:
            if not DAILY_NOTE_ROOT.exists():
                logger.warning('[DailyNotes] dailynote directory not found.')
                return {'folders': []}

            folders = [d.name for d in DAILY_NOTE_ROOT.iterdir() if d.is_dir()]
            return {'folders': folders}
        except Exception as e:
            logger.error('[DailyNotes] Error listing folders:', e)
            raise HTTPException(status_code=500, detail=f'Failed to list folders: {str(e)}')

    @app.get("/admin_api/dailynotes/folder/{folder_name}")
    async def get_daily_note_folder(folder_name: str):
        """获取指定文件夹中的所有日记文件"""
        try:
            folder_path = DAILY_NOTE_ROOT / folder_name
            if not folder_path.exists():
                raise HTTPException(status_code=404, detail=f"Folder '{folder_name}' not found.")

            notes = []
            for file_path in sorted(folder_path.glob('*.txt'), key=lambda p: p.name):
                stats = file_path.stat()
                preview = ''
                try:
                    content = file_path.read_text(encoding='utf-8')
                    preview = content.replace('\n', ' ')[:PREVIEW_LENGTH]
                    if len(content) > PREVIEW_LENGTH:
                        preview += '...'
                except Exception:
                    preview = '[无法加载预览]'

                notes.append({
                    'name': file_path.name,
                    'folderName': folder_name,
                    'lastModified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                    'preview': preview
                })

            return {'notes': notes}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f'[DailyNotes] Error listing notes in folder {folder_name}:', e)
            raise HTTPException(status_code=500, detail=f'Failed to list notes: {str(e)}')

    @app.get("/admin_api/dailynotes/search")
    async def search_daily_notes(term: Optional[str] = None, folder: Optional[str] = None):
        """搜索日记内容"""
        if not term or not term.strip():
            raise HTTPException(status_code=400, detail='Search term is required.')

        search_term = term.strip().lower()
        matched_notes = []

        try:
            # 确定要搜索的文件夹
            folders_to_search = []
            if folder and folder.strip():
                specific_folder = DAILY_NOTE_ROOT / folder.strip()
                if not specific_folder.exists() or not specific_folder.is_dir():
                    raise HTTPException(status_code=404, detail=f"Folder '{folder}' not found.")
                folders_to_search.append(specific_folder)
            else:
                if not DAILY_NOTE_ROOT.exists():
                    return {'notes': []}
                folders_to_search = [d for d in DAILY_NOTE_ROOT.iterdir() if d.is_dir()]

            # 搜索文件
            for folder_path in folders_to_search:
                for file_path in folder_path.glob('*.txt'):
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        if search_term in content.lower():
                            stats = file_path.stat()
                            preview = content.replace('\n', ' ')[:PREVIEW_LENGTH]
                            if len(content) > PREVIEW_LENGTH:
                                preview += '...'
                            matched_notes.append({
                                'name': file_path.name,
                                'folderName': folder_path.name,
                                'lastModified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                                'preview': preview
                            })
                    except Exception as e:
                        logger.warning(f'[DailyNotes] Error reading file {file_path}: {e}')

            # 排序
            matched_notes.sort(key=lambda x: (x['folderName'], x['name']))
            return {'notes': matched_notes}

        except HTTPException:
            raise
        except Exception as e:
            logger.error('[DailyNotes] Error during search:', e)
            raise HTTPException(status_code=500, detail=f'Search failed: {str(e)}')

    @app.get("/admin_api/dailynotes/note/{folder_name}/{file_name}")
    async def get_daily_note(folder_name: str, file_name: str):
        """获取指定日记文件的内容"""
        try:
            file_path = DAILY_NOTE_ROOT / folder_name / file_name
            if not file_path.exists():
                raise HTTPException(status_code=404, detail=f"Note '{file_name}' not found in folder '{folder_name}'.")

            content = file_path.read_text(encoding='utf-8')
            return {'content': content}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f'[DailyNotes] Error reading note {folder_name}/{file_name}:', e)
            raise HTTPException(status_code=500, detail=f'Failed to read note: {str(e)}')

    @app.post("/admin_api/dailynotes/note/{folder_name}/{file_name}")
    async def save_daily_note(folder_name: str, file_name: str, request: Request):
        """保存日记内容"""
        try:
            body = await request.json()
            content = body.get('content')
            if not isinstance(content, str):
                raise HTTPException(status_code=400, detail='Invalid content format. String expected.')

            folder_path = DAILY_NOTE_ROOT / folder_name
            file_path = folder_path / file_name

            folder_path.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')

            return {'message': f"Note '{file_name}' in folder '{folder_name}' saved successfully."}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f'[DailyNotes] Error saving note {folder_name}/{file_name}:', e)
            raise HTTPException(status_code=500, detail=f'Failed to save note: {str(e)}')

    @app.post("/admin_api/dailynotes/move")
    async def move_daily_notes(request: Request):
        """移动一个或多个日记到不同文件夹"""
        try:
            body = await request.json()
            source_notes = body.get('sourceNotes', [])
            target_folder = body.get('targetFolder', '')

            if not isinstance(source_notes, list) or not target_folder:
                raise HTTPException(status_code=400, detail='Invalid request body.')

            # 验证格式
            for note in source_notes:
                if not isinstance(note, dict) or 'folder' not in note or 'file' not in note:
                    raise HTTPException(status_code=400, detail='Invalid sourceNotes format.')

            target_path = DAILY_NOTE_ROOT / target_folder
            target_path.mkdir(parents=True, exist_ok=True)

            results = {'moved': [], 'errors': []}

            for note in source_notes:
                source_file = DAILY_NOTE_ROOT / note['folder'] / note['file']
                dest_file = target_path / note['file']

                try:
                    if not source_file.exists():
                        results['errors'].append({
                            'note': f"{note['folder']}/{note['file']}",
                            'error': 'Source file not found.'
                        })
                        continue

                    if dest_file.exists():
                        results['errors'].append({
                            'note': f"{note['folder']}/{note['file']}",
                            'error': f"File already exists at destination '{target_folder}/{note['file']}'."
                        })
                        continue

                    source_file.rename(dest_file)
                    results['moved'].append(f"{note['folder']}/{note['file']} to {target_folder}/{note['file']}")

                except Exception as e:
                    logger.error(f'[DailyNotes] Error moving note {note["folder"]}/{note["file"]}:', e)
                    results['errors'].append({
                        'note': f"{note['folder']}/{note['file']}",
                        'error': str(e)
                    })

            message = f"Moved {len(results['moved'])} note(s). {len(results['errors']) > 0 and f'Encountered {len(results['errors'])} error(s).' or ''}"
            return {'message': message, 'moved': results['moved'], 'errors': results['errors']}

        except HTTPException:
            raise
        except Exception as e:
            logger.error('[DailyNotes] Error moving notes:', e)
            raise HTTPException(status_code=500, detail=f'Failed to move notes: {str(e)}')

    @app.post("/admin_api/dailynotes/delete-batch")
    async def delete_daily_notes_batch(request: Request):
        """批量删除日记文件"""
        try:
            body = await request.json()
            notes_to_delete = body.get('notesToDelete', [])

            if not isinstance(notes_to_delete, list):
                raise HTTPException(status_code=400, detail='Invalid request body.')

            # 验证格式
            for note in notes_to_delete:
                if not isinstance(note, dict) or 'folder' not in note or 'file' not in note:
                    raise HTTPException(status_code=400, detail='Invalid notesToDelete format.')

            results = {'deleted': [], 'errors': []}

            for note in notes_to_delete:
                file_path = DAILY_NOTE_ROOT / note['folder'] / note['file']
                try:
                    if not file_path.exists():
                        results['errors'].append({
                            'note': f"{note['folder']}/{note['file']}",
                            'error': 'File not found.'
                        })
                        continue

                    file_path.unlink()
                    results['deleted'].append(f"{note['folder']}/{note['file']}")

                except Exception as e:
                    logger.error(f'[DailyNotes] Error deleting note {note["folder"]}/{note["file"]}:', e)
                    results['errors'].append({
                        'note': f"{note['folder']}/{note['file']}",
                        'error': str(e)
                    })

            message = f"Deleted {len(results['deleted'])} note(s). {len(results['errors']) > 0 and f'Encountered {len(results["errors"])} error(s).' or ''}"
            return {'message': message, 'deleted': results['deleted'], 'errors': results['errors']}

        except HTTPException:
            raise
        except Exception as e:
            logger.error('[DailyNotes] Error deleting notes:', e)
            raise HTTPException(status_code=500, detail=f'Failed to delete notes: {str(e)}')
