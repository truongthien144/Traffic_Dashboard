import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';

const ProtectedRoute: React.FC = () => {
    // Kiểm tra xem token có tồn tại trong localStorage không
    const isAuthenticated = !!localStorage.getItem('its_token');

    // Nếu có thì cho đi tiếp (Outlet render DashboardLayout)
    // Nếu không có thì đá văng về trang login
    return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
};

export default ProtectedRoute;