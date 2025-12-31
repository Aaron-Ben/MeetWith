import { StrictMode, Suspense } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import "./global.css";
import App from "./App.tsx";

// 使用 Suspense 懒加载组件
import { lazy } from "react";
const PPTHome = lazy(() => import("./pages/PPT/Home").then(m => ({ default: m.PPTHome })));
const OutlineEditor = lazy(() => import("./pages/PPT/OutlineEditor").then(m => ({ default: m.OutlineEditor })));
const DetailEditor = lazy(() => import("./pages/PPT/DetailEditor").then(m => ({ default: m.DetailEditor })));
const Preview = lazy(() => import("./pages/PPT/Preview").then(m => ({ default: m.Preview })));

// 加载中组件
const LoadingFallback = () => (
  <div className="h-screen flex items-center justify-center">
    <div className="text-gray-600">加载中...</div>
  </div>
);

// 创建路由配置
const router = createBrowserRouter([
  {
    path: "/ppt",
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <PPTHome />
      </Suspense>
    ),
  },
  {
    path: "/ppt/outline/:projectId",
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <OutlineEditor />
      </Suspense>
    ),
  },
  {
    path: "/ppt/detail/:projectId",
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <DetailEditor />
      </Suspense>
    ),
  },
  {
    path: "/ppt/preview/:projectId",
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <Preview />
      </Suspense>
    ),
  },
  {
    path: "*",
    element: <App />,
  },
]);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>
);
