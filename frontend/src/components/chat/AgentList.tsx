import { useState } from 'react';
import { useChat } from '@/contexts/ChatContext';

export default function AgentList() {
  const { agents, currentAgent, setCurrentAgent } = useChat();
  const [showCreateModal, setShowCreateModal] = useState(false);

  return (
    <div className="sidebar-tab-content active">
      <h2>VCP Agents</h2>
      <ul className="agent-list">
        {agents.map(agent => (
          <li
            key={agent.id}
            className={currentAgent?.id === agent.id ? 'active' : ''}
            onClick={() => setCurrentAgent(agent)}
          >
            {agent.avatarUrl && (
              <img src={agent.avatarUrl} alt={agent.name} className="avatar" />
            )}
            <span className="agent-name">{agent.name}</span>
          </li>
        ))}
      </ul>
      <div className="sidebar-actions">
        <button
          className="sidebar-button create-agent-btn"
          onClick={() => setShowCreateModal(true)}
        >
          创建新 Agent
        </button>
      </div>

      {showCreateModal && (
        <div className="modal active">
          <div className="modal-content">
            <span
              className="close-button"
              onClick={() => setShowCreateModal(false)}
            >
              ×
            </span>
            <h2>创建新 Agent</h2>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                // TODO: Implement agent creation
                setShowCreateModal(false);
              }}
            >
              <div>
                <label htmlFor="newAgentName">Agent 名称:</label>
                <input
                  type="text"
                  id="newAgentName"
                  name="name"
                  required
                  placeholder="输入 Agent 名称"
                />
              </div>
              <div>
                <label htmlFor="newAgentModel">模型名称:</label>
                <input
                  type="text"
                  id="newAgentModel"
                  name="model"
                  placeholder="例如 gpt-4"
                />
              </div>
              <div>
                <label htmlFor="newAgentPrompt">系统提示词:</label>
                <textarea
                  id="newAgentPrompt"
                  name="systemPrompt"
                  rows={4}
                  placeholder="定义 Agent 的行为和性格..."
                />
              </div>
              <button type="submit">创建</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
