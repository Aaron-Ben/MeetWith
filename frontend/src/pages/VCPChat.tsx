import { ChatProvider, useChat } from '@/contexts/ChatContext';
import Sidebar from '@/components/chat/Sidebar';
import ChatArea from '@/components/chat/ChatArea';
import NotificationSidebar from '@/components/chat/NotificationSidebar';
import ResizableSplitter from '@/components/chat/ResizableSplitter';

function VCPChatContent() {
  const { showNotificationSidebar } = useChat();

  return (
    <div className="flex w-full h-screen overflow-hidden font-system antialiased">
      <Sidebar />
      <ResizableSplitter direction="horizontal" onDrag={() => {}} />
      <ChatArea />
      {showNotificationSidebar && (
        <>
          <ResizableSplitter direction="horizontal" onDrag={() => {}} />
          <NotificationSidebar />
        </>
      )}
    </div>
  );
}

export default function VCPChat() {
  return (
    <ChatProvider>
      <VCPChatContent />
    </ChatProvider>
  );
}
