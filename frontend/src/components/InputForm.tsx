import { useState, useLayoutEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { SquarePen, Send, StopCircle } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";

interface InputFormProps {
  onSubmit: (inputValue: string, model: string) => void;
  onCancel: () => void;
  isLoading: boolean;
  hasHistory: boolean;
}

export const InputForm: React.FC<InputFormProps> = ({
  onSubmit,
  onCancel,
  isLoading,
  hasHistory,
}) => {
  const [internalInputValue, setInternalInputValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useLayoutEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = "auto";
    const LINE_HEIGHT = 24;
    const MAX_LINES = 5;
    const PADDING_Y = 12;
    const maxHeight = PADDING_Y * 2 + (LINE_HEIGHT * MAX_LINES);
    const contentHeight = textarea.scrollHeight;
    const newHeight = Math.min(contentHeight, maxHeight);
    textarea.style.height = `${newHeight}px`;
  }, [internalInputValue]);

  const handleInternalSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!internalInputValue.trim()) return;
    onSubmit(internalInputValue, "deepseek-chat");
    setInternalInputValue("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleInternalSubmit(undefined);
    }
  };

  const isSubmitDisabled = !internalInputValue.trim() || isLoading;

  return (
    <form
      onSubmit={handleInternalSubmit}
      className="flex flex-col gap-3 p-4 pb-6"
    >
      <div className="relative rounded-2xl bg-white border border-neutral-300 shadow-sm hover:border-neutral-400 transition-all duration-200 overflow-hidden">
        <Textarea
          ref={textareaRef}
          value={internalInputValue}
          onChange={(e) => setInternalInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入消息..."
          className="w-full text-neutral-900 placeholder:text-neutral-400 resize-none border-0 bg-transparent 
                    focus:outline-none focus:ring-0 outline-none focus-visible:ring-0 shadow-none
                    text-base px-4 py-3 pr-12 overflow-y-auto"
          rows={1}
          spellCheck="false"
          style={{
            height: "auto",
            lineHeight: "24px",
            maxHeight: "144px",
            boxSizing: "border-box"
          }}
        />
        
        <div className="absolute right-2 bottom-2">
          {isLoading ? (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-9 w-9 rounded-full bg-red-100 text-red-600 hover:bg-red-200 hover:text-red-700 transition-all duration-200"
              onClick={onCancel}
            >
              <StopCircle className="h-4.5 w-4.5" />
            </Button>
          ) : (
            <Button
              type="submit"
              variant="ghost"
              size="icon"
              className={`h-9 w-9 rounded-full transition-all duration-200 ${
                isSubmitDisabled
                  ? "text-neutral-400 cursor-not-allowed"
                  : "bg-blue-100 text-blue-600 hover:bg-blue-200 hover:text-blue-700"
              }`}
              disabled={isSubmitDisabled}
            >
              <Send className="h-4.5 w-4.5" />
            </Button>
          )}
        </div>
      </div>

      <div className="flex items-center justify-end">
        {hasHistory && (
          <Button
            variant="default"
            size="sm"
            className="bg-white border border-neutral-300 text-neutral-800 hover:bg-neutral-50 hover:border-neutral-400 rounded-xl px-3 py-1.5 text-sm transition-all"
            onClick={() => window.location.reload()}
          >
            <SquarePen size={14} className="mr-1.5" />
            新建对话
          </Button>
        )}
      </div>
    </form>
  );
};
