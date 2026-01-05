import { useState, useRef } from 'react';
import { useChat } from '@/contexts/ChatContext';
import { useTheme } from '@/contexts/ThemeContext';
import { uploadAgentAvatar } from '@/api/agents';

export default function AgentSettings() {
  const { currentAgent, setCurrentAgent, reloadAgents } = useChat();
  const { theme } = useTheme();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [streamEnabled, setStreamEnabled] = useState(true);
  const [settings, setSettings] = useState(
    currentAgent || {
      name: '',
      systemPrompt: '',
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

  const handleAvatarClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !currentAgent) return;

    // 检查文件类型
    if (!file.type.startsWith('image/')) {
      alert('请选择图片文件');
      return;
    }

    try {
      setUploading(true);
      await uploadAgentAvatar(currentAgent.id, file);
      // 重新加载 Agent 列表以获取新的头像 URL
      await reloadAgents();
      alert('头像上传成功');
    } catch (error) {
      console.error('上传头像失败:', error);
      alert('头像上传失败，请重试');
    } finally {
      setUploading(false);
      // 清空文件选择器
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
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
            名称:
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
          <label className={`block text-sm font-medium ${
            theme === 'dark' ? 'text-gray-400' : 'text-slate-600'
          }`}>
            头像:
          </label>
          <div
            onClick={handleAvatarClick}
            className={`relative w-16 h-16 rounded-full border-2 cursor-pointer transition-opacity ${
              theme === 'dark' ? 'border-gray-600 hover:border-gray-500' : 'border-blue-500 hover:border-blue-400'
            } ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
            title={uploading ? '上传中...' : '点击更换头像'}
          >
            {currentAgent.avatarUrl ? (
              <img
                src={currentAgent.avatarUrl}
                alt={currentAgent.name}
                className="w-full h-full rounded-full object-cover"
              />
            ) : (
              <div className={`w-full h-full rounded-full flex items-center justify-center text-sm ${
                theme === 'dark' ? 'bg-gray-700 text-gray-400' : 'bg-gray-200 text-slate-500'
              }`}>
                {uploading ? '...' : '+'}
              </div>
            )}
            {!uploading && (
              <div className={`absolute inset-0 rounded-full flex items-center justify-center text-xs font-medium opacity-0 hover:opacity-100 transition-opacity ${
                theme === 'dark' ? 'bg-black/50 text-white' : 'bg-black/30 text-white'
              }`}>
                更换
              </div>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="hidden"
            disabled={uploading}
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
        <div className="flex items-center gap-2">
          <div
            onClick={() => setStreamEnabled(!streamEnabled)}
            className={`w-5 h-5 rounded-full cursor-pointer transition-all duration-200 flex items-center justify-center relative ${
              streamEnabled
                ? theme === 'dark' ? 'bg-green-600' : 'bg-green-500'
                : theme === 'dark' ? 'bg-gray-700' : 'bg-gray-300'
            }`}
            title={streamEnabled ? '流式输出（点击关闭）' : '非流式输出（点击开启）'}
          >
            {streamEnabled && (
              <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
              </svg>
            )}
          </div>
          <label className={`text-sm font-medium cursor-pointer ${
            theme === 'dark' ? 'text-gray-400' : 'text-slate-600'
          }`} onClick={() => setStreamEnabled(!streamEnabled)}>
            流式输出
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
