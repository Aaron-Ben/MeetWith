import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Save,
  Wand2,
  ChevronLeft,
  ChevronRight,
  Home,
  List,
  Eye,
  Image as ImageIcon,
} from 'lucide-react';
import { usePPTStore } from '@/store/pptStore';
import { Button, Card, Textarea, StatusBadge, ProgressBar, ShimmerOverlay } from '@/components/ppt/ui';
import { cn } from '@/utils/ppt';

interface DescriptionCardProps {
  page: any;
  isGenerating: boolean;
  onEdit: (pageId: string, content: any) => void;
  onGenerate: (pageId: string) => void;
}

const DescriptionCard: React.FC<DescriptionCardProps> = ({ page, isGenerating, onEdit, onGenerate }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [content, setContent] = useState('');

  // 提取描述内容
  const getDescriptionText = (descriptionContent: any) => {
    if (!descriptionContent) return '';
    if (typeof descriptionContent === 'string') return descriptionContent;
    if (descriptionContent.text) return descriptionContent.text;
    if (descriptionContent.text_content) return descriptionContent.text_content.join('\n');
    return '';
  };

  useEffect(() => {
    setContent(getDescriptionText(page.description_content));
  }, [page]);

  const handleSave = () => {
    onEdit(page.id, {
      description_content: { text: content },
    });
    setIsEditing(false);
  };

  const descriptionText = getDescriptionText(page.description_content);

  return (
    <Card className="relative overflow-hidden" hoverable={false}>
      {isGenerating && <ShimmerOverlay />}
      <div className="p-4">
        {/* 标题 */}
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-900">
            {page.outline_content?.title || '未命名页面'}
          </h3>
          <div className="flex items-center gap-2">
            <StatusBadge status={page.status} />
            {isGenerating && (
              <span className="text-xs text-blue-600">生成中...</span>
            )}
          </div>
        </div>

        {/* 大纲预览 */}
        {page.outline_content?.points && page.outline_content.points.length > 0 && (
          <div className="mb-3 p-2 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-500 mb-1">大纲要点：</p>
            <ul className="space-y-1">
              {page.outline_content.points.slice(0, 2).map((point: string, idx: number) => (
                <li key={idx} className="text-xs text-gray-600 truncate flex items-center gap-1">
                  <span className="w-1 h-1 rounded-full bg-gray-400" />
                  {point}
                </li>
              ))}
              {page.outline_content.points.length > 2 && (
                <li className="text-xs text-gray-500">
                  +{page.outline_content.points.length - 2} 个要点
                </li>
              )}
            </ul>
          </div>
        )}

        {/* 描述内容 */}
        {isEditing ? (
          <div className="space-y-2">
            <Textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="输入页面描述内容..."
              rows={6}
              className="text-sm resize-none"
            />
            <div className="flex gap-2">
              <Button size="sm" onClick={handleSave}>
                保存
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  setIsEditing(false);
                  setContent(getDescriptionText(page.description_content));
                }}
              >
                取消
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {descriptionText ? (
              <div className="p-3 bg-blue-50 rounded-lg">
                <p className="text-sm text-gray-700 whitespace-pre-wrap break-words">
                  {descriptionText}
                </p>
              </div>
            ) : (
              <div className="p-6 bg-gray-50 rounded-lg text-center">
                <ImageIcon className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-500">暂无描述内容</p>
              </div>
            )}

            {/* 操作按钮 */}
            <div className="flex items-center justify-between">
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setIsEditing(true)}
                >
                  编辑内容
                </Button>
                <Button
                  size="sm"
                  onClick={() => onGenerate(page.id)}
                  loading={isGenerating}
                  disabled={isGenerating}
                  icon={<Wand2 className="w-3 h-3" />}
                >
                  {descriptionText ? '重新生成' : 'AI生成'}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

export const DetailEditor: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const {
    currentProject,
    isGlobalLoading,
    activeTaskId,
    taskProgress,
    pageDescriptionGeneratingTasks,
    error,
    syncProject,
    updatePageLocal,
    generateDescriptions,
    generatePageDescription,
    saveAllPages,
    setError,
  } = usePPTStore();

  useEffect(() => {
    if (projectId) {
      syncProject(projectId);
    }
  }, [projectId]);

  const handleBatchGenerate = async () => {
    setError(null);
    try {
      await generateDescriptions();
    } catch (err) {
      console.error('批量生成失败:', err);
    }
  };

  const handleNextStep = () => {
    saveAllPages().then(() => {
      if (projectId) {
        navigate(`/ppt/preview/${projectId}`);
      }
    });
  };

  const handleBack = () => {
    if (projectId) {
      navigate(`/ppt/outline/${projectId}`);
    }
  };

  if (!currentProject) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4" />
          <p className="text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  const hasPages = currentProject.pages && currentProject.pages.length > 0;
  const allHaveDescriptions = currentProject.pages?.every(
    (p) => p.description_content && getDescriptionText(p.description_content)
  );

  const getDescriptionText = (descriptionContent: any) => {
    if (!descriptionContent) return '';
    if (typeof descriptionContent === 'string') return descriptionContent;
    if (descriptionContent.text) return descriptionContent.text;
    if (descriptionContent.text_content) return descriptionContent.text_content.join('\n');
    return '';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航栏 */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate('/ppt')}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <Home className="w-5 h-5 text-gray-600" />
              </button>
              <div className="h-6 w-px bg-gray-300" />
              <h1 className="text-lg font-semibold text-gray-900 truncate max-w-md">
                {currentProject.idea_prompt || currentProject.outline_text || currentProject.description_text || '未命名项目'}
              </h1>
              <StatusBadge status={currentProject.status} />
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => saveAllPages()}
                icon={<Save className="w-4 h-4" />}
              >
                保存
              </Button>
            </div>
          </div>

          {/* 步骤指示器 */}
          <div className="flex items-center justify-center mt-4">
            <div className="flex items-center gap-2">
              <button
                onClick={handleBack}
                className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-600 rounded-lg font-medium hover:bg-gray-200 transition-colors"
              >
                <List className="w-4 h-4" />
                <span>1. 大纲编辑</span>
              </button>
              <ChevronRight className="w-4 h-4 text-gray-400" />
              <button
                className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg font-medium"
              >
                <span>2. 编辑描述</span>
              </button>
              <ChevronRight className="w-4 h-4 text-gray-400" />
              <button
                onClick={handleNextStep}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors",
                  allHaveDescriptions
                    ? "bg-gray-100 text-gray-600 hover:bg-gray-200"
                    : "bg-gray-100 text-gray-600 opacity-50 cursor-not-allowed"
                )}
                disabled={!allHaveDescriptions}
              >
                <Eye className="w-4 h-4" />
                <span>3. 预览导出</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 主内容区 */}
      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* 操作栏 */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Button
              onClick={handleBatchGenerate}
              icon={<Wand2 className="w-4 h-4" />}
              disabled={isGlobalLoading}
            >
              批量生成描述
            </Button>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">
              已完成: {currentProject.pages?.filter((p) => getDescriptionText(p.description_content)).length || 0} / {currentProject.pages?.length || 0}
            </span>
          </div>
        </div>

        {/* 进度条 */}
        {activeTaskId && taskProgress && (
          <Card className="mb-4 p-4 bg-blue-50 border-blue-200">
            <ProgressBar
              progress={taskProgress.completed || 0}
              total={taskProgress.total || 0}
              label="生成进度"
            />
          </Card>
        )}

        {/* 错误提示 */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600">
            {error}
            <button
              onClick={() => setError(null)}
              className="ml-2 text-red-800 underline"
            >
              关闭
            </button>
          </div>
        )}

        {/* 页面网格 */}
        {hasPages ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {currentProject.pages.map((page) => (
              <DescriptionCard
                key={page.id}
                page={page}
                isGenerating={!!pageDescriptionGeneratingTasks[page.id!]}
                onEdit={updatePageLocal}
                onGenerate={generatePageDescription}
              />
            ))}
          </div>
        ) : (
          <Card className="p-12 text-center">
            <div className="max-w-md mx-auto">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <List className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">还没有页面</h3>
              <p className="text-gray-600 mb-4">
                请先在大纲编辑页面创建页面
              </p>
              <Button onClick={handleBack} icon={<ChevronLeft className="w-4 h-4" />}>
                返回大纲编辑
              </Button>
            </div>
          </Card>
        )}

        {/* 底部操作栏 */}
        {hasPages && allHaveDescriptions && (
          <div className="mt-6 flex items-center justify-center">
            <Button
              size="lg"
              onClick={handleNextStep}
              icon={<ChevronRight className="w-5 h-5" />}
            >
              下一步：预览导出
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};
