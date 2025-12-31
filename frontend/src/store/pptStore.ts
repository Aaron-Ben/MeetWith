import { create } from 'zustand';
import type { Project } from '@/types/ppt';
import * as api from '@/api/endpoints';
import { normalizeProject, normalizeErrorMessage } from '@/utils/ppt';

interface ProjectState {
  // 状态
  currentProject: Project | null;
  isGlobalLoading: boolean;
  activeTaskId: string | null;
  taskProgress: { total: number; completed: number } | null;
  error: string | null;
  pageGeneratingTasks: Record<string, string>;
  pageDescriptionGeneratingTasks: Record<string, boolean>;
  updatePageApi: (projectId: string, pageId: string, data: any) => Promise<void>;

  // Actions
  setCurrentProject: (project: Project | null) => void;
  setGlobalLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;

  // 项目操作
  initializeProject: (type: 'idea' | 'outline' | 'description', content: string, templateImage?: File, templateStyle?: string) => Promise<void>;
  syncProject: (projectId?: string) => Promise<void>;

  // 页面操作
  updatePageLocal: (pageId: string, data: any) => void;
  saveAllPages: () => Promise<void>;
  reorderPages: (newOrder: string[]) => Promise<void>;
  addNewPage: () => Promise<void>;
  deletePageById: (pageId: string) => Promise<void>;

  // 异步任务
  startAsyncTask: (apiCall: () => Promise<any>) => Promise<void>;
  pollTask: (taskId: string) => Promise<void>;
  pollPageTask: (pageId: string, taskId: string) => Promise<void>;

  // 生成操作
  generateOutline: () => Promise<void>;
  generateFromDescription: () => Promise<void>;
  generateDescriptions: () => Promise<void>;
  generatePageDescription: (pageId: string) => Promise<void>;
  generateImages: () => Promise<void>;
  generatePageImage: (pageId: string, forceRegenerate?: boolean) => Promise<void>;
  editPageImage: (
    pageId: string,
    editPrompt: string,
    contextImages?: {
      useTemplate?: boolean;
      descImageUrls?: string[];
      uploadedFiles?: File[];
    }
  ) => Promise<void>;

  // 导出
  exportPPTX: () => Promise<void>;
  exportPDF: () => Promise<void>;
}

