import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { PPTHome } from '@/pages/PPT/Home';
import { OutlineEditor } from '@/pages/PPT/OutlineEditor';
import { DetailEditor } from '@/pages/PPT/DetailEditor';
import { Preview } from '@/pages/PPT/Preview';

// 导入原有组件 - 简单的占位符，因为实际路由需要配合App.tsx使用

const router = createBrowserRouter([
  {
    path: '/',
    element: <div>{/* 原有的App内容 */}</div>,
  },
  {
    path: '/ppt',
    element: <PPTHome />,
  },
  {
    path: '/ppt/outline/:projectId',
    element: <OutlineEditor />,
  },
  {
    path: '/ppt/detail/:projectId',
    element: <DetailEditor />,
  },
  {
    path: '/ppt/preview/:projectId',
    element: <Preview />,
  },
]);

export const AppRouter: React.FC = () => {
  return <RouterProvider router={router} />;
};

export default router;
