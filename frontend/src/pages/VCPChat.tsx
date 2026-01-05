import { useState } from 'react';
import { ChatProvider } from '@/contexts/ChatContext';
import Sidebar from '@/components/chat/Sidebar';
import ChatArea from '@/components/chat/ChatArea';
import NotificationSidebar from '@/components/chat/NotificationSidebar';
import ResizableSplitter from '@/components/chat/ResizableSplitter';
import './vcpchat.css';

export default function VCPChat() {
  const [sidebarWidth, setSidebarWidth] = useState(260);
  const [notificationWidth, setNotificationWidth] = useState(300);

  return (
    <ChatProvider>
      <div className="vcpchat-container">
        <Sidebar />
        <ResizableSplitter
          direction="horizontal"
          onDrag={(delta) => {
            setSidebarWidth(prev => Math.max(220, Math.min(400, prev + delta)));
          }}
        />
        <ChatArea />
        <ResizableSplitter
          direction="horizontal"
          onDrag={(delta) => {
            setNotificationWidth(prev => Math.max(250, Math.min(500, prev + delta)));
          }}
        />
        <NotificationSidebar />
      </div>
    </ChatProvider>
  );
}
