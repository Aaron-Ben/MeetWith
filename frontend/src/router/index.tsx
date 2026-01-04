import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { Settings } from '@/pages/Settings';
import { ChatApp } from '@/pages/Chat';

// 懒加载 PPT 相关页面
const PPTHome = lazy(() => import('@/pages/PPT/Home').then(m => ({ default: m.PPTHome })));
const OutlineEditor = lazy(() => import('@/pages/PPT/OutlineEditor').then(m => ({ default: m.OutlineEditor })));
const DetailEditor = lazy(() => import('@/pages/PPT/DetailEditor').then(m => ({ default: m.DetailEditor })));
const Preview = lazy(() => import('@/pages/PPT/Preview').then(m => ({ default: m.Preview })));

// 加载中组件
const LoadingFallback = () => (
  <div className="h-screen flex items-center justify-center">
    <div className="text-gray-600">加载中...</div>
  </div>
);

const router = createBrowserRouter([
  {
    path: '/',
    element: <ChatApp />,
  },
  {
    path: '/settings',
    element: <Settings />,
  },
  {
    path: '/ppt',
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <PPTHome />
      </Suspense>
    ),
  },
  {
    path: '/ppt/outline/:projectId',
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <OutlineEditor />
      </Suspense>
    ),
  },
  {
    path: '/ppt/detail/:projectId',
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <DetailEditor />
      </Suspense>
    ),
  },
  {
    path: '/ppt/preview/:projectId',
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <Preview />
      </Suspense>
    ),
  },
]);

export const AppRouter: React.FC = () => {
  return <RouterProvider router={router} />;
};

export default router;
