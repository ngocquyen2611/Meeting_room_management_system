import React from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  Divider,
  Stack,
  Alert,
} from '@mui/material';
import {
  MeetingRoom as MeetingRoomIcon,
  Security as SecurityIcon,
  Lock as LockIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleLogin = () => {
    login();
    navigate('/rooms');
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        bgcolor: '#F1F5F9',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2,
      }}
    >
      <Container maxWidth="xs">
        <Paper
          elevation={0}
          sx={{
            p: 4,
            borderRadius: 4,
            border: '1px solid #E2E8F0',
            textAlign: 'center',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01)',
          }}
        >
          {/* Logo */}
          <Box
            sx={{
              width: 56,
              height: 56,
              bgcolor: 'primary.main',
              color: 'white',
              borderRadius: 3,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mx: 'auto',
              mb: 2,
            }}
          >
            <MeetingRoomIcon sx={{ fontSize: 32 }} />
          </Box>

          <Typography variant="h5" color="primary.main" sx={{ fontWeight: 800 }}>
            MeetingHub
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, mb: 3 }}>
            Hệ thống Quản lý Đặt phòng họp Doanh nghiệp
          </Typography>

          <Alert severity="info" sx={{ textAlign: 'left', mb: 3, fontSize: '0.82rem' }}>
            Hệ thống áp dụng chuẩn bảo mật <strong>Auth0 Single Sign-On (SSO)</strong> và phân quyền
            RBAC đa cấp (Employee, Manager, Admin).
          </Alert>

          {/* Login Button */}
          <Button
            fullWidth
            size="large"
            variant="contained"
            color="primary"
            startIcon={<LockIcon />}
            onClick={handleLogin}
            sx={{ py: 1.4, mb: 2, fontSize: '0.95rem' }}
          >
            Đăng nhập với Auth0 SSO
          </Button>

          <Divider sx={{ my: 2.5 }}>
            <Typography variant="caption" color="text.secondary">
              BẢO MẬT DOANH NGHIỆP
            </Typography>
          </Divider>

          <Stack direction="row" spacing={1} sx={{ alignItems: 'center', justifyContent: 'center', color: 'text.secondary' }}>
            <SecurityIcon fontSize="small" color="action" />
            <Typography variant="caption">OAuth2 / OpenID Connect • RS256 JWT</Typography>
          </Stack>
        </Paper>
      </Container>
    </Box>
  );
};
