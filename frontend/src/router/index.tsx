import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { Settings } from '@/pages/Settings';
import { ChatApp } from '@/pages/Chat';

const router = createBrowserRouter([
  {
    path: '/',
    element: <ChatApp />,
  },
  {
    path: '/settings',
    element: <Settings />,
  },
]);

export const AppRouter: React.FC = () => {
  return <RouterProvider router={router} />;
};

export default router;
