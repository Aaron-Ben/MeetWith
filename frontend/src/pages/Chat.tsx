import { useState, useEffect, useRef, useCallback } from "react";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { ChatMessagesView } from "@/components/ChatMessagesView";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

type ChatMessage = {
  id: string;
  type: "human" | "ai";
  content: string;
  searchUsed?: boolean;  // 标记是否使用了网络搜索
};

export const ChatApp: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollViewport = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      ) as HTMLDivElement | null;
      if (scrollViewport) {
        scrollViewport.scrollTop = scrollViewport.scrollHeight;
      }
    }
  }, [messages]);

  const handleSubmit = useCallback(
    async (
      submittedInputValue: string,
      model: string
    ) => {
      if (!submittedInputValue.trim() || isLoading) return;

      const userMessage: ChatMessage = {
        id: Date.now().toString(),
        type: "human",
        content: submittedInputValue,
      };

      const baseMessages = [...messages, userMessage];
      const aiMessageId = `${Date.now()}-ai`;
      const aiPlaceholder: ChatMessage = {
        id: aiMessageId,
        type: "ai",
        content: "",
      };

      setMessages([...baseMessages, aiPlaceholder]);
      setIsLoading(true);
      setError(null);

      const payload = baseMessages.map((m) => ({
        role: m.type === "human" ? "user" : "assistant",
        content: m.content,
      }));

      const controller = new AbortController();
      controllerRef.current = controller;

      try {
        const res = await fetch(
          import.meta.env.DEV
            ? "http://localhost:8000/api/chat/stream"
            : "/api/chat/stream",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ messages: payload, model, use_tools: true }),
            signal: controller.signal,
          }
        );

        if (!res.ok || !res.body) {
          throw new Error(`HTTP error ${res.status}`);
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let aiContent = "";
        let searchUsed = false;
        const SEARCH_MARKER = "[SEARCH_USED]";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          aiContent += chunk;

          // 检查搜索标记
          if (aiContent.includes(SEARCH_MARKER)) {
            searchUsed = true;
            aiContent = aiContent.replace(SEARCH_MARKER, "");
          }

          const contentSnapshot = aiContent;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === aiMessageId
                ? { ...m, content: contentSnapshot, searchUsed }
                : m
            )
          );
        }
      } catch (e: any) {
        if (e?.name === "AbortError") {
          // 用户取消，不视为错误
        } else {
          setError(e.message ?? "请求失败");
        }
      } finally {
        controllerRef.current = null;
        setIsLoading(false);
      }
    },
    [messages, isLoading]
  );

  const handleCancel = useCallback(() => {
    if (controllerRef.current) {
      controllerRef.current.abort();
    }
    setIsLoading(false);
  }, []);

  return (
    <div className="flex h-full">
      {/* 设置按钮 */}
      <Link to="/settings" className="fixed top-4 right-4 z-50">
        <Button variant="outline" size="icon">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.09a2 2 0 0 1-1-1.74v-.47a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.39a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
        </Button>
      </Link>

      <main className="h-full w-full max-w-4xl mx-auto">
        {messages.length === 0 ? (
          <WelcomeScreen
            handleSubmit={handleSubmit}
            isLoading={isLoading}
            onCancel={handleCancel}
          />
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="flex flex-col items-center justify-center gap-4">
              <h1 className="text-2xl text-red-400 font-bold">Error</h1>
              <p className="text-red-400">{JSON.stringify(error)}</p>

              <Button
                variant="destructive"
                onClick={() => window.location.reload()}
              >
                Retry
              </Button>
            </div>
          </div>
        ) : (
          <ChatMessagesView
            messages={messages}
            isLoading={isLoading}
            scrollAreaRef={scrollAreaRef}
            onSubmit={handleSubmit}
            onCancel={handleCancel}
          />
        )}
      </main>
    </div>
  );
};
