import { useState } from 'react';
import { useChat } from '@/contexts/ChatContext';
import { useTheme } from '@/contexts/ThemeContext';

export default function TopicList() {
  const { topics, currentTopic, setCurrentTopic, createTopic, deleteTopic } = useChat();
  const { theme } = useTheme();
  const [searchQuery, setSearchQuery] = useState('');

  const filteredTopics = topics.filter(topic =>
    topic.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex flex-col flex-1 overflow-y-auto overflow-x-hidden">
      <div className="flex flex-col pb-2.5 mb-4">
        <h2 className={`text-xl mt-1 mb-2.5 border-b-0 pb-0 ${
          theme === 'dark' ? 'text-gray-400' : 'text-slate-600'
        }`}>
          话题
        </h2>
        <div className="flex w-full">
          <input
            type="text"
            placeholder="搜索话题..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={`flex-1 px-3 py-2.5 rounded-20 border text-base outline-none focus:ring-2 ${
              theme === 'dark'
                ? 'bg-gray-900 border-gray-700 text-gray-200 focus:border-blue-600/75 focus:ring-blue-900/30'
                : 'bg-white border-slate-200 text-slate-700 focus:border-blue-500/70 focus:ring-blue-500/30'
            }`}
            style={{ borderRadius: '20px' }}
          />
        </div>
      </div>
      <ul className="list-none m-0 p-0 overflow-y-auto flex-1">
        {filteredTopics.map(topic => (
          <li
            key={topic.id}
            className={`px-3 py-2.5 mb-1.5 rounded-lg cursor-pointer flex items-center transition-all duration-200 ${
              currentTopic?.id === topic.id
                ? theme === 'dark'
                  ? 'bg-blue-600/75 text-white font-medium'
                  : 'bg-blue-500/70 text-white font-medium'
                : theme === 'dark'
                  ? 'hover:bg-gray-700 hover:translate-x-0.5'
                  : 'hover:bg-slate-200 hover:translate-x-0.5'
            }`}
            onClick={() => setCurrentTopic(topic)}
          >
            <span className={`font-normal text-base flex-1 whitespace-nowrap overflow-hidden text-ellipsis ${
              theme === 'dark' ? 'text-gray-200' : 'text-slate-700'
            }`}>
              {topic.name}
            </span>
            <span className={`ml-auto px-2 py-0.75 rounded-10 text-xs min-w-5 text-center font-bold ${
              theme === 'dark' ? 'bg-gray-700 text-blue-400' : 'bg-slate-200 text-blue-500'
            }`} style={{ borderRadius: '10px' }}>
              {topic.messageCount}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
