import { useState, useRef, useEffect } from 'react';
import { useChat } from '@/contexts/ChatContext';
import { useTheme } from '@/contexts/ThemeContext';
import MessageList from './MessageList';
import AttachmentPreview from './AttachmentPreview';

export default function ChatArea() {
  const { theme, toggleTheme } = useTheme();
  const { currentAgent, messages, addMessage, clearMessages, showNotificationSidebar, toggleNotificationSidebar } = useChat();
  const [inputText, setInputText] = useState('');
  const [attachments, setAttachments] = useState<Array<{ id: string; name: string; url: string; type: string }>>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
    }
  }, [inputText]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    if (!inputText.trim() && attachments.length === 0) return;

    const newMessage = {
      id: `msg_${Date.now()}`,
      role: 'user' as const,
      content: inputText,
      timestamp: Date.now(),
      attachments: attachments.length > 0 ? attachments : undefined,
    };

    addMessage(newMessage);
    setInputText('');
    setAttachments([]);

    // TODO: Send to API and get response
  };

  const handleClearChat = () => {
    if (confirm('确定要清空当前对话记录吗？')) {
      clearMessages();
    }
  };

  return (
    <main className={`flex-1 flex flex-col bg-cover bg-center bg-no-repeat ${
      theme === 'dark' ? 'bg-gray-950' : 'bg-slate-100'
    }`} style={{
      backgroundImage: theme === 'dark' ? "url('/assets/dark.jpg')" : "url('/assets/light.jpeg')"
    }}>
      <header className={`px-5 py-3 flex justify-between items-center min-h-9 ${
        theme === 'dark' ? 'bg-gray-800 border-b-gray-700' : 'bg-white border-b-slate-200'
      } border-b`}>
        <h3 className={`m-0 text-xl font-medium ${
          theme === 'dark' ? 'text-blue-400' : 'text-blue-500'
        }`}>
          {currentAgent?.name || '选择一个 Agent 开始聊天'}
        </h3>
        <div className="flex items-center">
          <button
            className={`bg-transparent border px-2.5 h-8 rounded-lg cursor-pointer ml-2 text-sm inline-flex items-center justify-center transition-all ${
              theme === 'dark'
                ? 'border-gray-600 text-gray-400 hover:bg-gray-600 hover:text-gray-200'
                : 'border-blue-500 text-blue-500 hover:bg-blue-600 hover:text-white'
            }`}
            onClick={toggleTheme}
            title={theme === 'dark' ? '切换到亮色模式' : '切换到暗色模式'}
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
          <button
            className={`bg-transparent border px-2.5 h-8 rounded-lg cursor-pointer ml-2 text-sm inline-flex items-center justify-center transition-all ${
              theme === 'dark'
                ? 'border-gray-600 text-gray-400 hover:bg-gray-600 hover:text-gray-200'
                : 'border-blue-500 text-blue-500 hover:bg-blue-600 hover:text-white'
            }`}
            onClick={toggleNotificationSidebar}
            title={showNotificationSidebar ? '隐藏通知栏' : '显示通知栏'}
          >
            🔔
          </button>
          <button
            className={`bg-transparent border px-2.5 h-8 rounded-lg cursor-pointer ml-2 text-sm inline-flex items-center justify-center transition-all ${
              theme === 'dark'
                ? 'border-gray-600 text-gray-400 hover:bg-gray-600 hover:text-gray-200'
                : 'border-blue-500 text-blue-500 hover:bg-blue-600 hover:text-white'
            }`}
            onClick={handleClearChat}
            title="清空当前聊天记录"
          >
            🗑️ 清空对话
          </button>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto flex flex-col">
        <MessageList />
        <div ref={messagesEndRef} />
      </div>

      <footer className={`px-4 py-3 py-3 flex items-end flex-wrap ${
        theme === 'dark' ? 'bg-gray-800 border-t-gray-700' : 'bg-white border-t-slate-200'
      } border-t`}>
        <AttachmentPreview
          attachments={attachments}
          onRemove={(id) => setAttachments(prev => prev.filter(a => a.id !== id))}
        />
        <textarea
          ref={textareaRef}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入消息... (Shift+Enter 换行, Ctrl+Enter 发送)"
          disabled={!currentAgent}
          rows={1}
          className={`flex-1 px-3 py-2 rounded-20 border text-base resize-none mr-2.5 max-h-[150px] overflow-y-auto leading-[1.4] font-sans outline-none focus:ring-2 ${
            theme === 'dark'
              ? 'bg-gray-900 border-gray-700 text-gray-200 focus:border-blue-600/75 focus:ring-blue-900/30'
              : 'bg-white border-slate-200 text-slate-700 focus:border-blue-500/70 focus:ring-blue-500/30'
          }`}
          style={{ borderRadius: '20px' }}
        />
        <button
          onClick={handleSend}
          title="发送消息 (Ctrl+Enter)"
          disabled={!currentAgent || (!inputText.trim() && attachments.length === 0)}
          className={`w-10 h-10 rounded-full flex justify-center items-center cursor-pointer transition-colors p-0 ml-2 ${
            theme === 'dark'
              ? 'bg-gray-700 text-gray-200 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed'
              : 'bg-blue-500 text-white hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed'
          }`}
        >
          <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20" className={theme === 'light' ? 'text-white' : ''}>
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
          </svg>
        </button>
        <button
          title="发送文件"
          disabled={!currentAgent}
          className={`w-10 h-10 rounded-full flex justify-center items-center cursor-pointer transition-colors p-0 ml-2 ${
            theme === 'dark'
              ? 'bg-gray-700 text-gray-200 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed'
              : 'bg-blue-500 text-white hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed'
          }`}
        >
          <svg fill="currentColor" viewBox="0 0 24 24" width="20" height="20" className={theme === 'light' ? 'text-white' : ''}>
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="m18.375 12.739-7.693 7.693a4.5 4.5 0 0 1-6.364-6.364l10.94-10.94A3 3 0 1 1 19.5 7.372L8.552 18.32m.009-.01-.01.01m5.699-9.941-7.81 7.81a1.5 1.5 0 0 0 2.112 2.13"
            />
          </svg>
        </button>
      </footer>
    </main>
  );
}
