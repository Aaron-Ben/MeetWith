import { useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { useChat } from '@/contexts/ChatContext';
import { useTheme } from '@/contexts/ThemeContext';

export default function AgentList() {
  const { agents, currentAgent, setCurrentAgent, loadingAgents, reloadAgents } = useChat();
  const { theme } = useTheme();
  const [showCreateModal, setShowCreateModal] = useState(false);

  return (
    <div className="flex flex-col flex-1 overflow-y-auto overflow-x-hidden">
      <div className={`flex justify-between items-center mb-4 pb-2.5 ${
        theme === 'dark' ? 'border-b-gray-700' : 'border-b-slate-200'
      } border-b`}>
        <h2 className={`text-xl mt-1 m-0 ${
          theme === 'dark' ? 'text-gray-400' : 'text-slate-600'
        }`}>
          Agents
        </h2>
        <button
          onClick={reloadAgents}
          className={`p-1.5 rounded-lg transition-all duration-200 ${
            loadingAgents
              ? 'opacity-50 cursor-not-allowed'
              : theme === 'dark'
                ? 'hover:bg-gray-700 text-gray-400 hover:text-gray-200'
                : 'hover:bg-slate-200 text-slate-500 hover:text-slate-700'
          }`}
          title="刷新 Agent 列表"
          disabled={loadingAgents}
        >
          <RefreshCw className={`w-4 h-4 ${loadingAgents ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {loadingAgents ? (
        <div className="flex flex-col items-center justify-center flex-1 py-8">
          <div className={`animate-spin w-8 h-8 border-4 rounded-full ${
            theme === 'dark' ? 'border-gray-700 border-t-blue-400' : 'border-gray-200 border-t-blue-600'
          }`} />
          <p className={`text-sm mt-3 ${theme === 'dark' ? 'text-gray-400' : 'text-slate-600'}`}>
            加载角色...
          </p>
        </div>
      ) : agents.length === 0 ? (
        <div className="flex flex-col items-center justify-center flex-1 py-8">
          <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-slate-600'}`}>
            暂无角色，请在后端创建
          </p>
        </div>
      ) : (
        <ul className="list-none m-0 p-0 overflow-y-auto flex-1">
          {agents.map(agent => (
            <li
              key={agent.id}
              className={`px-3 py-2.5 mb-1.5 rounded-lg cursor-pointer flex items-center transition-all duration-200 ${
                currentAgent?.id === agent.id
                  ? theme === 'dark'
                    ? 'bg-blue-600/75 text-white font-medium'
                    : 'bg-blue-500/70 text-white font-medium'
                  : theme === 'dark'
                    ? 'hover:bg-gray-700 hover:translate-x-0.5'
                    : 'hover:bg-slate-200 hover:translate-x-0.5'
              }`}
              onClick={() => setCurrentAgent(agent)}
            >
              {agent.avatarUrl && (
                <img
                  src={agent.avatarUrl}
                  alt={agent.name}
                  className={`w-9 h-9 rounded-full mr-2.5 object-cover border-2 ${
                    theme === 'dark' ? 'border-gray-600' : 'border-blue-500'
                  }`}
                />
              )}
              <span className={`font-normal text-base flex-1 whitespace-nowrap overflow-hidden text-ellipsis ${
                theme === 'dark' ? 'text-gray-200' : 'text-slate-700'
              }`}>
                {agent.name}
              </span>
            </li>
          ))}
        </ul>
      )}

      <div className="mt-auto pt-2.5 border-t flex flex-col gap-2">
        <button
          className={`w-full py-2.5 rounded-lg cursor-pointer text-base text-center transition-colors ${
            theme === 'dark'
              ? 'bg-gray-700 text-gray-200 hover:bg-gray-600'
              : 'bg-blue-500 text-white border border-blue-500 hover:bg-blue-600'
          }`}
          onClick={() => setShowCreateModal(true)}
        >
          创建新 Agent
        </button>
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/60">
          <div className={`mx-auto p-6 rounded-xl border shadow-lg relative w-[90%] max-w-[550px] ${
            theme === 'dark'
              ? 'bg-gray-800 border-gray-700 text-gray-200'
              : 'bg-white border-slate-200 text-slate-700'
          }`}>
            <span
              className="absolute top-0 right-2 text-2xl font-bold cursor-pointer text-gray-400 hover:text-blue-500"
              onClick={() => setShowCreateModal(false)}
            >
              ×
            </span>
            <h2 className={`mt-0 mb-5 pb-2.5 border-b ${
              theme === 'dark' ? 'text-blue-400 border-gray-700' : 'text-blue-500 border-slate-200'
            }`}>
              创建新 Agent
            </h2>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                // TODO: Implement agent creation via API
                setShowCreateModal(false);
              }}
              className="w-full flex flex-col gap-3"
            >
              <div className="flex flex-col gap-1.5">
                <label htmlFor="newAgentName" className={`block text-sm font-medium ${
                  theme === 'dark' ? 'text-gray-400' : 'text-slate-600'
                }`}>
                  名称:
                </label>
                <input
                  type="text"
                  id="newAgentName"
                  name="name"
                  required
                  placeholder="输入名称"
                  className={`w-full px-2.5 py-2.5 rounded-lg border text-base outline-none focus:ring-2 ${
                    theme === 'dark'
                      ? 'bg-gray-900 border-gray-700 text-gray-200 focus:border-blue-600/75 focus:ring-blue-900/30'
                      : 'bg-white border-slate-200 text-slate-700 focus:border-blue-500/70 focus:ring-blue-500/30'
                  }`}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label htmlFor="newAgentModel" className={`block text-sm font-medium ${
                  theme === 'dark' ? 'text-gray-400' : 'text-slate-600'
                }`}>
                  模型名称:
                </label>
                <input
                  type="text"
                  id="newAgentModel"
                  name="model"
                  placeholder="例如 gpt-4"
                  className={`w-full px-2.5 py-2.5 rounded-lg border text-base outline-none focus:ring-2 ${
                    theme === 'dark'
                      ? 'bg-gray-900 border-gray-700 text-gray-200 focus:border-blue-600/75 focus:ring-blue-900/30'
                      : 'bg-white border-slate-200 text-slate-700 focus:border-blue-500/70 focus:ring-blue-500/30'
                  }`}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label htmlFor="newAgentPrompt" className={`block text-sm font-medium ${
                  theme === 'dark' ? 'text-gray-400' : 'text-slate-600'
                }`}>
                  系统提示词:
                </label>
                <textarea
                  id="newAgentPrompt"
                  name="systemPrompt"
                  rows={4}
                  placeholder="定义 Agent 的行为和性格..."
                  className={`w-full px-2.5 py-2.5 rounded-lg border text-base outline-none focus:ring-2 resize-y min-h-20 ${
                    theme === 'dark'
                      ? 'bg-gray-900 border-gray-700 text-gray-200 focus:border-blue-600/75 focus:ring-blue-900/30'
                      : 'bg-white border-slate-200 text-slate-700 focus:border-blue-500/70 focus:ring-blue-500/30'
                  }`}
                />
              </div>
              <button
                type="submit"
                className={`px-4 py-2.5 rounded-lg border-0 cursor-pointer text-base transition-colors mr-2.5 ${
                  theme === 'dark'
                    ? 'bg-blue-600/75 text-white hover:bg-gray-600'
                    : 'bg-blue-500/70 text-white hover:bg-blue-600'
                }`}
              >
                创建
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
