import { useState, useRef, useEffect } from 'react';
import { useChat } from '@/contexts/ChatContext';
import { useTheme } from '@/contexts/ThemeContext';
import { useChatStream } from '@/hooks/useChatStream';
import { ChatMessage } from '@/api/chat';
import MessageList from './MessageList';
import AttachmentPreview from './AttachmentPreview';

export default function ChatArea() {
  const { theme, toggleTheme } = useTheme();
  const {
    currentAgent,
    messages,
    addMessage,
    updateMessage,
    clearMessages,
    showNotificationSidebar,
    toggleNotificationSidebar
  } = useChat();
  const [inputText, setInputText] = useState('');
  const [attachments, setAttachments] = useState<Array<{ id: string; name: string; url: string; type: string }>>([]);
  const [assistantMessageId, setAssistantMessageId] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const accumulatedContentRef = useRef<string>('');
  const assistantMessageIdRef = useRef<string | null>(null);

  // 使用流式聊天 hook
  const { sendMessage, isLoading } = useChatStream({
    onChunk: (chunk: string) => {
      const currentAssistantId = assistantMessageIdRef.current;
      console.log('[ChatArea] onChunk called:', chunk, 'assistantMessageId:', currentAssistantId);
      if (currentAssistantId) {
        accumulatedContentRef.current += chunk;
        const newContent = accumulatedContentRef.current;
        console.log('[ChatArea] Updating message', currentAssistantId, 'with content length:', newContent.length);
        updateMessage(currentAssistantId, newContent);
      }
    },
    onComplete: (fullContent: string) => {
      const currentAssistantId = assistantMessageIdRef.current;
      console.log('[ChatArea] onComplete called with content length:', fullContent.length);
      if (currentAssistantId) {
        updateMessage(currentAssistantId, fullContent);
        accumulatedContentRef.current = '';
        assistantMessageIdRef.current = null;
      }
      setAssistantMessageId(null);
    },
    onError: (error: Error) => {
      const currentAssistantId = assistantMessageIdRef.current;
      console.error('[ChatArea] Chat error:', error);
      if (currentAssistantId) {
        updateMessage(currentAssistantId, `错误: ${error.message}`);
        accumulatedContentRef.current = '';
        assistantMessageIdRef.current = null;
      }
      setAssistantMessageId(null);
    },
  });

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

  const handleSend = async () => {
    if (!inputText.trim() && attachments.length === 0) return;
    if (!currentAgent) return;
    if (isLoading) return; // 防止重复发送

    // 添加用户消息
    const userMessage = {
      id: `msg_${Date.now()}`,
      role: 'user' as const,
      content: inputText,
      timestamp: Date.now(),
      attachments: attachments.length > 0 ? attachments : undefined,
    };

    addMessage(userMessage);
    const userInput = inputText;
    setInputText('');
    setAttachments([]);

    // 创建助手消息占位符
    const assistantId = `msg_${Date.now() + 1}`;
    setAssistantMessageId(assistantId);
    assistantMessageIdRef.current = assistantId; // 同步更新 ref
    accumulatedContentRef.current = ''; // 重置累积内容
    addMessage({
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
    });

    // 构建消息历史
    const chatMessages: ChatMessage[] = [
      { role: 'system', content: currentAgent.systemPrompt },
      ...messages.map(msg => ({
        role: msg.role,
        content: msg.content,
      })),
      { role: 'user', content: userInput },
    ];

    // 发送消息
    await sendMessage(chatMessages, currentAgent.model);
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
          title={isLoading ? "AI 正在回复..." : "发送消息 (Ctrl+Enter)"}
          disabled={!currentAgent || (!inputText.trim() && attachments.length === 0) || isLoading}
          className={`w-10 h-10 rounded-full flex justify-center items-center cursor-pointer transition-colors p-0 ml-2 ${
            theme === 'dark'
              ? 'bg-gray-700 text-gray-200 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed'
              : 'bg-blue-500 text-white hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed'
          }`}
        >
          {isLoading ? (
            <svg className="animate-spin" viewBox="0 0 24 24" fill="none" width="20" height="20">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20" className={theme === 'light' ? 'text-white' : ''}>
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
            </svg>
          )}
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
