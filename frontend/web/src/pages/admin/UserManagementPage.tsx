import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Avatar,
  Select,
  MenuItem,
  Switch,
  Alert,
  Snackbar,
} from '@mui/material';
import { useAuth } from '../../context/AuthContext';
import type { Role } from '../../types';

export const UserManagementPage: React.FC = () => {
  const { users, updateUserRole, updateUserStatus, role, currentUser } = useAuth();
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // RBAC Guard
  if (role !== 'ADMIN') {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Alert severity="error" sx={{ p: 3, borderRadius: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            Truy cập bị từ chối (403 Forbidden)
          </Typography>
          Bạn không có quyền quản trị người dùng. Tính năng này chỉ dành cho tài khoản có vai trò{' '}
          <strong>ADMIN</strong>. Vui lòng chuyển vai trò sang ADMIN ở góc trên bên phải màn hình để thử nghiệm.
        </Alert>
      </Container>
    );
  }

  const handleRoleChange = (userId: string, newRole: Role) => {
    updateUserRole(userId, newRole);
    setToastMessage(`Đã cập nhật vai trò người dùng thành ${newRole}.`);
  };

  const handleStatusToggle = (userId: string, currentStatus: 'ACTIVE' | 'INACTIVE') => {
    if (userId === currentUser?.id) {
      alert('Không thể tự vô hiệu hóa tài khoản của chính mình.');
      return;
    }
    const nextStatus = currentStatus === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE';
    updateUserStatus(userId, nextStatus);
    setToastMessage(`Đã chuyển trạng thái tài khoản thành ${nextStatus}.`);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 700 }}>
          Quản trị người dùng & Phân quyền (RBAC)
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Quản lý danh sách nhân viên công ty, phân quyền vai trò (Employee, Room Manager, Admin) và trạng thái tài khoản.
        </Typography>
      </Box>

      <TableContainer component={Paper} sx={{ borderRadius: 3 }}>
        <Table>
          <TableHead sx={{ bgcolor: '#F8FAFC' }}>
            <TableRow>
              <TableCell sx={{ fontWeight: 700 }}>Người dùng</TableCell>
              <TableCell sx={{ fontWeight: 700 }}>Email doanh nghiệp</TableCell>
              <TableCell sx={{ fontWeight: 700 }}>Auth0 Sub ID</TableCell>
              <TableCell sx={{ fontWeight: 700 }}>Vai trò (Role)</TableCell>
              <TableCell align="center" sx={{ fontWeight: 700 }}>Hoạt động</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((u) => {
              const isSelf = u.id === currentUser?.id;
              return (
                <TableRow key={u.id} hover>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                      <Avatar src={u.avatar} alt={u.name} />
                      <Box>
                        <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                          {u.name} {isSelf && '(Bạn)'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Ngày tạo: {new Date(u.created_at || '').toLocaleDateString('vi-VN')}
                        </Typography>
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>{u.email}</TableCell>
                  <TableCell>
                    <code>{u.auth0_user_id}</code>
                  </TableCell>
                  <TableCell>
                    <Select
                      size="small"
                      value={u.role}
                      onChange={(e) => handleRoleChange(u.id, e.target.value as Role)}
                      sx={{ minWidth: 160, fontWeight: 600 }}
                    >
                      <MenuItem value="EMPLOYEE">EMPLOYEE (Nhân viên)</MenuItem>
                      <MenuItem value="ROOM_MANAGER">ROOM_MANAGER (Quản lý)</MenuItem>
                      <MenuItem value="ADMIN">ADMIN (Quản trị viên)</MenuItem>
                    </Select>
                  </TableCell>
                  <TableCell align="center">
                    <Switch
                      checked={u.status === 'ACTIVE'}
                      disabled={isSelf}
                      color="success"
                      onChange={() => handleStatusToggle(u.id, u.status)}
                    />
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      <Snackbar
        open={Boolean(toastMessage)}
        autoHideDuration={3000}
        onClose={() => setToastMessage(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity="success" variant="filled">
          {toastMessage}
        </Alert>
      </Snackbar>
    </Container>
  );
};
