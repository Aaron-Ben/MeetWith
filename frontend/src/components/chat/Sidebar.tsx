import { useState } from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import AgentList from './AgentList';
import TopicList from './TopicList';
import AgentSettings from './AgentSettings';

type TabType = 'agents' | 'topics' | 'settings';

export default function Sidebar() {
  const { theme } = useTheme();
  const [activeTab, setActiveTab] = useState<TabType>('agents');

  return (
    <aside className={`w-[260px] min-w-[220px] p-4 flex flex-col border-r overflow-hidden ${
      theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-slate-200'
    }`}>
      <div className={`flex mb-4 ${theme === 'dark' ? 'border-b-gray-700' : 'border-b-slate-200'} border-b`}>
        <button
          className={`flex-1 px-1 py-2.5 bg-transparent border-0 text-sm text-center transition-all duration-200 -mb-px ${
            activeTab === 'agents'
              ? theme === 'dark'
                ? 'text-blue-400 border-b-2 border-b-blue-600/75 font-medium'
                : 'text-blue-500 border-b-2 border-b-blue-500/70 font-medium'
              : theme === 'dark'
                ? 'text-gray-400 border-b-2 border-b-transparent'
                : 'text-slate-600 border-b-2 border-b-transparent'
          } ${activeTab === 'agents' ? '' : theme === 'dark' ? 'hover:bg-gray-700 hover:text-blue-400' : 'hover:bg-slate-100 hover:text-blue-500'}`}
          onClick={() => setActiveTab('agents')}
        >
          助手
        </button>
        <button
          className={`flex-1 px-1 py-2.5 bg-transparent border-0 text-sm text-center transition-all duration-200 -mb-px ${
            activeTab === 'topics'
              ? theme === 'dark'
                ? 'text-blue-400 border-b-2 border-b-blue-600/75 font-medium'
                : 'text-blue-500 border-b-2 border-b-blue-500/70 font-medium'
              : theme === 'dark'
                ? 'text-gray-400 border-b-2 border-b-transparent'
                : 'text-slate-600 border-b-2 border-b-transparent'
          } ${activeTab === 'topics' ? '' : theme === 'dark' ? 'hover:bg-gray-700 hover:text-blue-400' : 'hover:bg-slate-100 hover:text-blue-500'}`}
          onClick={() => setActiveTab('topics')}
        >
          话题
        </button>
        <button
          className={`flex-1 px-1 py-2.5 bg-transparent border-0 text-sm text-center transition-all duration-200 -mb-px ${
            activeTab === 'settings'
              ? theme === 'dark'
                ? 'text-blue-400 border-b-2 border-b-blue-600/75 font-medium'
                : 'text-blue-500 border-b-2 border-b-blue-500/70 font-medium'
              : theme === 'dark'
                ? 'text-gray-400 border-b-2 border-b-transparent'
                : 'text-slate-600 border-b-2 border-b-transparent'
          } ${activeTab === 'settings' ? '' : theme === 'dark' ? 'hover:bg-gray-700 hover:text-blue-400' : 'hover:bg-slate-100 hover:text-blue-500'}`}
          onClick={() => setActiveTab('settings')}
        >
          设置
        </button>
      </div>

      <div className="flex-1 overflow-hidden flex flex-col">
        {activeTab === 'agents' && <AgentList />}
        {activeTab === 'topics' && <TopicList />}
        {activeTab === 'settings' && <AgentSettings />}
      </div>
    </aside>
  );
}
