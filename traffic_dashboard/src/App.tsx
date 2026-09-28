import React from 'react';
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import DashboardLayout from './layouts/DashboardLayout';
import DashboardOverview from './pages/DashboardOverview';
import IntersectionAnalytics from './pages/IntersectionAnalytics';
import HardwareStatus from './pages/HardwareStatus';
import ProtectedRoute from './components/ProtectedRoute'; 

const router = createBrowserRouter([
  { path: "/", element: <LandingPage /> },
  { path: "/login", element: <LoginPage /> },
  {
    // Bọc ProtectedRoute ở ngoài cùng của nhóm /dashboard
    element: <ProtectedRoute />,
    children: [
      {
        path: "/dashboard",
        element: <DashboardLayout />,
        children: [
          { index: true, element: <DashboardOverview /> },
          
          // Tự động chuyển hướng về ngã tư 1 nếu truy cập link cũ không có ID
          { path: "intersection", element: <Navigate to="/dashboard/intersection/1" replace /> },
          
          // Cấu hình đường dẫn động (Dynamic Route) nhận tham số :id cho 3 ngã tư
          { path: "intersection/:id", element: <IntersectionAnalytics /> },
          
          { path: "system", element: <HardwareStatus /> },
        ]
      }
    ]
  }
]);

const App: React.FC = () => {
  return <RouterProvider router={router} />;
};

export default App;