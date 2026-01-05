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
    <aside className={`notifications-sidebar notifications-sidebar-${theme}`}>
      <header className="notifications-header">
        <div className="datetime-container">
          <div
            className="digital-clock"
            dangerouslySetInnerHTML={{
              __html: formatTime(currentTime).replace(/:/g, '<span class="colon">:</span>')
            }}
          />
          <div className="date-display">{formatDate(currentTime)}</div>
        </div>
        <div className="notification-header-actions">
          <button
            className="header-button"
            onClick={clearNotifications}
            title="清空通知"
          >
            清空
          </button>
        </div>
      </header>

      <div className="notifications-status status-closed">
        VCPLog: 未连接
      </div>

      <ul className="notifications-list">
        {notifications.length === 0 ? (
          <li className="notification-item empty">
            <p>暂无通知</p>
          </li>
        ) : (
          notifications.map(notification => (
            <li key={notification.id} className="notification-item">
              <strong>{notification.title}</strong>
              <div className="notification-content">{notification.content}</div>
              <span className="notification-timestamp">
                {new Date(notification.timestamp).toLocaleTimeString()}
              </span>
            </li>
          ))
        )}
      </ul>

      <hr className="section-divider" />

      <div className="notes-section">
        <button id="devButton" className="header-button" title="待开发">
          <svg fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24" width="18" height="18">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712L12 16.125l-2.121-2.121m4.242 0a2.25 2.25 0 0 0 0-3.182M15.75 12H9.75m2.25-4.5H12m2.25 4.5H12" />
          </svg>
          待开发
        </button>
        <button id="openNotesBtn" className="header-button" title="打开笔记">
          <svg fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24" width="18" height="18">
            <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.2-8.2zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
          </svg>
          笔记
        </button>
        <button
          className="header-button settings-button"
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
