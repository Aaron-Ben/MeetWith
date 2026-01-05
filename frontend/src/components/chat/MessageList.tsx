import { useChat } from '@/contexts/ChatContext';
import { useTheme } from '@/contexts/ThemeContext';
import MessageItem from './MessageItem';

export default function MessageList() {
  const { messages } = useChat();
  const { theme } = useTheme();

  if (messages.length === 0) {
    return (
      <div className="px-5 py-4 flex flex-col gap-2.5">
        <div className={`text-center py-10 ${theme === 'dark' ? 'text-[#a0a0a0]' : 'text-[#5a6f80]'}`}>
          <p>开始一个新对话...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="px-5 py-4 flex flex-col gap-2.5">
      {messages.map(message => (
        <MessageItem key={message.id} message={message} />
      ))}
    </div>
  );
}
