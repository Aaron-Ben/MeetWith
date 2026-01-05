import { useState } from 'react';
import { useChat } from '@/contexts/ChatContext';

export default function AgentSettings() {
  const { currentAgent, setCurrentAgent } = useChat();
  const [settings, setSettings] = useState(
    currentAgent || {
      name: '',
      systemPrompt: '',
      model: '',
      temperature: 0.7,
      maxTokens: 4000,
    }
  );

  if (!currentAgent) {
    return (
      <div className="sidebar-tab-content active">
        <p className="select-agent-prompt">请先在"助手"标签页选择一个 Agent 以查看或修改其设置。</p>
      </div>
    );
  }

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Save settings
    console.log('Saving settings:', settings);
  };

  const handleDelete = () => {
    if (confirm(`确定要删除 Agent "${currentAgent.name}" 吗？`)) {
      // TODO: Delete agent
      setCurrentAgent(null);
    }
  };

  return (
    <div className="sidebar-tab-content active">
      <div className="settings-header-bar">
        <h3>助手设置: {currentAgent.name}</h3>
      </div>
      <form id="agentSettingsForm" onSubmit={handleSave}>
        <div>
          <label htmlFor="agentNameInput">Agent 名称:</label>
          <input
            type="text"
            id="agentNameInput"
            value={settings.name}
            onChange={(e) => setSettings({ ...settings, name: e.target.value })}
            required
          />
        </div>
        <div>
          <label htmlFor="agentAvatarInput">Agent 头像:</label>
          <input
            type="file"
            id="agentAvatarInput"
            accept="image/png, image/jpeg, image/gif"
          />
        </div>
        <div>
          <label htmlFor="agentSystemPrompt">系统提示词:</label>
          <textarea
            id="agentSystemPrompt"
            rows={6}
            value={settings.systemPrompt}
            onChange={(e) => setSettings({ ...settings, systemPrompt: e.target.value })}
          />
        </div>
        <div>
          <label htmlFor="agentModel">模型名称:</label>
          <input
            type="text"
            id="agentModel"
            value={settings.model}
            onChange={(e) => setSettings({ ...settings, model: e.target.value })}
            placeholder="例如 gpt-4"
          />
        </div>
        <div>
          <label htmlFor="agentTemperature">Temperature (0-1):</label>
          <input
            type="number"
            id="agentTemperature"
            min={0}
            max={1}
            step={0.1}
            value={settings.temperature}
            onChange={(e) => setSettings({ ...settings, temperature: parseFloat(e.target.value) })}
          />
        </div>
        <div>
          <label htmlFor="agentMaxTokens">最大输出 Token:</label>
          <input
            type="number"
            id="agentMaxTokens"
            min={0}
            step={100}
            value={settings.maxTokens}
            onChange={(e) => setSettings({ ...settings, maxTokens: parseInt(e.target.value) })}
          />
        </div>
        <div>
          <label>输出模式:</label>
          <label>
            <input
              type="radio"
              name="streamOutput"
              value="true"
              defaultChecked
            /> 流式
          </label>
          <label>
            <input
              type="radio"
              name="streamOutput"
              value="false"
            /> 非流式
          </label>
        </div>
        <div className="form-actions">
          <button type="submit">保存 Agent 设置</button>
          <button type="button" className="danger-button" onClick={handleDelete}>
            删除此 Agent
          </button>
        </div>
      </form>
    </div>
  );
}
