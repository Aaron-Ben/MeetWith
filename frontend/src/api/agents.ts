import { apiClient } from './client';

export interface Agent {
  id: string;
  name: string;
  configPath?: string;
  systemPrompt?: string;
  avatarUrl?: string | null;
}

export interface AgentResponse {
  agents: Agent[];
}

export interface SingleAgentResponse {
  id: string;
  name: string;
  configPath: string;
  systemPrompt: string;
}

// 获取所有 Agent 列表
export const fetchAgents = async (): Promise<Agent[]> => {
  const response = await apiClient.get<AgentResponse>('/admin_api/agents');
  return response.data.agents;
};

// 获取单个 Agent 的详细信息
export const fetchAgent = async (agentName: string): Promise<SingleAgentResponse> => {
  const response = await apiClient.get<SingleAgentResponse>(`/admin_api/agents/${agentName}`);
  return response.data;
};

// 保存 Agent 配置
export const saveAgent = async (agentName: string, systemPrompt: string): Promise<{ message: string }> => {
  const response = await apiClient.post<{ message: string }>(`/admin_api/agents/${agentName}`, {
    systemPrompt
  });
  return response.data;
};

// 删除 Agent
export const deleteAgent = async (agentName: string): Promise<{ message: string }> => {
  const response = await apiClient.delete<{ message: string }>(`/admin_api/agents/${agentName}`);
  return response.data;
};

// 上传 Agent 头像
export const uploadAgentAvatar = async (agentName: string, file: File): Promise<{ message: string; avatarUrl: string }> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<{ message: string; avatarUrl: string }>(
    `/admin_api/agents/${agentName}/avatar`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
};
