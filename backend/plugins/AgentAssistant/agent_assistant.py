#!/usr/bin/env python3
"""
AgentAssistant Plugin
Manages multiple AI agents with session history and OpenAI API integration
"""

import os
import sys
import json
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: 'requests' library is required. Install it with: pip install requests", file=sys.stderr)
    sys.exit(1)


# ==================== Configuration ====================

def load_env_config() -> Dict[str, str]:
    """Load configuration from config.env files"""
    env_config = {}

    # Possible config file locations
    plugin_config_path = Path(__file__).parent / 'config.env'
    root_config_path = Path(__file__).parent.parent.parent / 'config.env'

    # Load plugin config first
    if plugin_config_path.exists():
        try:
            with open(plugin_config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_config[key.strip()] = value.strip()
        except Exception as e:
            print(f"[AgentAssistant] Error parsing plugin config.env ({plugin_config_path}): {e}", file=sys.stderr)

    # Load root config (only for keys not already defined)
    if root_config_path.exists():
        try:
            with open(root_config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        if key not in env_config:
                            env_config[key] = value.strip()
        except Exception as e:
            print(f"[AgentAssistant] Error parsing root config.env ({root_config_path}): {e}", file=sys.stderr)

    # Override with environment variables
    for key, value in os.environ.items():
        if key.startswith('AGENT_') or key in ['API_URL', 'API_KEY', 'DebugMode',
                                                  'AGENT_ASSISTANT_MAX_HISTORY_ROUNDS',
                                                  'AGENT_ASSISTANT_CONTEXT_TTL_HOURS',
                                                  'PLUGIN_COMMUNICATION_TIMEOUT']:
            env_config[key] = value

    return env_config


# Load configuration
ENV_CONFIG = load_env_config()

API_URL = os.getenv('API_URL') or ENV_CONFIG.get('API_URL')
API_KEY = os.getenv('API_KEY') or ENV_CONFIG.get('API_KEY')
MAX_HISTORY_ROUNDS = int(os.getenv('AGENT_ASSISTANT_MAX_HISTORY_ROUNDS') or
                         ENV_CONFIG.get('AGENT_ASSISTANT_MAX_HISTORY_ROUNDS', '7'))
CONTEXT_TTL_HOURS = int(os.getenv('AGENT_ASSISTANT_CONTEXT_TTL_HOURS') or
                        ENV_CONFIG.get('AGENT_ASSISTANT_CONTEXT_TTL_HOURS', '24'))
DEBUG_MODE = (os.getenv('DebugMode') or ENV_CONFIG.get('DebugMode', 'False')).lower() == 'true'
TIMEOUT = int(os.getenv('PLUGIN_COMMUNICATION_TIMEOUT') or '118000')


# ==================== Agent Loading ====================

class AgentConfig:
    """Agent configuration class"""
    def __init__(self, model_id: str, name: str, base_name: str,
                 system_prompt: str, max_output_tokens: int,
                 temperature: float, description: str):
        self.id = model_id
        self.name = name
        self.base_name = base_name
        self.system_prompt = system_prompt
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'base_name': self.base_name,
            'systemPrompt': self.system_prompt,
            'maxOutputTokens': self.max_output_tokens,
            'temperature': self.temperature,
            'description': self.description
        }


def load_agents() -> Dict[str, AgentConfig]:
    """Load agents from configuration"""
    agents = {}
    agent_base_names = set()

    # First pass: Identify all unique agent base names
    for key in ENV_CONFIG.keys():
        if key.startswith('AGENT_') and key.endswith('_MODEL_ID'):
            match = re.match(r'^AGENT_([A-Z0-9_]+)_MODEL_ID$', key, re.IGNORECASE)
            if match and match.group(1):
                agent_base_names.add(match.group(1).upper())

    if DEBUG_MODE:
        print(f"[AgentAssistant] Identified agent base names from config: {', '.join(agent_base_names) or 'None'}", file=sys.stderr)

    # Second pass: Load full agent configuration
    for base_name in agent_base_names:
        model_id = ENV_CONFIG.get(f'AGENT_{base_name}_MODEL_ID')
        chinese_name = ENV_CONFIG.get(f'AGENT_{base_name}_CHINESE_NAME')

        if not model_id:
            if DEBUG_MODE:
                print(f"[AgentAssistant] Skipping {base_name}: Missing AGENT_{base_name}_MODEL_ID.", file=sys.stderr)
            continue

        if not chinese_name:
            if DEBUG_MODE:
                print(f"[AgentAssistant] Skipping {base_name}: Missing AGENT_{base_name}_CHINESE_NAME.", file=sys.stderr)
            continue

        # Process system prompt template
        system_prompt_template = ENV_CONFIG.get(f'AGENT_{base_name}_SYSTEM_PROMPT',
                                                  f'You are a helpful AI assistant named {{MaidName}}.')
        final_system_prompt = system_prompt_template.replace('{{MaidName}}', chinese_name)

        max_output_tokens = int(ENV_CONFIG.get(f'AGENT_{base_name}_MAX_OUTPUT_TOKENS', '40000'))
        temperature = float(ENV_CONFIG.get(f'AGENT_{base_name}_TEMPERATURE', '0.7'))
        description = ENV_CONFIG.get(f'AGENT_{base_name}_DESCRIPTION',
                                      f'Assistant {chinese_name}.')

        # Use Chinese name as the key for invocation
        agents[chinese_name] = AgentConfig(
            model_id=model_id,
            name=chinese_name,
            base_name=base_name,
            system_prompt=final_system_prompt,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            description=description
        )

        if DEBUG_MODE:
            print(f"[AgentAssistant] Loaded agent: '{chinese_name}' (Base: {base_name}, ModelID: {model_id})", file=sys.stderr)

    if not agents and DEBUG_MODE:
        print("[AgentAssistant] Warning: No agents were loaded. Please check config.env.", file=sys.stderr)

    return agents


# Load agents at startup
AGENTS = load_agents()


# ==================== Session Management ====================

class SessionData:
    """Session data container"""
    def __init__(self):
        self.timestamp = time.time()
        self.history: List[Dict[str, str]] = []


class AgentContextManager:
    """Manages agent session contexts with TTL"""
    def __init__(self):
        self.contexts: Dict[str, Dict[str, SessionData]] = {}

    def get_session_history(self, agent_name: str, session_id: str = 'default_user_session') -> List[Dict[str, str]]:
        """Get session history for an agent"""
        if agent_name not in self.contexts:
            self.contexts[agent_name] = {}

        sessions = self.contexts[agent_name]

        if session_id not in sessions or self._is_expired(sessions[session_id].timestamp):
            sessions[session_id] = SessionData()

        return sessions[session_id].history

    def update_session_history(self, agent_name: str, user_message: Dict[str, str],
                               assistant_message: Dict[str, str], session_id: str = 'default_user_session'):
        """Update session history for an agent"""
        if agent_name not in self.contexts:
            self.contexts[agent_name] = {}

        sessions = self.contexts[agent_name]

        if session_id not in sessions or self._is_expired(sessions[session_id].timestamp):
            session_data = SessionData()
            session_data.history = [user_message, assistant_message]
            sessions[session_id] = session_data
        else:
            session_data = sessions[session_id]
            session_data.history.extend([user_message, assistant_message])
            session_data.timestamp = time.time()

            # Limit history size
            max_messages = MAX_HISTORY_ROUNDS * 2
            if len(session_data.history) > max_messages:
                session_data.history = session_data.history[-max_messages:]

    def _is_expired(self, timestamp: float) -> bool:
        """Check if context has expired"""
        return (time.time() - timestamp) > (CONTEXT_TTL_HOURS * 3600)

    def cleanup_expired(self):
        """Clean up expired sessions"""
        for agent_name in list(self.contexts.keys()):
            sessions = self.contexts[agent_name]
            for session_id in list(sessions.keys()):
                if self._is_expired(sessions[session_id].timestamp):
                    if DEBUG_MODE:
                        print(f"[AgentAssistant] Cleared expired context for agent {agent_name}, session {session_id}", file=sys.stderr)
                    del sessions[session_id]

            if not sessions:
                del self.contexts[agent_name]


# Global context manager
context_manager = AgentContextManager()


# ==================== Placeholder Replacement ====================

def replace_placeholders(text: Any, agent_config: Optional[AgentConfig] = None) -> str:
    """Replace placeholders in text"""
    if text is None:
        return ''

    processed_text = str(text)
    now = datetime.now()

    # Date/Time placeholders
    processed_text = re.sub(r'\{\{Date\}\}', now.strftime('%Y年%m月%d日'), processed_text)
    processed_text = re.sub(r'\{\{Time\}\}', now.strftime('%H:%M:%S'), processed_text)
    processed_text = re.sub(r'\{\{Today\}\}', now.strftime('%A'), processed_text)

    # Agent name placeholders
    if agent_config and agent_config.name:
        processed_text = re.sub(r'\{\{AgentName\}\}', agent_config.name, processed_text)
        processed_text = re.sub(r'\{\{MaidName\}\}', agent_config.name, processed_text)

    # {{VarHome}}, {{公共日记本}}, {{小X日记本}} are expected to be replaced by VCP server
    return processed_text


# ==================== Request Handler ====================

def handle_request(input_data: str) -> Dict[str, Any]:
    """Handle incoming request"""
    if not API_URL or not API_KEY:
        return {
            'status': 'error',
            'error': 'AgentAssistant plugin is not configured with API_URL or API_KEY.'
        }

    try:
        request_data = json.loads(input_data)
    except json.JSONDecodeError:
        return {'status': 'error', 'error': 'Invalid JSON input to AgentAssistant.'}

    agent_name = request_data.get('agent_name')
    prompt = request_data.get('prompt')

    if not agent_name or not prompt:
        return {'status': 'error', 'error': "Missing 'agent_name' or 'prompt' in request."}

    # Lookup agent by Chinese name
    agent_config = AGENTS.get(agent_name)

    if not agent_config:
        available_names = list(AGENTS.keys())
        error_msg = f"请求的 Agent '{agent_name}' 未找到或未正确配置。"

        if available_names:
            error_msg += f" 当前已成功加载的 Agent 有: {', '.join(available_names)}。"
        else:
            error_msg += ' 系统当前没有加载任何 Agent。请检查 AgentAssistant 的 config.env 配置文件。'

        error_msg += " 请确认您请求的 Agent 名称是否准确。"

        if DEBUG_MODE:
            print(f"[AgentAssistant] Failed to find agent: '{agent_name}'. Loaded agents: {', '.join(available_names) or '无'}", file=sys.stderr)

        return {'status': 'error', 'error': error_msg}

    user_session_id = request_data.get('session_id', f"agent_{agent_config.base_name}_default_user_session")

    try:
        # Process placeholders in user prompt
        processed_prompt = replace_placeholders(prompt, agent_config)

        # Get session history
        history = context_manager.get_session_history(agent_name, user_session_id)

        # Build messages
        messages = [
            {'role': 'system', 'content': agent_config.system_prompt},
            *history,
            {'role': 'user', 'content': processed_prompt}
        ]

        payload = {
            'model': agent_config.id,
            'messages': messages,
            'max_tokens': agent_config.max_output_tokens,
            'temperature': agent_config.temperature,
            'stream': False
        }

        if DEBUG_MODE:
            print(f"[AgentAssistant] Sending request to API for agent {agent_name} (Base: {agent_config.base_name}):", file=sys.stderr)
            print(f"[AgentAssistant] Payload (model: {payload['model']}, temp: {payload['temperature']}, max_tokens: {payload['max_tokens']}):", file=sys.stderr)
            for msg in messages:
                content_preview = (msg.get('content', '') or '')[:100]
                print(f"  {msg['role']}: {content_preview}...", file=sys.stderr)

        # Make API request
        response = requests.post(
            f'{API_URL}/v1/chat/completions',
            json=payload,
            headers={
                'Authorization': f'Bearer {API_KEY}',
                'Content-Type': 'application/json'
            },
            timeout=TIMEOUT / 1000  # Convert to seconds
        )

        if DEBUG_MODE:
            print(f"[AgentAssistant] Received API response for agent {agent_name}. Status: {response.status_code}", file=sys.stderr)

        response_data = response.json()

        # Extract assistant response
        assistant_content = response_data.get('choices', [{}])[0].get('message', {}).get('content')

        if not isinstance(assistant_content, str):
            if DEBUG_MODE:
                print(f"[AgentAssistant] API response did not contain valid assistant content for agent {agent_name}", file=sys.stderr)
            return {'status': 'error', 'error': f"Agent '{agent_name}' 的 API 响应无效或缺失内容。"}

        # Update session history
        context_manager.update_session_history(
            agent_name,
            {'role': 'user', 'content': processed_prompt},
            {'role': 'assistant', 'content': assistant_content},
            user_session_id
        )

        return {'status': 'success', 'result': assistant_content}

    except requests.Timeout:
        error_msg = f"调用 Agent '{agent_name}' (Base: {agent_config.base_name}) 时发生错误。"
        error_msg += f" 请求超时 (超过 {TIMEOUT/1000}s)。"
        if DEBUG_MODE:
            print(f"[AgentAssistant] Timeout for agent {agent_name}", file=sys.stderr)
        return {'status': 'error', 'error': error_msg}

    except requests.RequestException as e:
        error_msg = f"调用 Agent '{agent_name}' (Base: {agent_config.base_name}) 时发生错误。"

        if hasattr(e, 'response') and e.response is not None:
            error_msg += f" API 状态: {e.response.status_code}."
            try:
                response_data = e.response.json()
                if 'error' in response_data and 'message' in response_data['error']:
                    error_msg += f" 错误信息: {response_data['error']['message']}"
                else:
                    error_msg += f" 返回数据: {str(e.response.text)[:150]}"
            except:
                error_msg += f" 返回数据: {str(e.response.text)[:150]}"
        else:
            error_msg += f" {str(e)}"

        if DEBUG_MODE:
            print(f"[AgentAssistant] Error handling request for agent {agent_name}: {e}", file=sys.stderr)

        return {'status': 'error', 'error': error_msg}

    except Exception as e:
        error_msg = f"调用 Agent '{agent_name}' (Base: {agent_config.base_name}) 时发生错误。 {str(e)}"
        if DEBUG_MODE:
            print(f"[AgentAssistant] Unexpected error for agent {agent_name}: {e}", file=sys.stderr)
        return {'status': 'error', 'error': error_msg}


# ==================== Main Entry Point ====================

def main():
    """Main entry point"""
    # Log startup
    if DEBUG_MODE:
        print(f"[AgentAssistant] Plugin started. API_URL: {'Configured' if API_URL else 'NOT CONFIGURED'}, API_KEY: {'Configured' if API_KEY else 'NOT CONFIGURED'}", file=sys.stderr)
        print(f"[AgentAssistant] MAX_HISTORY_ROUNDS: {MAX_HISTORY_ROUNDS}, CONTEXT_TTL_HOURS: {CONTEXT_TTL_HOURS}", file=sys.stderr)
        print(f"[AgentAssistant] Attempting to load agents using AGENT_BASENAME_MODEL_ID and AGENT_BASENAME_CHINESE_NAME from config.env.", file=sys.stderr)

        loaded_names = list(AGENTS.keys())
        if loaded_names:
            print(f"[AgentAssistant] Successfully loaded agents (callable by Chinese Name): {', '.join(loaded_names)}", file=sys.stderr)
        else:
            print(f"[AgentAssistant] Warning: No agents were loaded.", file=sys.stderr)

    # Read input from stdin
    input_data = sys.stdin.read()

    if not input_data.strip():
        result = {'status': 'error', 'error': 'AgentAssistant 未收到任何输入。'}
    else:
        # Cleanup expired contexts before processing
        context_manager.cleanup_expired()
        result = handle_request(input_data.strip())

    # Write output to stdout
    print(json.dumps(result, ensure_ascii=False))

    sys.exit(0)


if __name__ == '__main__':
    main()
