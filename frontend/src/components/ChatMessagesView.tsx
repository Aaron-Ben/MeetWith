import type React from "react";
import { useState } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, Copy, Check, Globe } from "lucide-react";
import { InputForm } from "@/components/InputForm";
import { Button } from "@/components/ui/button";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export type ChatMessage = {
  id: string;
  type: "human" | "ai";
  content: string;
  searchUsed?: boolean;  // 是否使用了网络搜索
};

interface ChatMessagesViewProps {
  messages: ChatMessage[];
  isLoading: boolean;
  scrollAreaRef: React.RefObject<HTMLDivElement | null>;
  onSubmit: (inputValue: string, model: string) => void;
  onCancel: () => void;
}

export function ChatMessagesView({
  messages,
  isLoading,
  scrollAreaRef,
  onSubmit,
  onCancel,
}: ChatMessagesViewProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopy = async (content: string, id: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <ScrollArea className="flex-1 overflow-y-auto" ref={scrollAreaRef}>
        <div className="p-4 md:p-6 space-y-4 max-w-4xl mx-auto pt-16">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.type === "human" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`relative max-w-[80%] rounded-2xl px-4 py-3 group ${
                  message.type === "human"
                    ? "bg-blue-500 text-white rounded-br-none"
                    : "bg-white border border-neutral-300 text-neutral-900 rounded-bl-none"
                }`}
              >
                {/* 网络搜索标记 */}
                {message.type === "ai" && message.searchUsed && (
                  <div className="absolute -top-2 left-2 bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full flex items-center gap-1 border border-blue-200">
                    <Globe className="h-3 w-3" />
                    <span>网络搜索</span>
                  </div>
                )}

                <div className="prose prose-sm max-w-none break-words">
                  {message.type === "ai" ? (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {message.content}
                    </ReactMarkdown>
                  ) : (
                    <div className="whitespace-pre-wrap">{message.content}</div>
                  )}
                </div>
                {message.type === "ai" && message.content && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute top-2 right-2 h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity bg-neutral-100 hover:bg-neutral-200"
                    onClick={() => handleCopy(message.content, message.id)}
                  >
                    {copiedId === message.id ? (
                      <Check className="h-3.5 w-3.5 text-green-600" />
                    ) : (
                      <Copy className="h-3.5 w-3.5 text-neutral-600" />
                    )}
                  </Button>
                )}
              </div>
            </div>
          ))}
          {isLoading &&
            (messages.length === 0 ||
              messages[messages.length - 1].type === "human") && (
              <div className="flex justify-start">
                <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-white border border-neutral-300 text-neutral-900 rounded-bl-none flex items-center">
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  <span>思考中...</span>
                </div>
              </div>
            )}
        </div>
      </ScrollArea>
      <InputForm
        onSubmit={onSubmit}
        isLoading={isLoading}
        onCancel={onCancel}
        hasHistory={messages.length > 0}
      />
    </div>
  );
}
