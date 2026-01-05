import { createContext, useContext, useState, ReactNode, useCallback } from 'react';

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

export const ChatProvider: React.FC<ChatProviderProps> = ({ children }) => {
  const [agents, setAgents] = useState<Agent[]>([
    {
      id: 'xiaoke',
      name: '猫娘小克',
      avatarUrl: '/avatars/xiaoke.png',
      systemPrompt: '你是猫娘小克，一个可爱的AI助手。',
      model: 'gpt-4',
      temperature: 0.7,
      maxTokens: 4000,
    },
  ]);

  const [topics, setTopics] = useState<Topic[]>([
    { id: 'default', name: '主要对话', createdAt: Date.now(), messageCount: 0 },
  ]);

  const [currentAgent, setCurrentAgent] = useState<Agent | null>(agents[0] || null);
  const [currentTopic, setCurrentTopic] = useState<Topic | null>(topics[0] || null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [showNotificationSidebar, setShowNotificationSidebar] = useState(true);

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
        setCurrentAgent,
        setCurrentTopic,
        addMessage,
        updateMessage,
        deleteMessage,
        clearMessages,
        createTopic,
        deleteTopic,
        toggleNotificationSidebar,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};
