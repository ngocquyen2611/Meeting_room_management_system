import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { ThemeProvider, CssBaseline, Box } from '@mui/material';
import { theme } from './theme';
import { AuthProvider } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { LoginPage } from './pages/LoginPage';
import { RoomsPage } from './pages/RoomsPage';
import { SearchPage } from './pages/SearchPage';
import { MyBookingsPage } from './pages/MyBookingsPage';
import { RoomManagementPage } from './pages/admin/RoomManagementPage';
import { UserManagementPage } from './pages/admin/UserManagementPage';
import { ReportsPage } from './pages/admin/ReportsPage';

const AppLayout: React.FC = () => {
  const location = useLocation();
  const isLoginPage = location.pathname === '/login';

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {!isLoginPage && <Navbar />}
      <Box component="main" sx={{ flexGrow: 1 }}>
        <Routes>
          <Route path="/" element={<Navigate to="/rooms" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/rooms" element={<RoomsPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/my-bookings" element={<MyBookingsPage />} />
          <Route path="/admin/rooms" element={<RoomManagementPage />} />
          <Route path="/admin/users" element={<UserManagementPage />} />
          <Route path="/admin/reports" element={<ReportsPage />} />
          <Route path="*" element={<Navigate to="/rooms" replace />} />
        </Routes>
      </Box>
    </Box>
  );
};

export const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <BrowserRouter>
          <AppLayout />
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
