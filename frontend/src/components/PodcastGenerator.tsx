import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Upload, Mic, ChevronDown } from "lucide-react";

type Mode = "efficient" | "deep";

interface PodcastGeneratorProps {
  onBack: () => void;
}

export const PodcastGenerator: React.FC<PodcastGeneratorProps> = ({
  onBack,
}) => {
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const [mode, setMode] = useState<Mode>("efficient");
  const [speakerCount, setSpeakerCount] = useState<string>("2 人");
  const [hostName, setHostName] = useState<string>("主持人");
  const [guestName, setGuestName] = useState<string>("嘉宾");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFileName(file.name);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white text-neutral-900">
      {/* 顶部栏 */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-neutral-200">
        <div className="flex items-center gap-2">
          <span className="text-sm text-neutral-500">AI 工具</span>
          <span className="text-base font-semibold text-neutral-900">
            AI 播客生成器
          </span>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="border-neutral-300 text-neutral-700 bg-white hover:bg-neutral-50 hover:text-neutral-900"
          onClick={onBack}
        >
          返回聊天
        </Button>
      </header>

      {/* 主体三栏布局 */}
      <main className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-4 p-4 md:p-6">
        {/* 左侧：上传 PDF */}
        <section className="bg-neutral-50 border border-neutral-200 rounded-2xl p-4 flex flex-col">
          <label className="flex-1 flex flex-col items-center justify-center rounded-xl border border-dashed border-neutral-300 bg-white hover:border-blue-400 cursor-pointer transition-colors">
            <div className="flex flex-col items-center gap-3 px-4 py-6 text-center">
              <div className="h-12 w-12 rounded-2xl bg-blue-50 flex items-center justify-center">
                <Upload className="h-6 w-6 text-blue-500" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium text-neutral-900">
                  上传 PDF
                </p>
                <p className="text-xs text-neutral-500">
                  点击上传或拖拽文件到此处
                </p>
              </div>
              {selectedFileName && (
                <p className="text-xs text-neutral-700 mt-2 truncate max-w-[220px]">
                  已选择：{selectedFileName}
                </p>
              )}
            </div>
            <input
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={handleFileChange}
            />
          </label>
        </section>

        {/* 中间：生成控制 */}
        <section className="bg-neutral-50 border border-neutral-200 rounded-2xl p-4 flex flex-col items-center">
          <div className="w-full flex flex-col items-center gap-4">
            <div className="mt-2 mb-1">
              <div className="h-20 w-20 rounded-full bg-blue-50 flex items-center justify-center shadow-lg shadow-blue-100/50">
                <Mic className="h-10 w-10 text-blue-500" />
              </div>
            </div>
            <div className="text-center space-y-1">
              <h2 className="text-lg font-semibold text-neutral-900">
                AI 播客生成器
              </h2>
              <p className="text-xs text-neutral-500">
                基于你上传的内容，一键生成双/多人播客
              </p>
            </div>

            {/* 抽客模式 */}
            <div className="w-full mt-4 space-y-2">
              <p className="text-xs font-medium text-neutral-700">播客模式</p>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setMode("efficient")}
                  className={`rounded-xl px-3 py-2 text-xs border transition-colors ${
                    mode === "efficient"
                      ? "bg-blue-500 text-white border-blue-400"
                      : "bg-white text-neutral-700 border-neutral-300 hover:border-blue-300"
                  }`}
                >
                  高效模式
                </button>
                <button
                  type="button"
                  onClick={() => setMode("deep")}
                  className={`rounded-xl px-3 py-2 text-xs border transition-colors ${
                    mode === "deep"
                      ? "bg-blue-500 text-white border-blue-400"
                      : "bg-white text-neutral-700 border-neutral-300 hover:border-blue-300"
                  }`}
                >
                  深度模式
                </button>
              </div>
              <p className="text-[11px] text-neutral-500">
                高效模式：快速生成概要式播客 · 深度模式：更长、更细致的讨论
              </p>
            </div>

            {/* 生成按钮 */}
            <Button
              className="w-full mt-4 rounded-xl bg-blue-500 hover:bg-blue-600 text-sm font-medium py-2.5"
              disabled={!selectedFileName}
            >
              生成播客
            </Button>

            {!selectedFileName && (
              <p className="text-[11px] text-neutral-500 mt-1">
                请先上传 PDF 文档再生成播客
              </p>
            )}
          </div>
        </section>

        {/* 右侧：对话配置 */}
        <section className="bg-neutral-50 border border-neutral-200 rounded-2xl p-4 flex flex-col">
          <h3 className="text-sm font-medium text-neutral-900 mb-3">
            对话配置
          </h3>

          {/* 对话人数 */}
          <div className="mb-4">
            <p className="text-xs text-neutral-500 mb-1">对话人数</p>
            <button
              type="button"
              className="w-full flex items-center justify-between px-3 py-2 rounded-xl bg-white border border-neutral-300 text-xs text-neutral-700"
            >
              <span>{speakerCount}</span>
              <ChevronDown className="h-3 w-3 text-neutral-500" />
            </button>
          </div>

          {/* 声音选择 */}
          <div className="space-y-3">
            <p className="text-xs text-neutral-500">声音选择</p>

            <div className="flex items-center gap-3 rounded-xl bg-white border border-neutral-300 px-3 py-2">
              <div className="h-8 w-8 rounded-full bg-blue-100" />
              <div className="flex-1">
                <p className="text-xs text-neutral-700">主持人 / 男声 1</p>
                <input
                  value={hostName}
                  onChange={(e) => setHostName(e.target.value)}
                  className="mt-1 w-full text-[11px] bg-transparent border border-neutral-300 rounded-lg px-2 py-1 text-neutral-700 placeholder:text-neutral-400 outline-none focus:border-blue-500"
                  placeholder="主持人名称 / 人设"
                />
              </div>
            </div>

            <div className="flex items-center gap-3 rounded-xl bg-white border border-neutral-300 px-3 py-2">
              <div className="h-8 w-8 rounded-full bg-blue-100" />
              <div className="flex-1">
                <p className="text-xs text-neutral-700">嘉宾 / 女声 1</p>
                <input
                  value={guestName}
                  onChange={(e) => setGuestName(e.target.value)}
                  className="mt-1 w-full text-[11px] bg-transparent border border-neutral-300 rounded-lg px-2 py-1 text-neutral-700 placeholder:text-neutral-400 outline-none focus:border-blue-500"
                  placeholder="嘉宾名称 / 人设"
                />
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};