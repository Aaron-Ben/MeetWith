import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Message, Attachment, ToolCall } from '@/contexts/ChatContext';
import { useTheme } from '@/contexts/ThemeContext';

interface MessageItemProps {
  message: Message;
}

export default function MessageItem({ message }: MessageItemProps) {
  const { theme } = useTheme();
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(message.content);

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleSave = () => {
    // TODO: Implement save
    setIsEditing(false);
  };

  return (
    <div
      className={`message-item ${message.role} ${isEditing ? 'message-item-editing' : ''}`}
    >
      {!isEditing ? (
        <>
          <span className="sender-name">
            {message.role === 'user' ? '你' : 'AI'}
          </span>
          <div className="md-content">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>

          {message.attachments && message.attachments.length > 0 && (
            <div className="message-attachments">
              {message.attachments.map(attachment => (
                <div key={attachment.id} className="attachment-item">
                  {attachment.type.startsWith('image/') ? (
                    <img
                      src={attachment.url}
                      alt={attachment.name}
                      className="message-attachment-image-thumbnail"
                    />
                  ) : (
                    <div className="attachment-file">
                      <span>📄 {attachment.name}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {message.toolCalls && message.toolCalls.length > 0 && (
            <div className="vcp-tool-request-bubble">
              {message.toolCalls.map((tool, idx) => (
                <div key={idx}>
                  <strong>tool_name:</strong> {tool.toolName}
                  <br />
                  <strong>parameters:</strong>{' '}
                  <span className="vcp-param-value">
                    {JSON.stringify(tool.parameters, null, 2)}
                  </span>
                  {tool.result && (
                    <>
                      <br />
                      <strong>result:</strong>{' '}
                      <span className="vcp-param-value">
                        {tool.result.substring(0, 100)}...
                      </span>
                    </>
                  )}
                </div>
              ))}
            </div>
          )}

          <span className="message-timestamp">{formatDate(message.timestamp)}</span>

          <div className="message-controls">
            <button
              className="message-edit-btn"
              onClick={() => setIsEditing(true)}
              title="编辑消息"
            >
              ✏️
            </button>
          </div>
        </>
      ) : (
        <div className="message-edit-container">
          <textarea
            className="message-edit-textarea"
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
          />
          <div className="message-edit-controls">
            <button onClick={handleSave}>保存</button>
            <button onClick={() => setIsEditing(false)}>取消</button>
          </div>
        </div>
      )}
    </div>
  );
}
