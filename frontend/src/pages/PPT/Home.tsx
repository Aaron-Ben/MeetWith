import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, FileText, List, Home, History } from 'lucide-react';
import { usePPTStore } from '@/store/pptStore';
import { Button } from '@/components/ppt/ui';
import { Input, Textarea } from '@/components/ppt/ui';

type CreationMode = 'idea' | 'outline' | 'description';
type TabType = 'create' | 'history';

const TABS = [
  { id: 'create' as TabType, label: '创建项目', icon: Sparkles },
  { id: 'history' as TabType, label: '历史项目', icon: History },
];

const CREATION_MODES = [
  {
    id: 'idea' as CreationMode,
    title: '从想法开始',
    description: '输入一个想法，AI将自动生成PPT大纲',
    icon: Sparkles,
    placeholder: '例如：制作一个关于人工智能发展历程的演示文稿',
    inputLabel: '你的想法',
  },
  {
    id: 'outline' as CreationMode,
    title: '从大纲开始',
    description: '提供PPT大纲结构，AI将按大纲生成内容',
    icon: List,
    placeholder: '例如：\n1. 人工智能概述\n2. 发展历程\n3. 应用领域\n4. 未来展望',
    inputLabel: 'PPT大纲',
  },
  {
    id: 'description' as CreationMode,
    title: '从描述开始',
    description: '提供详细的内容描述，AI将生成完整的PPT',
    icon: FileText,
    placeholder: '例如：第一页介绍人工智能的定义和背景，第二页讲述AI的发展历史...',
    inputLabel: '内容描述',
  },
];

export const PPTHome: React.FC = () => {
  const navigate = useNavigate();
  const { initializeProject, isGlobalLoading, error } = usePPTStore();

  const [activeTab, setActiveTab] = useState<TabType>('create');
  const [creationMode, setCreationMode] = useState<CreationMode>('idea');
  const [inputValue, setInputValue] = useState('');
  const [templateStyle, setTemplateStyle] = useState('');
  const [templateImage, setTemplateImage] = useState<File | null>(null);

  const currentMode = CREATION_MODES.find((m) => m.id === creationMode)!;

  const handleCreateProject = async () => {
    if (!inputValue.trim()) {
      return;
    }

    try {
      await initializeProject(
        creationMode,
        inputValue.trim(),
        templateImage || undefined,
        templateStyle.trim() || undefined
      );

      const projectId = localStorage.getItem('currentPPTProjectId');
      if (projectId) {
        navigate(`/ppt/outline/${projectId}`);
      }
    } catch (err) {
      console.error('创建项目失败:', err);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setTemplateImage(file);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* 顶部导航 */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div
              className="flex items-center gap-2 cursor-pointer"
              onClick={() => navigate('/')}
            >
              <Home className="w-5 h-5 text-blue-500" />
              <span className="text-xl font-bold text-gray-900">AI PPT</span>
            </div>

            <div className="flex gap-1">
              {TABS.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                      activeTab === tab.id
                        ? 'bg-blue-500 text-white'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {tab.label}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* 主内容区 */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        {activeTab === 'create' ? (
          <div className="space-y-6">
            {/* 标题 */}
            <div className="text-center">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">创建AI演示文稿</h1>
              <p className="text-gray-600">选择一种方式开始创建您的PPT</p>
            </div>

            {/* 创建模式选择 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {CREATION_MODES.map((mode) => {
                const Icon = mode.icon;
                return (
                  <button
                    key={mode.id}
                    onClick={() => setCreationMode(mode.id)}
                    className={`p-4 rounded-xl border-2 text-left transition-all ${
                      creationMode === mode.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300 bg-white'
                    }`}
                  >
                    <Icon className={`w-6 h-6 mb-2 ${
                      creationMode === mode.id ? 'text-blue-500' : 'text-gray-500'
                    }`} />
                    <h3 className="font-semibold text-gray-900 mb-1">{mode.title}</h3>
                    <p className="text-sm text-gray-600">{mode.description}</p>
                  </button>
                );
              })}
            </div>

            {/* 输入区域 */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4">
              <Textarea
                label={currentMode.inputLabel}
                placeholder={currentMode.placeholder}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                rows={8}
                className="resize-none"
              />

              {/* 风格设置 */}
              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-700">
                  风格设置（可选）
                </label>
                <Input
                  placeholder="例如：简约商务风格、蓝色调、现代科技感..."
                  value={templateStyle}
                  onChange={(e) => setTemplateStyle(e.target.value)}
                />
                <div className="flex items-center gap-2">
                  <label className="text-sm text-gray-600">或上传模板图片：</label>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleFileChange}
                    className="text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                  />
                  {templateImage && (
                    <span className="text-sm text-green-600">{templateImage.name}</span>
                  )}
                </div>
              </div>

              {/* 错误提示 */}
              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
                  {error}
                </div>
              )}

              {/* 创建按钮 */}
              <Button
                onClick={handleCreateProject}
                loading={isGlobalLoading}
                disabled={!inputValue.trim()}
                className="w-full"
                size="lg"
              >
                <Sparkles className="w-5 h-5" />
                开始生成
              </Button>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
            <div className="text-center py-12">
              <History className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-gray-900 mb-2">历史项目</h2>
              <p className="text-gray-600">此功能正在开发中</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
