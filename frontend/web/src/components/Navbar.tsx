import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Container,
  Avatar,
  Menu,
  MenuItem,
  Chip,
  IconButton,
  Tooltip,
  Divider,
  ListItemIcon,
  Badge,
  Popover,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import {
  MeetingRoom as MeetingRoomIcon,
  Search as SearchIcon,
  EventNote as EventNoteIcon,
  AdminPanelSettings as AdminIcon,
  ManageAccounts as UsersIcon,
  BarChart as ReportsIcon,
  SwapHoriz as SwitchRoleIcon,
  Logout as LogoutIcon,
  Check as CheckIcon,
  Notifications as NotificationsIcon,
  DoneAll as DoneAllIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import type { Role } from '../types';

export const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    currentUser,
    role,
    setRole,
    logout,
    notifications,
    unreadNotificationCount,
    markAllNotificationsAsRead,
  } = useAuth();

  const [roleAnchorEl, setRoleAnchorEl] = useState<null | HTMLElement>(null);
  const [userAnchorEl, setUserAnchorEl] = useState<null | HTMLElement>(null);
  const [notifAnchorEl, setNotifAnchorEl] = useState<null | HTMLElement>(null);

  const handleOpenRoleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setRoleAnchorEl(event.currentTarget);
  };

  const handleCloseRoleMenu = () => {
    setRoleAnchorEl(null);
  };

  const handleSelectRole = (newRole: Role) => {
    setRole(newRole);
    handleCloseRoleMenu();
  };

  const getRoleBadgeColor = (r: Role) => {
    switch (r) {
      case 'ADMIN':
        return 'error';
      case 'ROOM_MANAGER':
        return 'warning';
      default:
        return 'primary';
    }
  };

  const isActive = (path: string) => location.pathname === path;

  return (
    <AppBar position="sticky" elevation={0}>
      <Container maxWidth="lg">
        <Toolbar disableGutters sx={{ minHeight: 68 }}>
          {/* Brand Logo */}
          <Box
            onClick={() => navigate('/rooms')}
            sx={{
              display: 'flex',
              alignItems: 'center',
              cursor: 'pointer',
              mr: 4,
            }}
          >
            <Box
              sx={{
                bgcolor: 'primary.main',
                color: 'white',
                p: 1,
                borderRadius: 2,
                display: 'flex',
                mr: 1.5,
              }}
            >
              <MeetingRoomIcon />
            </Box>
            <Typography variant="h6" color="primary.main" sx={{ fontWeight: 700 }}>
              MeetingHub
            </Typography>
          </Box>

          {/* Navigation Items */}
          <Box sx={{ flexGrow: 1, display: { xs: 'none', md: 'flex' }, gap: 1 }}>
            <Button
              color={isActive('/rooms') ? 'primary' : 'inherit'}
              variant={isActive('/rooms') ? 'outlined' : 'text'}
              startIcon={<MeetingRoomIcon />}
              onClick={() => navigate('/rooms')}
            >
              Phòng họp
            </Button>
            <Button
              color={isActive('/search') ? 'primary' : 'inherit'}
              variant={isActive('/search') ? 'outlined' : 'text'}
              startIcon={<SearchIcon />}
              onClick={() => navigate('/search')}
            >
              Tìm phòng
            </Button>
            <Button
              color={isActive('/my-bookings') ? 'primary' : 'inherit'}
              variant={isActive('/my-bookings') ? 'outlined' : 'text'}
              startIcon={<EventNoteIcon />}
              onClick={() => navigate('/my-bookings')}
            >
              Lịch của tôi
            </Button>

            {/* Room Manager & Admin route */}
            {(role === 'ROOM_MANAGER' || role === 'ADMIN') && (
              <Button
                color={isActive('/admin/rooms') ? 'primary' : 'inherit'}
                variant={isActive('/admin/rooms') ? 'outlined' : 'text'}
                startIcon={<AdminIcon />}
                onClick={() => navigate('/admin/rooms')}
              >
                Quản lý phòng
              </Button>
            )}

            {/* Admin only routes */}
            {role === 'ADMIN' && (
              <>
                <Button
                  color={isActive('/admin/users') ? 'primary' : 'inherit'}
                  variant={isActive('/admin/users') ? 'outlined' : 'text'}
                  startIcon={<UsersIcon />}
                  onClick={() => navigate('/admin/users')}
                >
                  Quản trị User
                </Button>
                <Button
                  color={isActive('/admin/reports') ? 'primary' : 'inherit'}
                  variant={isActive('/admin/reports') ? 'outlined' : 'text'}
                  startIcon={<ReportsIcon />}
                  onClick={() => navigate('/admin/reports')}
                >
                  Báo cáo
                </Button>
              </>
            )}
          </Box>

          {/* Role Switcher, Notification & User Profile */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {/* Quick Role Switcher Pill for Easy Testing */}
            <Tooltip title="Chuyển vai trò thử nghiệm giao diện (RBAC)">
              <Chip
                icon={<SwitchRoleIcon />}
                label={role}
                color={getRoleBadgeColor(role)}
                variant="filled"
                onClick={handleOpenRoleMenu}
                clickable
                sx={{ fontWeight: 600, px: 1 }}
              />
            </Tooltip>

            <Menu
              anchorEl={roleAnchorEl}
              open={Boolean(roleAnchorEl)}
              onClose={handleCloseRoleMenu}
              transformOrigin={{ horizontal: 'right', vertical: 'top' }}
              anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
            >
              <Typography variant="caption" sx={{ px: 2, py: 1, color: 'text.secondary', display: 'block' }}>
                CHỌN VAI TRÒ THỬ NGHIỆM:
              </Typography>
              <MenuItem onClick={() => handleSelectRole('EMPLOYEE')}>
                <ListItemIcon>{role === 'EMPLOYEE' && <CheckIcon fontSize="small" color="primary" />}</ListItemIcon>
                EMPLOYEE (Nhân viên)
              </MenuItem>
              <MenuItem onClick={() => handleSelectRole('ROOM_MANAGER')}>
                <ListItemIcon>{role === 'ROOM_MANAGER' && <CheckIcon fontSize="small" color="primary" />}</ListItemIcon>
                ROOM_MANAGER (Quản lý phòng)
              </MenuItem>
              <MenuItem onClick={() => handleSelectRole('ADMIN')}>
                <ListItemIcon>{role === 'ADMIN' && <CheckIcon fontSize="small" color="primary" />}</ListItemIcon>
                ADMIN (Quản trị viên)
              </MenuItem>
            </Menu>

            {/* Notification Bell (FR-06) */}
            <Tooltip title="Thông báo hệ thống">
              <IconButton onClick={(e) => setNotifAnchorEl(e.currentTarget)} color="inherit">
                <Badge badgeContent={unreadNotificationCount} color="error">
                  <NotificationsIcon />
                </Badge>
              </IconButton>
            </Tooltip>

            <Popover
              anchorEl={notifAnchorEl}
              open={Boolean(notifAnchorEl)}
              onClose={() => setNotifAnchorEl(null)}
              anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
              transformOrigin={{ vertical: 'top', horizontal: 'right' }}
              slotProps={{ paper: { sx: { width: 340, p: 1, borderRadius: 3 } } }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: 1 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                  Thông báo ({unreadNotificationCount} chưa đọc)
                </Typography>
                {unreadNotificationCount > 0 && (
                  <Button
                    size="small"
                    startIcon={<DoneAllIcon />}
                    onClick={markAllNotificationsAsRead}
                    sx={{ fontSize: '0.75rem' }}
                  >
                    Đọc tất cả
                  </Button>
                )}
              </Box>
              <Divider />
              <List sx={{ maxHeight: 300, overflow: 'auto' }}>
                {notifications.map((n) => (
                  <ListItem
                    key={n.id}
                    sx={{
                      bgcolor: n.is_read ? 'transparent' : '#EFF6FF',
                      borderRadius: 1,
                      mb: 0.5,
                      alignItems: 'flex-start',
                    }}
                  >
                    <ListItemText
                      primary={
                        <Typography variant="body2" sx={{ fontWeight: n.is_read ? 500 : 700 }}>
                          {n.title}
                        </Typography>
                      }
                      secondary={
                        <Typography variant="caption" color="text.secondary">
                          {n.content}
                        </Typography>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </Popover>

            {/* User Avatar Menu */}
            {currentUser && (
              <>
                <IconButton onClick={(e) => setUserAnchorEl(e.currentTarget)} sx={{ p: 0.5 }}>
                  <Avatar src={currentUser.avatar} alt={currentUser.name} sx={{ width: 38, height: 38 }} />
                </IconButton>
                <Menu
                  anchorEl={userAnchorEl}
                  open={Boolean(userAnchorEl)}
                  onClose={() => setUserAnchorEl(null)}
                  transformOrigin={{ horizontal: 'right', vertical: 'top' }}
                  anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
                >
                  <Box sx={{ px: 2, py: 1 }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                      {currentUser.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {currentUser.email}
                    </Typography>
                  </Box>
                  <Divider />
                  <MenuItem
                    onClick={() => {
                      setUserAnchorEl(null);
                      logout();
                      navigate('/login');
                    }}
                  >
                    <ListItemIcon>
                      <LogoutIcon fontSize="small" />
                    </ListItemIcon>
                    Đăng xuất
                  </MenuItem>
                </Menu>
              </>
            )}
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
};
