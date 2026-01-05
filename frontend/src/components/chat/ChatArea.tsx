import { useState, useRef, useEffect } from 'react';
import { useChat } from '@/contexts/ChatContext';
import { useTheme } from '@/contexts/ThemeContext';
import MessageList from './MessageList';
import AttachmentPreview from './AttachmentPreview';

export default function ChatArea() {
  const { theme, toggleTheme } = useTheme();
  const { currentAgent, messages, addMessage, clearMessages } = useChat();
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
    <main className={`main-content main-content-${theme}`}>
      <header className="chat-header">
        <h3>{currentAgent?.name || '选择一个 Agent 开始聊天'}</h3>
        <div className="chat-actions">
          <button
            className="header-button"
            onClick={toggleTheme}
            title={theme === 'dark' ? '切换到亮色模式' : '切换到暗色模式'}
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
          <button
            className="header-button"
            onClick={handleClearChat}
            title="清空当前聊天记录"
          >
            🗑️ 清空对话
          </button>
        </div>
      </header>

      <div className="chat-messages-container">
        <MessageList />
        <div ref={messagesEndRef} />
      </div>

      <footer className="chat-input-area">
        <AttachmentPreview
          attachments={attachments}
          onRemove={(id) => setAttachments(prev => prev.filter(a => a.id !== id))}
        />
        <textarea
          ref={textareaRef}
          id="messageInput"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入消息... (Shift+Enter 换行, Ctrl+Enter 发送)"
          disabled={!currentAgent}
          rows={1}
        />
        <button
          id="sendMessageBtn"
          onClick={handleSend}
          title="发送消息 (Ctrl+Enter)"
          disabled={!currentAgent || (!inputText.trim() && attachments.length === 0)}
        >
          <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
          </svg>
        </button>
        <button
          id="attachFileBtn"
          title="发送文件"
          disabled={!currentAgent}
        >
          <svg fill="currentColor" viewBox="0 0 24 24" width="20" height="20">
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
