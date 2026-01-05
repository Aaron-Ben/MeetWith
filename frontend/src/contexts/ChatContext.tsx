import { createContext, useContext, useState, ReactNode, useCallback, useEffect } from 'react';
import { fetchAgents as fetchAgentsApi, Agent as ApiAgent } from '@/api/agents';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  attachments?: Attachment[];
  toolCalls?: ToolCall[];
}

export interface Attachment {
  id: string;
  name: string;
  type: string;
  url: string;
  size?: number;
}

export interface ToolCall {
  toolName: string;
  parameters: Record<string, any>;
  result?: string;
}

export interface Agent {
  id: string;
  name: string;
  avatarUrl?: string;
  systemPrompt: string;
  model: string;
  temperature: number;
  maxTokens: number;
}

export interface Topic {
  id: string;
  name: string;
  createdAt: number;
  messageCount: number;
}

interface ChatContextType {
  // Current state
  currentAgent: Agent | null;
  currentTopic: Topic | null;
  agents: Agent[];
  topics: Topic[];
  messages: Message[];
  showNotificationSidebar: boolean;
  loadingAgents: boolean;

  // Actions
  setCurrentAgent: (agent: Agent | null) => void;
  setCurrentTopic: (topic: Topic | null) => void;
  addMessage: (message: Message) => void;
  updateMessage: (id: string, content: string) => void;
  deleteMessage: (id: string) => void;
  clearMessages: () => void;
  createTopic: (name: string) => Topic;
  deleteTopic: (topicId: string) => void;
  toggleNotificationSidebar: () => void;
  reloadAgents: () => Promise<void>;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within ChatProvider');
  }
  return context;
};

interface ChatProviderProps {
  children: ReactNode;
}

// 将 API 返回的 Agent 数据转换为前端使用的 Agent 格式
const convertApiAgentToAgent = (apiAgent: ApiAgent): Agent => ({
  id: apiAgent.id,
  name: apiAgent.name,
  avatarUrl: apiAgent.avatarUrl || `/avatars/${apiAgent.id}.png`, // 优先使用后端返回的头像路径
  systemPrompt: apiAgent.systemPrompt || '',
  model: 'gpt-4', // 默认模型
  temperature: 0.7,
  maxTokens: 4000,
});

export const ChatProvider: React.FC<ChatProviderProps> = ({ children }) => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loadingAgents, setLoadingAgents] = useState(true);
  const [topics, setTopics] = useState<Topic[]>([
    { id: 'default', name: '主要对话', createdAt: Date.now(), messageCount: 0 },
  ]);

  const [currentAgent, setCurrentAgent] = useState<Agent | null>(null);
  const [currentTopic, setCurrentTopic] = useState<Topic | null>(topics[0] || null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [showNotificationSidebar, setShowNotificationSidebar] = useState(true);

  // 从后端加载 Agent 列表
  const reloadAgents = useCallback(async () => {
    try {
      setLoadingAgents(true);
      const apiAgents = await fetchAgentsApi();
      const convertedAgents = apiAgents.map(convertApiAgentToAgent);
      setAgents(convertedAgents);

      // 如果当前没有选中的 Agent，自动选中第一个
      if (!currentAgent && convertedAgents.length > 0) {
        setCurrentAgent(convertedAgents[0]);
      }
    } catch (error) {
      console.error('Failed to load agents:', error);
      // 加载失败时清空 Agent 列表
      setAgents([]);
    } finally {
      setLoadingAgents(false);
    }
  }, [currentAgent]);

  // 组件挂载时加载 Agent 列表
  useEffect(() => {
    reloadAgents();
  }, [reloadAgents]);

  const addMessage = useCallback((message: Message) => {
    setMessages(prev => [...prev, message]);
  }, []);

  const updateMessage = useCallback((id: string, content: string) => {
    setMessages(prev =>
      prev.map(msg => (msg.id === id ? { ...msg, content } : msg))
    );
  }, []);

  const deleteMessage = useCallback((id: string) => {
    setMessages(prev => prev.filter(msg => msg.id !== id));
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const createTopic = useCallback((name: string) => {
    const newTopic: Topic = {
      id: `topic_${Date.now()}`,
      name,
      createdAt: Date.now(),
      messageCount: 0,
    };
    setTopics(prev => [...prev, newTopic]);
    return newTopic;
  }, []);

  const deleteTopic = useCallback((topicId: string) => {
    setTopics(prev => {
      const filtered = prev.filter(t => t.id !== topicId);
      // Ensure at least one topic remains
      if (filtered.length === 0) {
        const defaultTopic: Topic = {
          id: 'default',
          name: '主要对话',
          createdAt: Date.now(),
          messageCount: 0,
        };
        return [defaultTopic];
      }
      return filtered;
    });
    if (currentTopic?.id === topicId) {
      setCurrentTopic(topics[0] || null);
    }
  }, [currentTopic, topics]);

  const toggleNotificationSidebar = useCallback(() => {
    setShowNotificationSidebar(prev => !prev);
  }, []);

  return (
    <ChatContext.Provider
      value={{
        currentAgent,
        currentTopic,
        agents,
        topics,
        messages,
        showNotificationSidebar,
        loadingAgents,
        setCurrentAgent,
        setCurrentTopic,
        addMessage,
        updateMessage,
        deleteMessage,
        clearMessages,
        createTopic,
        deleteTopic,
        toggleNotificationSidebar,
        reloadAgents,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};
