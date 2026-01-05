import { useChat } from '@/contexts/ChatContext';
import MessageItem from './MessageItem';

export default function MessageList() {
  const { messages } = useChat();

  if (messages.length === 0) {
    return (
      <div className="chat-messages">
        <div className="empty-state">
          <p>开始一个新对话...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-messages">
      {messages.map(message => (
        <MessageItem key={message.id} message={message} />
      ))}
    </div>
  );
}
