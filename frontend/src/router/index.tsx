import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { Settings } from '@/pages/Settings';
import VCPChat from '@/pages/VCPChat';

// 路由配置
const routes = [
  {
    path: '/',
    element: <VCPChat />,
  },
  {
    path: '/settings',
    element: <Settings />,
  },
];

const router = createBrowserRouter(routes);

export const AppRouter: React.FC = () => {
  return <RouterProvider router={router} />;
};

export default router;
export { routes };
