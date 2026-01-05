import { useState, useEffect } from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import { useNavigate } from 'react-router-dom';

interface Notification {
  id: string;
  type: string;
  title: string;
  content: string;
  timestamp: number;
}

export default function NotificationSidebar() {
  const { theme } = useTheme();
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
  };

  const clearNotifications = () => {
    setNotifications([]);
  };

  return (
    <aside className={`w-[300px] min-w-[250px] flex flex-col ${
      theme === 'dark' ? 'bg-gray-800 border-l-gray-700' : 'bg-white border-l-slate-200'
    } border-l`}>
      <header className={`px-4 py-2.5 flex justify-between items-center ${
        theme === 'dark' ? 'bg-gray-700 border-b-gray-700' : 'bg-slate-100 border-b-slate-200'
      } border-b`}>
        <div className="flex flex-col items-start">
          <div
            className={`text-2xl font-extrabold tracking-wide leading-none mb-[-1px] text-left ${
              theme === 'dark' ? 'text-blue-400' : 'text-blue-500'
            }`}
            style={{ fontFamily: 'Arial Black, sans-serif' }}
          >
            {formatTime(currentTime).split('').map((char, i) => (
              <span key={i} className={char === ':' ? 'colon' : ''} style={char === ':' ? { animation: 'blinkColon 2s infinite' } : {}}>
                {char}
              </span>
            ))}
          </div>
          <div className={`text-xs font-medium leading-none mt-0 relative top-[-1px] left-0.5 ${
            theme === 'dark' ? 'text-gray-400' : 'text-slate-600'
          }`}>
            {formatDate(currentTime)}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            className={`bg-transparent border px-2.5 h-8 rounded-lg cursor-pointer text-sm inline-flex items-center justify-center transition-all ${
              theme === 'dark'
                ? 'border-gray-600 text-gray-400 hover:bg-gray-600 hover:text-gray-200'
                : 'border-blue-500 text-blue-500 hover:bg-blue-600 hover:text-white'
            }`}
            onClick={clearNotifications}
            title="清空通知"
          >
            清空
          </button>
        </div>
      </header>

      <div className={`px-4 py-2 text-sm text-center ${
        theme === 'dark' ? 'bg-gray-950 text-gray-400 border-b-gray-700' : 'bg-slate-100 text-slate-600 border-b-slate-200'
      } border-b`}>
        VCPLog: 未连接
      </div>

      <ul className="list-none m-0 p-0 overflow-y-auto flex-1">
        {notifications.length === 0 ? (
          <li className={`px-4 py-5 text-center ${
            theme === 'dark' ? 'text-gray-400' : 'text-slate-600'
          }`}>
            <p>暂无通知</p>
          </li>
        ) : (
          notifications.map(notification => (
            <li
              key={notification.id}
              className={`px-4 py-2.5 border-b text-sm ${
                theme === 'dark' ? 'bg-gray-800 border-gray-700 text-gray-200' : 'bg-sky-50 border-slate-200 text-slate-700'
              }`}
            >
              <strong className={`block mb-1 ${
                theme === 'dark' ? 'text-blue-400' : 'text-blue-500'
              }`}>
                {notification.title}
              </strong>
              <div>{notification.content}</div>
              <span className={`text-xs opacity-70 block text-right mt-1.25 ${
                theme === 'dark' ? 'text-gray-400' : 'text-slate-600'
              }`}>
                {new Date(notification.timestamp).toLocaleTimeString()}
              </span>
            </li>
          ))
        )}
      </ul>

      <hr className={`border-0 border-t my-0 w-full ${
        theme === 'dark' ? 'border-t-gray-700' : 'border-t-slate-200'
      }`} />

      <div className={`px-4 py-2.5 flex justify-end items-center gap-2 ${
        theme === 'dark' ? 'bg-gray-800' : 'bg-white'
      }`}>
        <button
          className={`px-2.5 h-8 rounded-lg cursor-pointer border transition-all flex items-center gap-1.5 ${
            theme === 'dark'
              ? 'bg-gray-700 text-gray-400 border-gray-700 hover:bg-gray-600 hover:text-gray-200'
              : 'bg-blue-500 text-white border-blue-500 hover:bg-blue-600'
          }`}
          title="待开发"
        >
          <svg fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24" width="18" height="18">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712L12 16.125l-2.121-2.121m4.242 0a2.25 2.25 0 0 0 0-3.182M15.75 12H9.75m2.25-4.5H12m2.25 4.5H12" />
          </svg>
          待开发
        </button>
        <button
          className={`px-2.5 h-8 rounded-lg cursor-pointer border transition-all flex items-center gap-1.5 ${
            theme === 'dark'
              ? 'bg-gray-700 text-gray-400 border-gray-700 hover:bg-gray-600 hover:text-gray-200'
              : 'bg-blue-500 text-white border-blue-500 hover:bg-blue-600'
          }`}
          title="打开笔记"
        >
          <svg fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24" width="18" height="18">
            <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.2-8.2zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
          </svg>
          笔记
        </button>
        <button
          className={`px-2.5 h-8 rounded-lg cursor-pointer border transition-all flex items-center gap-1.5 ${
            theme === 'dark'
              ? 'bg-gray-700 text-gray-400 border-gray-700 hover:bg-gray-600 hover:text-gray-200'
              : 'bg-blue-500 text-white border-blue-500 hover:bg-blue-600'
          }`}
          onClick={() => navigate('/settings')}
          title="打开设置"
        >
          <svg fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24" width="18" height="18">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          设置
        </button>
      </div>
    </aside>
  );
}
