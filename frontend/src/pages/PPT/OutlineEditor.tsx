import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Plus,
  Trash2,
  GripVertical,
  Save,
  Wand2,
  ChevronRight,
  Home,
  FileText,
  Eye,
} from 'lucide-react';
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors, DragEndEvent } from '@dnd-kit/core';
import { arrayMove, SortableContext, sortableKeyboardCoordinates, verticalListSortingStrategy, useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { usePPTStore } from '@/store/pptStore';
import { Button, Card, Modal, Textarea, Input, StatusBadge, ProgressBar } from '@/components/ppt/ui';

interface SortablePageCardProps {
  page: any;
  index: number;
  onEdit: (pageId: string, data: any) => void;
  onDelete: (pageId: string) => void;
}

const SortablePageCard: React.FC<SortablePageCardProps> = ({ page, index, onEdit, onDelete }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: page.id! });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState(page.outline_content?.title || '');
  const [points, setPoints] = useState(page.outline_content?.points?.join('\n') || '');

  useEffect(() => {
    setTitle(page.outline_content?.title || '');
    setPoints(page.outline_content?.points?.join('\n') || '');
  }, [page]);

  const handleSave = () => {
    onEdit(page.id, {
      outline_content: {
        title,
        points: points.split('\n').filter((p: string) => p.trim()),
      },
    });
    setIsEditing(false);
  };

  return (
    <div ref={setNodeRef} style={style} className="relative group">
      <Card className="p-4" hoverable={false}>
        <div className="flex items-start gap-3">
          {/* 拖拽手柄 */}
          <button
            className="mt-1 text-gray-400 hover:text-gray-600 cursor-grab active:cursor-grabbing"
            {...attributes}
            {...listeners}
          >
            <GripVertical className="w-5 h-5" />
          </button>

          {/* 页面序号 */}
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-medium text-sm">
            {index + 1}
          </div>

          {/* 内容区 */}
          <div className="flex-1 min-w-0">
            {isEditing ? (
              <div className="space-y-2">
                <Input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="页面标题"
                  className="text-sm"
                />
                <Textarea
                  value={points}
                  onChange={(e) => setPoints(e.target.value)}
                  placeholder="每行一个要点"
                  rows={3}
                  className="text-sm resize-none"
                />
                <div className="flex gap-2">
                  <Button size="sm" onClick={handleSave}>
                    保存
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setIsEditing(false)}
                  >
                    取消
                  </Button>
                </div>
              </div>
            ) : (
              <>
                <h3 className="font-medium text-gray-900 truncate">
                  {page.outline_content?.title || '未命名页面'}
                </h3>
                {page.outline_content?.points && page.outline_content.points.length > 0 && (
                  <ul className="mt-2 space-y-1">
                    {page.outline_content.points.slice(0, 3).map((point: string, idx: number) => (
                      <li key={idx} className="text-sm text-gray-600 truncate flex items-center gap-1">
                        <span className="w-1 h-1 rounded-full bg-gray-400 flex-shrink-0" />
                        {point}
                      </li>
                    ))}
                    {page.outline_content.points.length > 3 && (
                      <li className="text-sm text-gray-500">
                        还有 {page.outline_content.points.length - 3} 个要点...
                      </li>
                    )}
                  </ul>
                )}
                <div className="mt-2 flex items-center gap-2">
                  <StatusBadge status={page.status} />
                </div>
              </>
            )}
          </div>

          {/* 操作按钮 */}
          {!isEditing && (
            <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={() => setIsEditing(true)}
                className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                title="编辑"
              >
                <Wand2 className="w-4 h-4" />
              </button>
              <button
                onClick={() => {
                  if (confirm(`确定要删除"${page.outline_content?.title}"吗？`)) {
                    onDelete(page.id);
                  }
                }}
                className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                title="删除"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

export const OutlineEditor: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const {
    currentProject,
    isGlobalLoading,
    activeTaskId,
    taskProgress,
    error,
    syncProject,
    updatePageLocal,
    reorderPages,
    addNewPage,
    deletePageById,
    generateOutline,
    saveAllPages,
    setError,
  } = usePPTStore();

  const [isAiModalOpen, setIsAiModalOpen] = useState(false);
  const [aiPrompt, setAiPrompt] = useState('');
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  useEffect(() => {
    if (projectId) {
      syncProject(projectId);
    }
  }, [projectId]);

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id && currentProject) {
      const oldIndex = currentProject.pages.findIndex((p) => p.id === active.id);
      const newIndex = currentProject.pages.findIndex((p) => p.id === over.id);

      const newPages = arrayMove(currentProject.pages, oldIndex, newIndex);
      const newOrder = newPages.map((p) => p.id!);

      reorderPages(newOrder);
    }
  };

  const handleAiGenerate = async () => {
    if (!aiPrompt.trim()) {
      return;
    }

    setIsAiModalOpen(false);
    setError(null);

    try {
      // 如果用户提供了要求，使用 refineOutline API
      if (aiPrompt.trim()) {
        // 这里需要添加 refineOutline 功能
        // 暂时使用 generateOutline
        await generateOutline();
      } else {
        await generateOutline();
      }
      setAiPrompt('');
    } catch (err) {
      console.error('生成大纲失败:', err);
    }
  };

  const handleNextStep = () => {
    saveAllPages().then(() => {
      if (projectId) {
        navigate(`/ppt/detail/${projectId}`);
      }
    });
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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航栏 */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-3">
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
                onClick={() => navigate('/ppt')}
                className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg font-medium"
              >
                <span>1. 大纲编辑</span>
              </button>
              <ChevronRight className="w-4 h-4 text-gray-400" />
              <button
                onClick={handleNextStep}
                className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-600 rounded-lg font-medium hover:bg-gray-200 transition-colors"
                disabled={!hasPages}
              >
                <FileText className="w-4 h-4" />
                <span>2. 编辑描述</span>
              </button>
              <ChevronRight className="w-4 h-4 text-gray-400" />
              <button
                className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-600 rounded-lg font-medium opacity-50 cursor-not-allowed"
                disabled
              >
                <Eye className="w-4 h-4" />
                <span>3. 预览导出</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 主内容区 */}
      <div className="max-w-5xl mx-auto px-4 py-6">
        {/* 操作栏 */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Button
              onClick={() => setIsAiModalOpen(true)}
              icon={<Wand2 className="w-4 h-4" />}
              disabled={isGlobalLoading}
            >
              AI生成大纲
            </Button>
            <Button
              variant="secondary"
              onClick={addNewPage}
              icon={<Plus className="w-4 h-4" />}
            >
              添加页面
            </Button>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">
              {currentProject.pages?.length || 0} 页
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

        {/* 页面列表 */}
        {hasPages ? (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
          >
            <SortableContext
              items={currentProject.pages.map((p) => p.id!)}
              strategy={verticalListSortingStrategy}
            >
              <div className="space-y-3">
                {currentProject.pages.map((page, index) => (
                  <SortablePageCard
                    key={page.id}
                    page={page}
                    index={index}
                    onEdit={updatePageLocal}
                    onDelete={deletePageById}
                  />
                ))}
              </div>
            </SortableContext>
          </DndContext>
        ) : (
          <Card className="p-12 text-center">
            <div className="max-w-md mx-auto">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <FileText className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">还没有页面</h3>
              <p className="text-gray-600 mb-4">
                点击"AI生成大纲"让AI帮你创建大纲，或手动添加页面
              </p>
              <Button onClick={() => setIsAiModalOpen(true)} icon={<Wand2 className="w-4 h-4" />}>
                AI生成大纲
              </Button>
            </div>
          </Card>
        )}

        {/* 底部操作栏 */}
        {hasPages && (
          <div className="mt-6 flex items-center justify-center">
            <Button
              size="lg"
              onClick={handleNextStep}
              icon={<ChevronRight className="w-5 h-5" />}
            >
              下一步：编辑描述
            </Button>
          </div>
        )}
      </div>

      {/* AI生成大纲模态框 */}
      <Modal
        isOpen={isAiModalOpen}
        onClose={() => setIsAiModalOpen(false)}
        title="AI生成大纲"
        size="lg"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            输入您的想法，AI将根据您的想法生成PPT大纲。也可以留空直接生成。
          </p>
          <Textarea
            placeholder="例如：生成一个关于人工智能发展历程的PPT大纲，包含概述、历史、应用和未来展望..."
            value={aiPrompt}
            onChange={(e) => setAiPrompt(e.target.value)}
            rows={5}
          />
          <div className="flex justify-end gap-2">
            <Button
              variant="ghost"
              onClick={() => setIsAiModalOpen(false)}
            >
              取消
            </Button>
            <Button
              onClick={handleAiGenerate}
              loading={isGlobalLoading}
              icon={<Wand2 className="w-4 h-4" />}
            >
              开始生成
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
