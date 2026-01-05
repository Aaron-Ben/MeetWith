import { useState } from 'react';
import { useChat } from '@/contexts/ChatContext';
import { useTheme } from '@/contexts/ThemeContext';
import AgentList from './AgentList';
import TopicList from './TopicList';
import AgentSettings from './AgentSettings';

type TabType = 'agents' | 'topics' | 'settings';

export default function Sidebar() {
  const { theme } = useTheme();
  const [activeTab, setActiveTab] = useState<TabType>('agents');

  return (
    <aside className={`sidebar sidebar-${theme}`}>
      <div className="sidebar-tabs">
        <button
          className={`sidebar-tab-button ${activeTab === 'agents' ? 'active' : ''}`}
          onClick={() => setActiveTab('agents')}
        >
          助手
        </button>
        <button
          className={`sidebar-tab-button ${activeTab === 'topics' ? 'active' : ''}`}
          onClick={() => setActiveTab('topics')}
        >
          话题
        </button>
        <button
          className={`sidebar-tab-button ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
        >
          设置
        </button>
      </div>

      <div className="sidebar-content">
        {activeTab === 'agents' && <AgentList />}
        {activeTab === 'topics' && <TopicList />}
        {activeTab === 'settings' && <AgentSettings />}
      </div>
    </aside>
  );
}
