import { useState, useCallback, useRef } from 'react';
import { sendChatMessageStream, ChatMessage } from '@/api/chat';

interface UseChatStreamOptions {
  onChunk?: (chunk: string) => void;
  onComplete?: (fullContent: string) => void;
  onError?: (error: Error) => void;
}

interface UseChatStreamReturn {
  sendMessage: (messages: ChatMessage[], model?: string) => Promise<void>;
  isLoading: boolean;
  error: Error | null;
  abort: () => void;
}

export function useChatStream(options: UseChatStreamOptions = {}): UseChatStreamReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (messages: ChatMessage[], model?: string) => {
    // 取消之前的请求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    console.log('[useChatStream] Starting send message with', messages.length, 'messages');
    setIsLoading(true);
    setError(null);

    // 创建新的 AbortController
    abortControllerRef.current = new AbortController();

    try {
      let fullContent = '';
      let chunkCount = 0;

      console.log('[useChatStream] Starting stream...');
      for await (const chunk of sendChatMessageStream({
        messages,
        model: model || 'qwen-plus',
        stream: true,
      })) {
        // 检查是否被取消
        if (abortControllerRef.current.signal.aborted) {
          console.log('[useChatStream] Request was aborted');
          throw new Error('Request aborted');
        }

        fullContent += chunk;
        chunkCount++;
        console.log(`[useChatStream] Chunk ${chunkCount}:`, chunk);
        options.onChunk?.(chunk);
      }

      console.log('[useChatStream] Stream completed. Full content:', fullContent);
      options.onComplete?.(fullContent);
    } catch (err) {
      const error = err as Error;
      console.error('[useChatStream] Error:', error);
      if (error.name === 'AbortError' || error.message === 'Request aborted') {
        console.log('[useChatStream] Chat stream aborted');
      } else {
        setError(error);
        options.onError?.(error);
      }
    } finally {
      console.log('[useChatStream] Finally: setting loading to false');
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  }, [options]);

  const abort = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  return {
    sendMessage,
    isLoading,
    error,
    abort,
  };
}
