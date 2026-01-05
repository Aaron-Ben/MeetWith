import { useState } from 'react';
import { Message } from '@/contexts/ChatContext';
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
      className={`px-3 py-2 rounded-2.5 max-w-[60%] break-words leading-relaxed shadow-sm relative backdrop-blur-md ${
        message.role === 'user'
          ? theme === 'dark'
            ? 'bg-blue-600/75 text-gray-200 ml-auto rounded-br-sm'
            : 'bg-blue-500/70 text-white ml-auto rounded-br-sm'
          : theme === 'dark'
            ? 'bg-gray-800/75 text-gray-200 mr-auto max-w-[75%] rounded-bl-sm'
            : 'bg-sky-50/70 text-slate-700 mr-auto max-w-[75%] rounded-bl-sm border border-slate-300'
      } ${isEditing ? '!max-w-[95%]' : ''}`}
    >
      {!isEditing ? (
        <>
          <span className={`font-medium mb-0.75 text-xs opacity-80 block ${
            theme === 'dark' ? 'text-gray-400' : 'text-slate-600'
          }`}>
            {message.role === 'user' ? '你' : 'AI'}
          </span>
          <div className="color-inherit">
            <div className="m-0 mb-2">
              {message.content.split('\n').map((line, i) => (
                <p key={i} className="m-0 mb-2 last:mb-0">{line}</p>
              ))}
            </div>
          </div>

          {message.attachments && message.attachments.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {message.attachments.map(attachment => (
                <div key={attachment.id}>
                  {attachment.type.startsWith('image/') ? (
                    <img
                      src={attachment.url}
                      alt={attachment.name}
                      className={`max-w-[150px] max-h-[150px] rounded-lg cursor-pointer object-cover border-2 transition-transform hover:scale-105 ${
                        theme === 'dark' ? 'border-gray-600' : 'border-blue-500'
                      }`}
                    />
                  ) : (
                    <div className={`px-3 py-2 rounded-lg text-sm ${
                      theme === 'dark' ? 'bg-gray-700 text-gray-200' : 'bg-slate-200 text-slate-700'
                    }`}>
                      <span>📄 {attachment.name}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {message.toolCalls && message.toolCalls.length > 0 && (
            <div className={`rounded-lg px-4 py-2.5 mt-2.5 font-mono text-sm whitespace-pre-wrap ${
              theme === 'dark' ? 'bg-gray-700 border border-gray-600 text-gray-300' : 'bg-slate-200 border border-slate-300 text-slate-700'
            }`}>
              {message.toolCalls.map((tool, idx) => (
                <div key={idx}>
                  <strong className={theme === 'dark' ? 'text-blue-300' : 'text-blue-500'}>tool_name:</strong> {tool.toolName}
                  <br />
                  <strong className={theme === 'dark' ? 'text-blue-300' : 'text-blue-500'}>parameters:</strong>{' '}
                  <span className={theme === 'dark' ? 'text-lime-500' : 'text-green-600'}>
                    {JSON.stringify(tool.parameters, null, 2)}
                  </span>
                  {tool.result && (
                    <>
                      <br />
                      <strong className={theme === 'dark' ? 'text-blue-300' : 'text-blue-500'}>result:</strong>{' '}
                      <span className={theme === 'dark' ? 'text-lime-500' : 'text-green-600'}>
                        {tool.result.substring(0, 100)}...
                      </span>
                    </>
                  )}
                </div>
              ))}
            </div>
          )}

          <span className={`text-xs opacity-70 block text-right mt-1.25 ${
            theme === 'dark' ? 'text-gray-400' : 'text-slate-600'
          }`}>
            {formatDate(message.timestamp)}
          </span>

          <div className="absolute top-0.5 right-1.25 hidden group-hover:flex">
            <button
              className="bg-white/10 border-0 px-1.5 py-0.75 text-xs rounded-lg cursor-pointer hover:bg-white/20"
              onClick={() => setIsEditing(true)}
              title="编辑消息"
            >
              ✏️
            </button>
          </div>
        </>
      ) : (
        <div>
          <textarea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            className={`w-full min-w-[250px] min-h-[50px] px-2 py-2 my-1.25 mb-1.25 rounded-lg border bg-gray-900 text-gray-200 font-sans text-base resize-y ${
              theme === 'dark'
                ? 'border-gray-700 text-gray-200'
                : 'border-slate-200 text-slate-700 bg-white'
            }`}
          />
          <div className="flex justify-end gap-2 mt-1.25">
            <button
              onClick={handleSave}
              className={`px-2.5 py-1.25 rounded border-0 cursor-pointer text-sm bg-gray-700 text-gray-200 hover:bg-gray-600 ${
                theme === 'dark' ? '' : 'bg-blue-500 text-white hover:bg-blue-600'
              }`}
            >
              保存
            </button>
            <button
              onClick={() => setIsEditing(false)}
              className={`px-2.5 py-1.25 rounded border-0 cursor-pointer text-sm bg-gray-700 text-gray-200 hover:bg-gray-600 ${
                theme === 'dark' ? '' : 'bg-blue-500 text-white hover:bg-blue-600'
              }`}
            >
              取消
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
