import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Home,
  List,
  FileText,
  Download,
  Wand2,
  ChevronLeft,
  ChevronRight,
  Edit3,
  Image as ImageIcon,
  ZoomIn,
  ZoomOut,
} from 'lucide-react';
import { usePPTStore } from '@/store/pptStore';
import { Button, Card, Modal, Textarea, StatusBadge, ProgressBar, ShimmerOverlay } from '@/components/ppt/ui';
import { getImageUrl } from '@/api/client';

interface SlideCardProps {
  page: any;
  isGenerating: boolean;
  onSelect: (page: any) => void;
  onGenerate: (pageId: string) => void;
  onEdit: (pageId: string, prompt: string) => void;
}

const SlideCard: React.FC<SlideCardProps> = ({ page, isGenerating, onSelect, onGenerate, onEdit }) => {
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editPrompt, setEditPrompt] = useState('');
  const imageUrl = getImageUrl(page.generated_image_url || page.generated_image_path, page.updated_at);

  return (
    <>
      <Card
        className="relative overflow-hidden cursor-pointer group"
        hoverable
        onClick={() => !isGenerating && onSelect(page)}
      >
        {isGenerating && <ShimmerOverlay />}

        {/* 图片或占位符 */}
        <div className="aspect-video bg-gray-100 relative overflow-hidden">
          {imageUrl ? (
            <img
              src={imageUrl}
              alt={page.outline_content?.title}
              className="w-full h-full object-cover"
              loading="lazy"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <ImageIcon className="w-12 h-12 text-gray-400" />
            </div>
          )}

          {/* 悬浮操作栏 */}
          <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
            {imageUrl ? (
              <>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={(e) => {
                    e.stopPropagation();
                    setIsEditModalOpen(true);
                  }}
                  icon={<Edit3 className="w-3 h-3" />}
                >
                  编辑
                </Button>
                <Button
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    onGenerate(page.id);
                  }}
                  loading={isGenerating}
                  disabled={isGenerating}
                  icon={<Wand2 className="w-3 h-3" />}
                >
                  重新生成
                </Button>
              </>
            ) : (
              <Button
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  onGenerate(page.id);
                }}
                loading={isGenerating}
                disabled={isGenerating}
                icon={<Wand2 className="w-3 h-3" />}
              >
                生成图片
              </Button>
            )}
          </div>
        </div>

        {/* 页面信息 */}
        <div className="p-3">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-gray-900 text-sm truncate flex-1">
              {page.outline_content?.title || '未命名页面'}
            </h3>
            <StatusBadge status={page.status} className="text-xs" />
          </div>
          {isGenerating && (
            <p className="text-xs text-blue-600 mt-1">生成中...</p>
          )}
        </div>
      </Card>

      {/* 编辑图片模态框 */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="编辑图片"
        size="md"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            用自然语言描述你想要的修改，AI将重新生成图片
          </p>
          <Textarea
            placeholder="例如：把背景改成蓝色，增加一些图表，使用更现代的设计风格..."
            value={editPrompt}
            onChange={(e) => setEditPrompt(e.target.value)}
            rows={4}
          />
          <div className="flex justify-end gap-2">
            <Button
              variant="ghost"
              onClick={() => {
                setIsEditModalOpen(false);
                setEditPrompt('');
              }}
            >
              取消
            </Button>
            <Button
              onClick={() => {
                onEdit(page.id, editPrompt);
                setIsEditModalOpen(false);
                setEditPrompt('');
              }}
              disabled={!editPrompt.trim()}
              icon={<Edit3 className="w-4 h-4" />}
            >
              开始编辑
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
};

