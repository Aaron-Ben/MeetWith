"""
插件管理器，统一管理，加载，执行不同类型插件
"""

import os
import json
import asyncio
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import dotenv_values, load_dotenv


class PluginManager:
    """插件管理器核心类"""

    def __init__(self):
        # 插件存储
        self.plugins: Dict[str, dict] = {}
        self.static_placeholder_values: Dict[str, str] = {}
        self.individual_plugin_descriptions: Dict[str, str] = {}

        # 不同类型插件的存储
        self.message_preprocessors: Dict[str, Any] = {}
        self.service_modules: Dict[str, Any] = {}

        # 项目路径
        self.project_base_path: Optional[str] = None

        # 定时任务调度器
        self.scheduler = AsyncIOScheduler()

        # 插件目录
        self.plugin_dir = Path(__file__).parent / "plugins"
        self.manifest_filename = "plugin-manifest.json"

    def set_project_base_path(self, base_path: str):
        """设置项目基础路径"""
        self.project_base_path = base_path
        print(f"[PluginManager] Project base path set to: {self.project_base_path}")

    def _get_plugin_config(self, plugin_manifest: dict) -> dict:
        """
        获取插件配置
        优先级: 插件特定 .env > 全局环境变量
        """
        config = {}

        # 全局环境变量
        global_env = dict(os.environ)

        # 插件特定配置 (从 pluginSpecificEnvConfig 读取)
        plugin_specific_env = plugin_manifest.get('pluginSpecificEnvConfig', {})

        # 根据 configSchema 构建配置
        if 'configSchema' in plugin_manifest:
            for key, expected_type in plugin_manifest['configSchema'].items():
                # 优先使用插件特定配置
                raw_value = plugin_specific_env.get(key)

                # 如果插件特定配置没有，使用全局配置
                if raw_value is None:
                    raw_value = global_env.get(key)

                if raw_value is None:
                    continue

                # 类型转换
                try:
                    if expected_type == 'integer':
                        config[key] = int(raw_value)
                    elif expected_type == 'boolean':
                        config[key] = str(raw_value).lower() == 'true'
                    else:
                        config[key] = raw_value
                except (ValueError, TypeError) as e:
                    print(f"[PluginManager] Config key '{key}' for {plugin_manifest.get('name')} "
                          f"expected {expected_type}, got error: {e}")

        # 添加 DebugMode (特殊处理)
        debug_mode = plugin_specific_env.get('DebugMode') or global_env.get('DebugMode', 'false')
        config['DebugMode'] = str(debug_mode).lower() == 'true'

        return config

    def get_resolved_plugin_config_value(self, plugin_name: str, config_key: str) -> Any:
        """获取插件的特定配置值"""
        plugin_manifest = self.plugins.get(plugin_name)
        if not plugin_manifest:
            return None

        effective_config = self._get_plugin_config(plugin_manifest)
        return effective_config.get(config_key)

    async def _execute_static_plugin_command(self, plugin: dict) -> str:
        """执行静态插件命令"""
        if plugin.get('pluginType') != 'static':
            raise ValueError(f"Plugin {plugin.get('name')} is not a static plugin")

        if not plugin.get('entryPoint', {}).get('command'):
            raise ValueError(f"Static plugin {plugin.get('name')} missing command")

        plugin_config = self._get_plugin_config(plugin)
        env = {**os.environ}

        # 添加插件配置到环境变量
        for key, value in plugin_config.items():
            if value is not None:
                env[key] = str(value)

        # 添加项目基础路径
        if self.project_base_path:
            env['PROJECT_BASE_PATH'] = self.project_base_path

        command = plugin['entryPoint']['command']
        cwd = plugin['basePath']

        timeout = plugin.get('communication', {}).get('timeout', 30000) / 1000  # 转换为秒

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=cwd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore').strip()
                raise RuntimeError(f"Plugin exited with code {process.returncode}: {error_msg}")

            return stdout.decode('utf-8', errors='ignore').strip()

        except asyncio.TimeoutError:
            if 'process' in locals():
                process.kill()
            raise TimeoutError(f"Static plugin {plugin.get('name')} execution timed out")

    async def _update_static_plugin_value(self, plugin: dict):
        """更新静态插件的值"""
        try:
            print(f"[PluginManager] Updating static plugin: {plugin['name']}")
            new_value = await self._execute_static_plugin_command(plugin)
        except Exception as e:
            print(f"[PluginManager] Error executing static plugin {plugin['name']}: {e}")
            new_value = None
            error = e

        # 更新占位符值
        capabilities = plugin.get('capabilities', {})
        placeholders = capabilities.get('systemPromptPlaceholders', [])

        for ph in placeholders:
            placeholder_key = ph.get('placeholder')
            current_value = self.static_placeholder_values.get(placeholder_key)

            if new_value is not None and new_value.strip():
                self.static_placeholder_values[placeholder_key] = new_value.strip()
                print(f"[PluginManager] Placeholder {placeholder_key} for {plugin['name']} "
                      f"updated with value: \"{new_value.strip()[:70]}...\"")
            elif 'error' in locals():
                error_message = f"[Error updating {plugin['name']}: {str(error)[:100]}...]"
                if not current_value or (current_value and current_value.startswith("[Error")):
                    self.static_placeholder_values[placeholder_key] = error_message
                    print(f"[PluginManager] Placeholder {placeholder_key} for {plugin['name']} "
                          f"set to error state: {error_message}")
            else:
                print(f"[PluginManager] Static plugin {plugin['name']} produced no output for {placeholder_key}")
                if placeholder_key not in self.static_placeholder_values:
                    self.static_placeholder_values[placeholder_key] = \
                        f"[{plugin['name']} data currently unavailable]"

    async def initialize_static_plugins(self):
        """初始化所有静态插件"""
        print("[PluginManager] Initializing static plugins...")

        for plugin in self.plugins.values():
            if plugin.get('pluginType') == 'static':
                await self._update_static_plugin_value(plugin)

                # 设置定时刷新
                refresh_interval = plugin.get('refreshIntervalCron')
                if refresh_interval:
                    try:
                        # APScheduler 使用 cron 格式
                        self.scheduler.add_job(
                            self._update_static_plugin_value,
                            'cron',
                            args=[plugin],
                            id=plugin['name'],
                            **self._parse_cron(refresh_interval)
                        )
                        print(f"[PluginManager] Scheduled {plugin['name']} with cron: {refresh_interval}")
                    except Exception as e:
                        print(f"[PluginManager] Invalid cron string for {plugin['name']}: {e}")

        if not self.scheduler.running:
            self.scheduler.start()

        print("[PluginManager] Static plugins initialized.")

    def _parse_cron(self, cron_str: str) -> dict:
        """解析 cron 表达式为 APScheduler 格式"""
        # 简单解析，假设格式为 "0 4 * * *" (分 时 日 月 周)
        parts = cron_str.split()
        if len(parts) >= 5:
            return {
                'minute': parts[0],
                'hour': parts[1],
                'day': parts[2],
                'month': parts[3],
                'day_of_week': parts[4]
            }
        return {}

    def get_placeholder_value(self, placeholder: str) -> str:
        """获取占位符的值"""
        return self.static_placeholder_values.get(placeholder) or \
            f"[Placeholder {placeholder} not found]"

    async def execute_message_preprocessor(self, plugin_name: str, messages: List[dict]) -> List[dict]:
        """执行消息预处理器插件"""
        if plugin_name not in self.message_preprocessors:
            print(f"[PluginManager] Message preprocessor plugin '{plugin_name}' not found.")
            return messages

        processor_module = self.message_preprocessors[plugin_name]
        plugin_manifest = self.plugins.get(plugin_name, {})

        if not hasattr(processor_module, 'processMessages'):
            print(f"[PluginManager] Plugin '{plugin_name}' does not have 'processMessages' function.")
            return messages

        try:
            print(f"[PluginManager] Executing message preprocessor: {plugin_name}")
            plugin_config = self._get_plugin_config(plugin_manifest)
            processed_messages = await processor_module.processMessages(messages, plugin_config)
            print(f"[PluginManager] Message preprocessor {plugin_name} finished.")
            return processed_messages
        except Exception as e:
            print(f"[PluginManager] Error in message preprocessor {plugin_name}: {e}")
            return messages

    async def load_plugins(self):
        """发现并加载所有插件"""
        print("[PluginManager] Starting plugin discovery...")
        self.plugins.clear()
        self.static_placeholder_values.clear()
        self.message_preprocessors.clear()
        self.service_modules.clear()

        try:
            plugin_folders = [f for f in self.plugin_dir.iterdir() if f.is_dir()]

            for folder in plugin_folders:
                plugin_path = folder
                manifest_path = plugin_path / self.manifest_filename

                if not manifest_path.exists():
                    continue

                try:
                    manifest_content = manifest_path.read_text(encoding='utf-8')
                    manifest = json.loads(manifest_content)

                    # 验证必需字段
                    required_fields = ['name', 'pluginType', 'entryPoint']
                    if not all(field in manifest for field in required_fields):
                        print(f"[PluginManager] Invalid manifest in {folder.name}: Missing fields.")
                        continue

                    # 检查重复名称
                    if manifest['name'] in self.plugins:
                        print(f"[PluginManager] Duplicate plugin name '{manifest['name']}' in {folder.name}. Skipping.")
                        continue

                    # 设置基础路径
                    manifest['basePath'] = str(plugin_path)

                    # 加载插件特定的 .env 文件
                    env_file = plugin_path / '.env'
                    if env_file.exists():
                        try:
                            plugin_env = dotenv_values(env_file)
                            manifest['pluginSpecificEnvConfig'] = plugin_env
                            print(f"[PluginManager] Loaded specific .env for plugin: {manifest['name']}")
                        except Exception as e:
                            print(f"[PluginManager] Error reading .env for plugin {manifest['name']}: {e}")

                    # 存储插件清单
                    self.plugins[manifest['name']] = manifest
                    print(f"[PluginManager] Loaded manifest: {manifest.get('displayName')} "
                          f"({manifest['name']}, Type: {manifest['pluginType']})")

                    # 加载不同类型的插件模块
                    await self._load_plugin_module(manifest, plugin_path)

                except json.JSONDecodeError as e:
                    print(f"[PluginManager] Invalid JSON in {manifest_path}: {e}")
                except Exception as e:
                    print(f"[PluginManager] Error loading plugin from {folder.name}: {e}")

            # 构建 VCP 描述
            self._build_vcp_description()

            print(f"[PluginManager] Plugin discovery finished. Loaded {len(self.plugins)} plugins.")

        except Exception as e:
            print(f"[PluginManager] Error reading plugin directory: {e}")

    async def _load_plugin_module(self, manifest: dict, plugin_path: Path):
        """加载插件模块"""
        plugin_type = manifest['pluginType']
        entry_point = manifest.get('entryPoint', {})
        communication = manifest.get('communication', {})

        if plugin_type == 'messagePreprocessor':
            if entry_point.get('script') and communication.get('protocol') == 'direct':
                script_path = plugin_path / entry_point['script']
                if script_path.exists():
                    try:
                        # 动态导入 Python 模块
                        import importlib.util
                        spec = importlib.util.spec_from_file_location(
                            manifest['name'], script_path
                        )
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        # 初始化
                        plugin_config = self._get_plugin_config(manifest)
                        if hasattr(module, 'initialize'):
                            await module.initialize(plugin_config)
                            print(f"[PluginManager] Initialized messagePreprocessor: {manifest['name']}")

                        self.message_preprocessors[manifest['name']] = module
                    except Exception as e:
                        print(f"[PluginManager] Error loading messagePreprocessor {manifest['name']}: {e}")

        elif plugin_type == 'service':
            if entry_point.get('script') and communication.get('protocol') == 'direct':
                script_path = plugin_path / entry_point['script']
                if script_path.exists():
                    try:
                        import importlib.util
                        spec = importlib.util.spec_from_file_location(
                            manifest['name'], script_path
                        )
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        if hasattr(module, 'registerRoutes'):
                            self.service_modules[manifest['name']] = {
                                'manifest': manifest,
                                'module': module
                            }
                            print(f"[PluginManager] Loaded service module: {manifest['name']}")
                        else:
                            print(f"[PluginManager] Service plugin {manifest['name']} "
                                  "does not have 'registerRoutes' function.")
                    except Exception as e:
                        print(f"[PluginManager] Error loading service plugin {manifest['name']}: {e}")

    def _build_vcp_description(self):
        """构建各个插件的 VCP 描述"""
        self.individual_plugin_descriptions.clear()

        for plugin in self.plugins.values():
            capabilities = plugin.get('capabilities', {})
            invocation_commands = capabilities.get('invocationCommands', [])

            if invocation_commands:
                plugin_descriptions = []

                for cmd in invocation_commands:
                    if cmd.get('description'):
                        command_description = \
                            f"- {plugin.get('displayName')} ({plugin['name']}) - " \
                            f"命令: {cmd.get('command', 'N/A')}:\n"

                        indented_desc = '\n    '.join(cmd['description'].split('\n'))
                        command_description += f"    {indented_desc}"

                        if cmd.get('example'):
                            example_header = "\n  调用示例:\n"
                            indented_example = '\n    '.join(cmd['example'].split('\n'))
                            command_description += example_header + f"    {indented_example}"

                        plugin_descriptions.append(command_description)

                if plugin_descriptions:
                    placeholder_key = f"VCP{plugin['name']}"
                    full_description = '\n\n'.join(plugin_descriptions)
                    self.individual_plugin_descriptions[placeholder_key] = full_description

        print(f"[PluginManager] Built {len(self.individual_plugin_descriptions)} plugin descriptions")

    def get_individual_plugin_descriptions(self) -> Dict[str, str]:
        """获取所有插件的描述"""
        return self.individual_plugin_descriptions

    def get_plugin(self, name: str) -> Optional[dict]:
        """获取插件清单"""
        return self.plugins.get(name)

    async def process_tool_call(self, tool_name: str, tool_args: dict) -> Any:
        """
        处理工具调用
        这是 server.py 调用的主要接口
        """
        plugin = self.plugins.get(tool_name)
        if not plugin:
            raise ValueError(f"Plugin '{tool_name}' not found for tool call.")

        # 验证插件类型
        if plugin.get('pluginType') != 'synchronous':
            raise ValueError(f"Plugin '{tool_name}' is not a synchronous plugin")

        protocol = plugin.get('communication', {}).get('protocol')
        if protocol != 'stdio':
            raise ValueError(f"Plugin '{tool_name}' does not use stdio protocol")

        # 准备执行参数
        execution_param = self._prepare_execution_param(tool_name, tool_args)

        print(f"[PluginManager processToolCall] Calling executePlugin for: {tool_name} "
              f"with param: {str(execution_param)[:100] if execution_param else None}...")

        try:
            plugin_output = await self.execute_plugin(tool_name, execution_param)

            if plugin_output.get('status') == 'success':
                return plugin_output.get('result')
            else:
                raise ValueError(plugin_output.get('error') or
                               f"Plugin '{tool_name}' reported an unspecified error")

        except Exception as e:
            print(f"[PluginManager processToolCall] Error executing plugin {tool_name}: {e}")
            raise

    def _prepare_execution_param(self, tool_name: str, tool_args: dict) -> Optional[str]:
        """准备插件执行参数"""
        if tool_name == "SciCalculator":
            if isinstance(tool_args.get('expression'), str):
                return tool_args['expression']
            raise ValueError("Missing or invalid 'expression' argument for SciCalculator")

        elif tool_name == "FluxGen":
            if (isinstance(tool_args, dict) and
                isinstance(tool_args.get('prompt'), str) and
                isinstance(tool_args.get('resolution'), str)):
                return json.dumps(tool_args)
            raise ValueError("Invalid arguments for FluxGen")

        # 其他插件
        if tool_args and isinstance(tool_args, dict) and tool_args:
            return json.dumps(tool_args)
        elif isinstance(tool_args, str) and tool_args.strip():
            return tool_args

        return None

    async def execute_plugin(self, plugin_name: str, input_data: Optional[str]) -> dict:
        """
        执行同步插件 (stdio 协议)
        返回: {"status": "success"|"error", "result": ...|"error": ...}
        """
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_name}' not found")

        if plugin.get('pluginType') != 'synchronous':
            raise ValueError(f"Plugin '{plugin_name}' is not a synchronous plugin")

        if not plugin.get('entryPoint', {}).get('command'):
            raise ValueError(f"Plugin '{plugin_name}' missing entry point command")

        plugin_config = self._get_plugin_config(plugin)
        env = {**os.environ}

        # 添加配置到环境变量
        for key, value in plugin_config.items():
            if value is not None:
                env[key] = str(value)

        # 添加额外环境变量
        if self.project_base_path:
            env['PROJECT_BASE_PATH'] = self.project_base_path
        if os.getenv('PORT'):
            env['SERVER_PORT'] = os.getenv('PORT')

        image_server_key = self.get_resolved_plugin_config_value('ImageServer', 'Image_Key')
        if image_server_key:
            env['IMAGESERVER_IMAGE_KEY'] = image_server_key

        # 强制 UTF-8 编码
        env['PYTHONIOENCODING'] = 'utf-8'

        command = plugin['entryPoint']['command']
        cwd = plugin['basePath']
        timeout = plugin.get('communication', {}).get('timeout', 5000) / 1000

        try:
            print(f"[PluginManager executePlugin] Spawning: {command} in {cwd}")

            process = await asyncio.create_subprocess_shell(
                command,
                cwd=cwd,
                env=env,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )

            # 写入输入数据
            stdin_data = None
            if input_data is not None:
                stdin_data = input_data.encode('utf-8')

            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=stdin_data),
                timeout=timeout
            )

            output = stdout.decode('utf-8', errors='ignore').strip()
            error_output = stderr.decode('utf-8', errors='ignore').strip()

            # 尝试解析 JSON 输出
            try:
                parsed_output = json.loads(output)
                if parsed_output.get('status') in ['success', 'error']:
                    return parsed_output
                print(f"[PluginManager] Plugin '{plugin_name}' invalid JSON format: {output[:100]}")
            except json.JSONDecodeError:
                print(f"[PluginManager] Failed to parse JSON from '{plugin_name}': {output[:100]}")

            # 处理非 JSON 输出
            if process.returncode != 0:
                error_msg = f"Plugin '{plugin_name}' exited with code {process.returncode}"
                if output:
                    error_msg += f". Stdout: {output[:200]}"
                if error_output:
                    error_msg += f". Stderr: {error_output[:200]}"
                raise RuntimeError(error_msg)

            # 退出码为 0 但 JSON 解析失败
            return {
                'status': 'success',
                'result': output
            }

        except asyncio.TimeoutError:
            if 'process' in locals():
                process.kill()
            raise TimeoutError(f"Plugin '{plugin_name}' execution timed out")
        except Exception as e:
            raise RuntimeError(f"Failed to execute plugin '{plugin_name}': {e}")

    def initialize_services(self, app, project_base_path: str):
        """初始化服务插件"""
        if not app:
            print("[PluginManager] Cannot initialize services without app instance.")
            return

        print("[PluginManager] Initializing service plugins...")

        for name, service_data in self.service_modules.items():
            try:
                plugin_config = self._get_plugin_config(service_data['manifest'])
                debug_mode = plugin_config.get('DebugMode', 'N/A')
                print(f"[PluginManager] Registering routes for service plugin: {name}. "
                      f"DebugMode: {debug_mode}")

                service_data['module'].registerRoutes(app, plugin_config, project_base_path)

            except Exception as e:
                print(f"[PluginManager] Error initializing service plugin {name}: {e}")

        print("[PluginManager] Service plugins initialized.")

    async def shutdown_all_plugins(self):
        """关闭所有插件"""
        print("[PluginManager] Shutting down all plugins...")

        # 关闭消息预处理器
        for name, module in self.message_preprocessors.items():
            if hasattr(module, 'shutdown'):
                try:
                    print(f"[PluginManager] Calling shutdown for {name}...")
                    await module.shutdown()
                except Exception as e:
                    print(f"[PluginManager] Error during shutdown of plugin {name}: {e}")

        # 关闭服务模块
        for name, service_data in self.service_modules.items():
            module = service_data.get('module')
            if module and hasattr(module, 'shutdown'):
                try:
                    print(f"[PluginManager] Calling shutdown for service plugin {name}...")
                    await module.shutdown()
                except Exception as e:
                    print(f"[PluginManager] Error during shutdown of service plugin {name}: {e}")

        # 停止定时任务
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("[PluginManager] Scheduler stopped.")

        print("[PluginManager] All plugin shutdown processes initiated.")


# 全局单例
plugin_manager = PluginManager()
