import type React from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2 } from "lucide-react";
import { InputForm } from "@/components/InputForm";

export type ChatMessage = {
  id: string;
  type: "human" | "ai";
  content: string;
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
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  message.type === "human"
                    ? "bg-blue-500 text-white rounded-br-none"
                    : "bg-white border border-neutral-300 text-neutral-900 rounded-bl-none"
                }`}
              >
                <div className="whitespace-pre-wrap break-words">
                  {message.content}
                </div>
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