export const Preview: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const {
    currentProject,
    isGlobalLoading,
    activeTaskId,
    taskProgress,
    pageGeneratingTasks,
    error,
    syncProject,
    generateImages,
    generatePageImage,
    editPageImage,
    exportPPTX,
    exportPDF,
    setError,
  } = usePPTStore();

  const [selectedPage, setSelectedPage] = useState<any | null>(null);
  const [imageZoom, setImageZoom] = useState(1);

  useEffect(() => {
    if (projectId) {
      syncProject(projectId);
    }
  }, [projectId]);

  const handleBatchGenerate = async () => {
    setError(null);
    try {
      await generateImages();
    } catch (err) {
      console.error('批量生成失败:', err);
    }
  };

  const handleEditImage = async (pageId: string, prompt: string) => {
    setError(null);
    try {
      await editPageImage(pageId, prompt);
    } catch (err) {
      console.error('编辑图片失败:', err);
    }
  };

  const handleExportPPTX = async () => {
    try {
      await exportPPTX();
    } catch (err) {
      console.error('导出失败:', err);
    }
  };

  const handleExportPDF = async () => {
    try {
      await exportPDF();
    } catch (err) {
      console.error('导出失败:', err);
    }
  };

  const handleBack = () => {
    if (projectId) {
      navigate(`/ppt/detail/${projectId}`);
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
  const allHaveImages = currentProject.pages?.every(
    (p) => p.generated_image_url || p.generated_image_path
  );

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
                onClick={handleBack}
                icon={<ChevronLeft className="w-4 h-4" />}
              >
                返回
              </Button>
            </div>
          </div>

          {/* 步骤指示器 */}
          <div className="flex items-center justify-center mt-4">
            <div className="flex items-center gap-2">
              <button
                onClick={handleBack}
                className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 text-gray-600 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
              >
                <List className="w-3.5 h-3.5" />
                <span>大纲</span>
              </button>
              <ChevronRight className="w-4 h-4 text-gray-400" />
              <button
                onClick={handleBack}
                className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 text-gray-600 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>描述</span>
              </button>
              <ChevronRight className="w-4 h-4 text-gray-400" />
              <button className="flex items-center gap-2 px-3 py-1.5 bg-blue-500 text-white rounded-lg text-sm font-medium">
                <span>预览导出</span>
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
              批量生成图片
            </Button>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">
              已完成: {currentProject.pages?.filter((p) => p.generated_image_url || p.generated_image_path).length || 0} / {currentProject.pages?.length || 0}
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

        {/* 导出操作栏 */}
        {allHaveImages && (
          <Card className="mb-4 p-4 bg-green-50 border-green-200">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-medium text-gray-900">准备就绪！</h3>
                <p className="text-sm text-gray-600">所有页面图片已生成完成，可以导出PPT了</p>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  onClick={handleExportPPTX}
                  loading={isGlobalLoading}
                  icon={<Download className="w-4 h-4" />}
                >
                  导出PPTX
                </Button>
                <Button
                  variant="secondary"
                  onClick={handleExportPDF}
                  loading={isGlobalLoading}
                  icon={<Download className="w-4 h-4" />}
                >
                  导出PDF
                </Button>
              </div>
            </div>
          </Card>
        )}

        {/* 页面网格 */}
        {hasPages ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {currentProject.pages.map((page) => (
              <SlideCard
                key={page.id}
                page={page}
                isGenerating={!!pageGeneratingTasks[page.id!]}
                onSelect={setSelectedPage}
                onGenerate={generatePageImage}
                onEdit={handleEditImage}
              />
            ))}
          </div>
        ) : (
          <Card className="p-12 text-center">
            <div className="max-w-md mx-auto">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <ImageIcon className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">还没有页面</h3>
              <p className="text-gray-600 mb-4">请先完成前面的步骤</p>
              <Button onClick={handleBack} icon={<ChevronLeft className="w-4 h-4" />}>
                返回
              </Button>
            </div>
          </Card>
        )}
      </div>

      {/* 图片预览模态框 */}
      {selectedPage && (
        <Modal
          isOpen={!!selectedPage}
          onClose={() => {
            setSelectedPage(null);
            setImageZoom(1);
          }}
          title={selectedPage.outline_content?.title || '未命名页面'}
          size="xl"
        >
          <div className="space-y-4">
            <div className="relative overflow-hidden rounded-lg bg-gray-100">
              <img
                src={getImageUrl(
                  selectedPage.generated_image_url || selectedPage.generated_image_path,
                  selectedPage.updated_at
                )}
                alt={selectedPage.outline_content?.title}
                className="w-full transition-transform duration-200"
                style={{ transform: `scale(${imageZoom})` }}
              />
            </div>

            {/* 缩放控制 */}
            <div className="flex items-center justify-center gap-4">
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setImageZoom(Math.max(0.5, imageZoom - 0.1))}
                icon={<ZoomOut className="w-4 h-4" />}
              >
                缩小
              </Button>
              <span className="text-sm text-gray-600">{Math.round(imageZoom * 100)}%</span>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setImageZoom(Math.min(2, imageZoom + 0.1))}
                icon={<ZoomIn className="w-4 h-4" />}
              >
                放大
              </Button>
            </div>

            {/* 描述信息 */}
            {selectedPage.description_content && (
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 whitespace-pre-wrap">
                  {typeof selectedPage.description_content === 'string'
                    ? selectedPage.description_content
                    : selectedPage.description_content.text ||
                      (selectedPage.description_content.text_content?.join('\n'))}
                </p>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
};