export const usePPTStore = create<ProjectState>((set, get) => {


  return {
    // 初始状态
    currentProject: null,
    isGlobalLoading: false,
    activeTaskId: null,
    taskProgress: null,
    error: null,
    pageGeneratingTasks: {},
    pageDescriptionGeneratingTasks: {},

    // Setters
    setCurrentProject: (project) => set({ currentProject: project }),
    setGlobalLoading: (loading) => set({ isGlobalLoading: loading }),
    setError: (error) => set({ error }),

    // 初始化项目
    initializeProject: async (type, content, templateImage, templateStyle) => {
      set({ isGlobalLoading: true, error: null });
      try {
        const request: any = {};

        if (type === 'idea') {
          request.idea_prompt = content;
        } else if (type === 'outline') {
          request.outline_text = content;
        } else if (type === 'description') {
          request.description_text = content;
        }

        if (templateStyle && templateStyle.trim()) {
          request.template_style = templateStyle.trim();
        }

        const response = await api.createProject(request);
        const projectId = response.data?.project_id;

        if (!projectId) {
          throw new Error('项目创建失败：未返回项目ID');
        }

        if (templateImage) {
          try {
            await api.uploadTemplate(projectId, templateImage);
          } catch (error) {
            console.warn('模板上传失败:', error);
          }
        }

        if (type === 'description') {
          try {
            await api.generateFromDescription(projectId, content);
          } catch (error) {
            console.error('从描述生成失败:', error);
          }
        }

        const projectResponse = await api.getProject(projectId);
        const project = normalizeProject(projectResponse.data);

        if (project) {
          set({ currentProject: project });
          localStorage.setItem('currentPPTProjectId', project.id!);
        }
      } catch (error: any) {
        set({ error: normalizeErrorMessage(error.message || '创建项目失败') });
        throw error;
      } finally {
        set({ isGlobalLoading: false });
      }
    },

    // 同步项目数据
    syncProject: async (projectId?: string) => {
      const { currentProject } = get();

      let targetProjectId = projectId;
      if (!targetProjectId) {
        if (currentProject?.id) {
          targetProjectId = currentProject.id;
        } else {
          targetProjectId = localStorage.getItem('currentPPTProjectId') || undefined;
        }
      }

      if (!targetProjectId) {
        console.warn('syncProject: 没有可用的项目ID');
        return;
      }

      try {
        const response = await api.getProject(targetProjectId);
        if (response.data) {
          const project = normalizeProject(response.data);
          set({ currentProject: project });
          localStorage.setItem('currentPPTProjectId', project.id!);
        }
      } catch (error: any) {
        let errorMessage = '同步项目失败';
        let shouldClearStorage = false;

        if (error.response) {
          if (error.response.status === 404) {
            errorMessage = '项目不存在，可能已被删除';
            shouldClearStorage = true;
          } else if (error.response.data?.error?.message) {
            errorMessage = error.response.data.error.message;
          } else if (error.response.data?.message) {
            errorMessage = error.response.data.message;
          }
        } else if (error.message) {
          errorMessage = error.message;
        }

        if (shouldClearStorage) {
          localStorage.removeItem('currentPPTProjectId');
          set({ currentProject: null, error: normalizeErrorMessage(errorMessage) });
        } else {
          set({ error: normalizeErrorMessage(errorMessage) });
        }
      }
    },

    updatePageApi: async (projectId, pageId, data) => {
      try {
        if (data.description_content) {
          await api.updatePageDescription(projectId, pageId, data.description_content);
        } else if (data.outline_content) {
          await api.updatePageOutline(projectId, pageId, data.outline_content);
        } else {
          await api.updatePage(projectId, pageId, data);
        }

        await get().syncProject(projectId);
      } catch (error: any) {
        console.error('保存页面失败:', error);
        set({ error: normalizeErrorMessage(error.message || '保存页面失败') });
      }
    },

    // 本地更新页面（乐观更新）
    updatePageLocal: (pageId, data) => {
      const { currentProject } = get();
      if (!currentProject?.id) return;

      const updatedPages = currentProject.pages.map((page) =>
        page.id === pageId ? { ...page, ...data } : page
      );

      set({
        currentProject: {
          ...currentProject,
          pages: updatedPages,
        },
      });

    },

    // 保存所有页面
    saveAllPages: async () => {
      const { currentProject } = get();
      if (!currentProject?.id) return;

      await new Promise((resolver) => setTimeout(resolver, 1500));
      await get().syncProject(currentProject.id);
    },

    // 重新排序页面
    reorderPages: async (newOrder) => {
      const { currentProject } = get();
      if (!currentProject?.id) return;

      const reorderedPages = newOrder
        .map((id) => currentProject.pages.find((p) => p.id === id))
        .filter(Boolean) as any[];

      set({
        currentProject: {
          ...currentProject,
          pages: reorderedPages,
        },
      });

      try {
        await api.updatePagesOrder(currentProject.id, newOrder);
      } catch (error: any) {
        set({ error: error.message || '更新顺序失败' });
        await get().syncProject();
      }
    },

    // 添加新页面
    addNewPage: async () => {
      const { currentProject } = get();
      if (!currentProject?.id) return;

      try {
        const newPage = {
          outline_content: { title: '新页面', points: [] },
          order_index: currentProject.pages.length,
        };

        const response = await api.addPage(currentProject.id, newPage);
        if (response.data) {
          await get().syncProject();
        }
      } catch (error: any) {
        set({ error: error.message || '添加页面失败' });
      }
    },

    // 删除页面
    deletePageById: async (pageId) => {
      const { currentProject } = get();
      if (!currentProject?.id) return;

      try {
        await api.deletePage(currentProject.id, pageId);
        await get().syncProject();
      } catch (error: any) {
        set({ error: error.message || '删除页面失败' });
      }
    },

    // 启动异步任务
    startAsyncTask: async (apiCall) => {
      set({ isGlobalLoading: true, error: null });
      try {
        const response = await apiCall();
        const taskId = response.data?.task_id;
        if (taskId) {
          set({ activeTaskId: taskId });
          await get().pollTask(taskId);
        } else {
          await get().syncProject();
          set({ isGlobalLoading: false });
        }
      } catch (error: any) {
        set({ error: error.message || '任务启动失败', isGlobalLoading: false });
        throw error;
      }
    },

    // 轮询任务状态
    pollTask: async (taskId) => {
      const { currentProject } = get();
      if (!currentProject) return;

      const poll = async () => {
        try {
          const response = await api.getTaskStatus(currentProject.id!, taskId);
          const task = response.data;

          if (!task) return;

          if (task.progress) {
            set({ taskProgress: task.progress });
          }

          if (task.status === 'COMPLETED') {
            set({
              activeTaskId: null,
              taskProgress: null,
              isGlobalLoading: false
            });
            await get().syncProject();
          } else if (task.status === 'FAILED') {
            set({
              error: normalizeErrorMessage(task.error_message || task.error || '任务失败'),
              activeTaskId: null,
              taskProgress: null,
              isGlobalLoading: false
            });
          } else if (task.status === 'PENDING' || task.status === 'RUNNING') {
            setTimeout(poll, 2000);
          }
        } catch (error: any) {
          set({
            error: normalizeErrorMessage(error.message || '任务查询失败'),
            activeTaskId: null,
            taskProgress: null,
            isGlobalLoading: false
          });
        }
      };

      await poll();
    },

    // 生成大纲
    generateOutline: async () => {
      const { currentProject } = get();
      if (!currentProject?.id) return;

      set({ isGlobalLoading: true, error: null });
      try {
        await api.generateOutline(currentProject.id);
        await get().syncProject();
      } catch (error: any) {
        set({ error: error.message || '生成大纲失败' });
        throw error;
      } finally {
        set({ isGlobalLoading: false });
      }
    },

    // 从描述生成
    generateFromDescription: async () => {
      const { currentProject } = get();
      if (!currentProject?.id) return;

      set({ isGlobalLoading: true, error: null });
      try {
        await api.generateFromDescription(currentProject.id);
        await get().syncProject();
      } catch (error: any) {
        set({ error: error.message || '生成失败' });
        throw error;
      } finally {
        set({ isGlobalLoading: false });
      }
    },

    // 生成描述
    generateDescriptions: async () => {
      const { currentProject } = get();
      if (!currentProject?.id) return;

      const pages = currentProject.pages.filter((p) => p.id);
      if (pages.length === 0) return;

      set({ error: null });

      const initialTasks: Record<string, boolean> = {};
      pages.forEach((page) => {
        if (page.id) {
          initialTasks[page.id] = true;
        }
      });
      set({ pageDescriptionGeneratingTasks: initialTasks });

      try {
        const projectId = currentProject.id;
        const response = await api.generateDescriptions(projectId);
        const taskId = response.data?.task_id;

        if (!taskId) {
          throw new Error('未收到任务ID');
        }

        const pollAndSync = async () => {
          try {
            const taskResponse = await api.getTaskStatus(projectId, taskId);
            const task = taskResponse.data;

            if (task) {
              if (task.progress) {
                set({ taskProgress: task.progress });
              }

              await get().syncProject();

              const { currentProject: updatedProject } = get();
              if (updatedProject) {
                const updatedTasks: Record<string, boolean> = {};
                updatedProject.pages.forEach((page) => {
                  if (page.id) {
                    const hasDescription = !!page.description_content;
                    const isGenerating = page.status === 'GENERATING' ||
                      (!hasDescription && initialTasks[page.id]);
                    if (isGenerating) {
                      updatedTasks[page.id] = true;
                    }
                  }
                });
                set({ pageDescriptionGeneratingTasks: updatedTasks });
              }

              if (task.status === 'COMPLETED') {
                set({
                  pageDescriptionGeneratingTasks: {},
                  taskProgress: null,
                  activeTaskId: null
                });
                await get().syncProject();
              } else if (task.status === 'FAILED') {
                set({
                  pageDescriptionGeneratingTasks: {},
                  taskProgress: null,
                  activeTaskId: null,
                  error: normalizeErrorMessage(task.error_message || task.error || '生成描述失败')
                });
              } else if (task.status === 'PENDING' || task.status === 'RUNNING') {
                setTimeout(pollAndSync, 2000);
              }
            }
          } catch (error: any) {
            await get().syncProject();
            setTimeout(pollAndSync, 2000);
          }
        };

        setTimeout(pollAndSync, 2000);

      } catch (error: any) {
        set({
          pageDescriptionGeneratingTasks: {},
          error: normalizeErrorMessage(error.message || '启动生成任务失败')
        });
        throw error;
      }
    },

    // 生成单页描述
    generatePageDescription: async (pageId: string) => {
      const { currentProject, pageDescriptionGeneratingTasks } = get();
      if (!currentProject?.id) return;

      if (pageDescriptionGeneratingTasks[pageId]) {
        return;
      }

      set({ error: null });

      set({
        pageDescriptionGeneratingTasks: {
          ...pageDescriptionGeneratingTasks,
          [pageId]: true,
        },
      });

      try {
        await get().syncProject();
        await api.generatePageDescription(currentProject.id, pageId, true);
        await get().syncProject();
      } catch (error: any) {
        set({ error: normalizeErrorMessage(error.message || '生成描述失败') });
        throw error;
      } finally {
        const { pageDescriptionGeneratingTasks: currentTasks } = get();
        const newTasks = { ...currentTasks };
        delete newTasks[pageId];
        set({ pageDescriptionGeneratingTasks: newTasks });
      }
    },

    // 生成单页图片
    generatePageImage: async (pageId, forceRegenerate = false) => {
      const { currentProject, pageGeneratingTasks } = get();
      if (!currentProject?.id) return;

      if (pageGeneratingTasks[pageId]) {
        return;
      }

      set({ error: null });
      try {
        const response = await api.generatePageImage(currentProject.id, pageId, forceRegenerate);
        const taskId = response.data?.task_id;

        if (taskId) {
          set({
            pageGeneratingTasks: { ...pageGeneratingTasks, [pageId]: taskId }
          });

          await get().syncProject();
          await get().pollPageTask(pageId, taskId);
        } else {
          await get().syncProject();
        }
      } catch (error: any) {
        const { pageGeneratingTasks } = get();
        const newTasks = { ...pageGeneratingTasks };
        delete newTasks[pageId];
        set({ pageGeneratingTasks: newTasks, error: normalizeErrorMessage(error.message || '生成图片失败') });
        throw error;
      }
    },

    // 生成图片
    generateImages: async () => {
      const { currentProject, startAsyncTask } = get();
      if (!currentProject?.id) return;

      await startAsyncTask(() => api.generateImages(currentProject.id!));
    },

    // 轮询单个页面的任务状态
    pollPageTask: async (pageId: string, taskId: string) => {
      const { currentProject } = get();
      if (!currentProject) return;

      const poll = async () => {
        try {
          const response = await api.getTaskStatus(currentProject.id!, taskId);
          const task = response.data;

          if (!task) return;

          if (task.status === 'COMPLETED') {
            const { pageGeneratingTasks } = get();
            const newTasks = { ...pageGeneratingTasks };
            delete newTasks[pageId];
            set({ pageGeneratingTasks: newTasks });
            await get().syncProject();
          } else if (task.status === 'FAILED') {
            const { pageGeneratingTasks } = get();
            const newTasks = { ...pageGeneratingTasks };
            delete newTasks[pageId];
            set({
              pageGeneratingTasks: newTasks,
              error: normalizeErrorMessage(task.error_message || task.error || '生成失败')
            });
            await get().syncProject();
          } else if (task.status === 'PENDING' || task.status === 'RUNNING') {
            await get().syncProject();
            setTimeout(poll, 2000);
          }
        } catch (error: any) {
          const { pageGeneratingTasks } = get();
          const newTasks = { ...pageGeneratingTasks };
          delete newTasks[pageId];
          set({ pageGeneratingTasks: newTasks });
        }
      };

      await poll();
    },

    // 编辑页面图片
    editPageImage: async (pageId, editPrompt, contextImages) => {
      const { currentProject, pageGeneratingTasks } = get();
      if (!currentProject?.id) return;

      if (pageGeneratingTasks[pageId]) {
        return;
      }

      set({ error: null });
      try {
        const response = await api.editPageImage(currentProject.id, pageId, editPrompt, contextImages);
        const taskId = response.data?.task_id;

        if (taskId) {
          set({
            pageGeneratingTasks: { ...pageGeneratingTasks, [pageId]: taskId }
          });

          await get().syncProject();
          await get().pollPageTask(pageId, taskId);
        } else {
          await get().syncProject();
        }
      } catch (error: any) {
        const { pageGeneratingTasks } = get();
        const newTasks = { ...pageGeneratingTasks };
        delete newTasks[pageId];
        set({ pageGeneratingTasks: newTasks, error: normalizeErrorMessage(error.message || '编辑图片失败') });
        throw error;
      }
    },

    // 导出PPTX
    exportPPTX: async () => {
      const { currentProject } = get();
      if (!currentProject?.id) return;

      set({ isGlobalLoading: true, error: null });
      try {
        const response = await api.exportPPTX(currentProject.id);
        const downloadUrl =
          response.data?.download_url || response.data?.download_url_absolute;

        if (!downloadUrl) {
          throw new Error('导出链接获取失败');
        }

        window.open(downloadUrl, '_blank');
      } catch (error: any) {
        set({ error: error.message || '导出失败' });
      } finally {
        set({ isGlobalLoading: false });
      }
    },

    // 导出PDF
    exportPDF: async () => {
      const { currentProject } = get();
      if (!currentProject?.id) return;

      set({ isGlobalLoading: true, error: null });
      try {
        const response = await api.exportPDF(currentProject.id);
        const downloadUrl =
          response.data?.download_url || response.data?.download_url_absolute;

        if (!downloadUrl) {
          throw new Error('导出链接获取失败');
        }

        window.open(downloadUrl, '_blank');
      } catch (error: any) {
        set({ error: error.message || '导出失败' });
      } finally {
        set({ isGlobalLoading: false });
      }
    },
  };
});
