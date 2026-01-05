import { useState } from 'react';
import { useChat } from '@/contexts/ChatContext';
import { useTheme } from '@/contexts/ThemeContext';

export default function AgentSettings() {
  const { currentAgent, setCurrentAgent } = useChat();
  const { theme } = useTheme();
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
      <div className="flex flex-col flex-1 overflow-y-auto overflow-x-hidden">
        <p className={`text-center py-5 ${theme === 'dark' ? 'text-gray-400' : 'text-slate-600'}`}>
          请先在"助手"标签页选择一个 Agent 以查看或修改其设置。
        </p>
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
    <div className="flex flex-col flex-1 overflow-y-auto overflow-x-hidden">
      <div className={`flex justify-between items-center mb-4 pb-2.5 ${
        theme === 'dark' ? 'border-b-gray-700' : 'border-b-slate-200'
      } border-b`}>
        <h3 className={`m-0 ${theme === 'dark' ? 'text-blue-400' : 'text-blue-500'}`}>
          助手设置: {currentAgent.name}
        </h3>
      </div>
      <form onSubmit={handleSave} className="w-full flex flex-col gap-3">
        <div className="flex flex-col gap-1.5">
          <label htmlFor="agentNameInput" className={`block text-sm font-medium ${
            theme === 'dark' ? 'text-gray-400' : 'text-slate-600'
          }`}>
            Agent 名称:
          </label>
          <input
            type="text"
            id="agentNameInput"
            value={settings.name}
            onChange={(e) => setSettings({ ...settings, name: e.target.value })}
            required
            className={`w-full px-2.5 py-2.5 rounded-lg border text-base outline-none focus:ring-2 ${
              theme === 'dark'
                ? 'bg-gray-900 border-gray-700 text-gray-200 focus:border-blue-600/75 focus:ring-blue-900/30'
                : 'bg-white border-slate-200 text-slate-700 focus:border-blue-500/70 focus:ring-blue-500/30'
            }`}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor="agentAvatarInput" className={`block text-sm font-medium ${
            theme === 'dark' ? 'text-gray-400' : 'text-slate-600'
          }`}>
            Agent 头像:
          </label>
          <input
            type="file"
            id="agentAvatarInput"
            accept="image/png, image/jpeg, image/gif"
            className={`w-full px-2.5 py-2.5 rounded-lg border text-base outline-none focus:ring-2 ${
              theme === 'dark'
                ? 'bg-gray-900 border-gray-700 text-gray-200 focus:border-blue-600/75 focus:ring-blue-900/30'
                : 'bg-white border-slate-200 text-slate-700 focus:border-blue-500/70 focus:ring-blue-500/30'
            }`}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor="agentSystemPrompt" className={`block text-sm font-medium ${
            theme === 'dark' ? 'text-gray-400' : 'text-slate-600'
          }`}>
            系统提示词:
          </label>
          <textarea
            id="agentSystemPrompt"
            rows={6}
            value={settings.systemPrompt}
            onChange={(e) => setSettings({ ...settings, systemPrompt: e.target.value })}
            className={`w-full px-2.5 py-2.5 rounded-lg border text-base outline-none focus:ring-2 resize-y min-h-20 ${
              theme === 'dark'
                ? 'bg-gray-900 border-gray-700 text-gray-200 focus:border-blue-600/75 focus:ring-blue-900/30'
                : 'bg-white border-slate-200 text-slate-700 focus:border-blue-500/70 focus:ring-blue-500/30'
            }`}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor="agentModel" className={`block text-sm font-medium ${
            theme === 'dark' ? 'text-gray-400' : 'text-slate-600'
          }`}>
            模型名称:
          </label>
          <input
            type="text"
            id="agentModel"
            value={settings.model}
            onChange={(e) => setSettings({ ...settings, model: e.target.value })}
            placeholder="例如 gpt-4"
            className={`w-full px-2.5 py-2.5 rounded-lg border text-base outline-none focus:ring-2 ${
              theme === 'dark'
                ? 'bg-gray-900 border-gray-700 text-gray-200 focus:border-blue-600/75 focus:ring-blue-900/30'
                : 'bg-white border-slate-200 text-slate-700 focus:border-blue-500/70 focus:ring-blue-500/30'
            }`}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor="agentTemperature" className={`block text-sm font-medium ${
            theme === 'dark' ? 'text-gray-400' : 'text-slate-600'
          }`}>
            Temperature (0-1):
          </label>
          <input
            type="number"
            id="agentTemperature"
            min={0}
            max={1}
            step={0.1}
            value={settings.temperature}
            onChange={(e) => setSettings({ ...settings, temperature: parseFloat(e.target.value) })}
            className={`w-full px-2.5 py-2.5 rounded-lg border text-base outline-none focus:ring-2 ${
              theme === 'dark'
                ? 'bg-gray-900 border-gray-700 text-gray-200 focus:border-blue-600/75 focus:ring-blue-900/30'
                : 'bg-white border-slate-200 text-slate-700 focus:border-blue-500/70 focus:ring-blue-500/30'
            }`}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor="agentMaxTokens" className={`block text-sm font-medium ${
            theme === 'dark' ? 'text-gray-400' : 'text-slate-600'
          }`}>
            最大输出 Token:
          </label>
          <input
            type="number"
            id="agentMaxTokens"
            min={0}
            step={100}
            value={settings.maxTokens}
            onChange={(e) => setSettings({ ...settings, maxTokens: parseInt(e.target.value) })}
            className={`w-full px-2.5 py-2.5 rounded-lg border text-base outline-none focus:ring-2 ${
              theme === 'dark'
                ? 'bg-gray-900 border-gray-700 text-gray-200 focus:border-blue-600/75 focus:ring-blue-900/30'
                : 'bg-white border-slate-200 text-slate-700 focus:border-blue-500/70 focus:ring-blue-500/30'
            }`}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className={`block text-sm font-medium ${
            theme === 'dark' ? 'text-gray-400' : 'text-slate-600'
          }`}>
            输出模式:
          </label>
          <label className={`flex items-center gap-3 ${theme === 'dark' ? 'text-gray-200' : 'text-slate-700'}`}>
            <input
              type="radio"
              name="streamOutput"
              value="true"
              defaultChecked
              className="sr-only peer"
            />
            <div className={`w-12 h-6 rounded-full transition-colors cursor-pointer relative ${
              theme === 'dark' ? 'bg-gray-300 peer-checked:bg-green-500' : 'bg-gray-300 peer-checked:bg-green-500'
            }`}>
              <div className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform peer-checked:translate-x-6`} />
            </div>
            <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-slate-600'}`}>
              流式
            </span>
          </label>
          <label className={`flex items-center gap-3 ${theme === 'dark' ? 'text-gray-200' : 'text-slate-700'}`}>
            <input
              type="radio"
              name="streamOutput"
              value="false"
              className="sr-only peer"
            />
            <div className={`w-12 h-6 rounded-full transition-colors cursor-pointer relative ${
              theme === 'dark' ? 'bg-gray-300 peer-checked:bg-green-500' : 'bg-gray-300 peer-checked:bg-green-500'
            }`}>
              <div className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform peer-checked:translate-x-6`} />
            </div>
            <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-slate-600'}`}>
              非流式
            </span>
          </label>
        </div>
        <div className="flex justify-start gap-2.5 mt-4">
          <button
            type="submit"
            className={`px-4 py-2.5 rounded-lg border-0 cursor-pointer text-base transition-colors mr-2.5 ${
              theme === 'dark'
                ? 'bg-blue-600/75 text-white hover:bg-gray-600'
                : 'bg-blue-500/70 text-white hover:bg-blue-600'
            }`}
          >
            保存
          </button>
          <button
            type="button"
            onClick={handleDelete}
            className={`px-4 py-2.5 rounded-lg border-0 cursor-pointer text-base transition-colors ${
              theme === 'dark'
                ? 'bg-red-400 text-white hover:bg-red-500'
                : 'bg-red-500 text-white hover:bg-red-600'
            }`}
          >
            删除
          </button>
        </div>
      </form>
    </div>
  );
}
