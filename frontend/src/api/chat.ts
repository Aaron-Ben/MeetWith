import { apiClient } from './client';

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  stream?: boolean;
  model?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface ChatChoice {
  index: number;
  message: {
    role: string;
    content: string;
  };
  finish_reason: string;
}

export interface ChatResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: ChatChoice[];
}

/**
 * 发送聊天请求（非流式）
 */
export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await apiClient.post<ChatResponse>('/v1/chat/completions', {
    ...request,
    stream: false,
  });
  return response.data;
}

/**
 * 发送聊天请求（流式）
 * 返回一个异步生成器，逐个产生内容块
 * 在浏览器环境中使用 fetch API 来处理 SSE
 */
export async function* sendChatMessageStream(request: ChatRequest): AsyncGenerator<string, void, unknown> {
  console.log('[Chat API] Sending stream request with messages:', request.messages.length);

  // 使用 fetch API 而不是 axios，因为浏览器中的 axios 不支持流式响应
  const response = await fetch('/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
    },
    body: JSON.stringify({
      messages: request.messages,
      model: request.model || 'qwen-plus',
      stream: true,
      temperature: request.temperature,
      max_tokens: request.max_tokens,
    }),
  });

  console.log('[Chat API] Response received, status:', response.status);

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  // 获取 ReadableStream
  const stream = response.body;
  if (!stream) {
    throw new Error('Response body is null');
  }

  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith('data: ')) continue;

        const data = trimmed.slice(6);
        if (data === '[DONE]') {
          console.log('[Chat API] Stream completed with [DONE]');
          return;
        }

        try {
          const parsed = JSON.parse(data);
          const content = parsed.choices?.[0]?.delta?.content;
          if (content) {
            console.log('[Chat API] Received chunk:', content);
            yield content;
          }
        } catch (e) {
          console.warn('[Chat API] Failed to parse SSE data:', data, e);
        }
      }
    }
  } catch (error) {
    console.error('[Chat API] Stream error:', error);
    throw error;
  } finally {
    reader.releaseLock();
    console.log('[Chat API] Reader released');
  }
}
