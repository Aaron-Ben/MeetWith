import { useState } from 'react';
import { useChat } from '@/contexts/ChatContext';

export default function TopicList() {
  const { topics, currentTopic, setCurrentTopic, createTopic, deleteTopic } = useChat();
  const [searchQuery, setSearchQuery] = useState('');

  const filteredTopics = topics.filter(topic =>
    topic.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="sidebar-tab-content active">
      <div className="topics-header">
        <h2>话题</h2>
        <div className="topic-search-container">
          <input
            type="text"
            className="topic-search-input"
            placeholder="搜索话题..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>
      <ul className="topic-list">
        {filteredTopics.map(topic => (
          <li
            key={topic.id}
            className={`topic-item ${currentTopic?.id === topic.id ? 'active' : ''}`}
            onClick={() => setCurrentTopic(topic)}
          >
            <span className="agent-name">{topic.name}</span>
            <span className="message-count">{topic.messageCount}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
