import React from 'react';
import {
  Container,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  CheckCircleOutlined as CheckCircleIcon,
  CancelOutlined as CancelIcon,
  TimerOff as TimerOffIcon,
  Star as StarIcon,
  AccessTime as AccessTimeIcon,
} from '@mui/icons-material';
import { useAuth } from '../../context/AuthContext';

export const ReportsPage: React.FC = () => {
  const { bookings, rooms, role } = useAuth();

  // RBAC Guard
  if (role !== 'ADMIN') {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Alert severity="error" sx={{ p: 3, borderRadius: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            Truy cập bị từ chối (403 Forbidden)
          </Typography>
          Trang báo cáo thống kê chỉ dành cho tài khoản <strong>ADMIN</strong>. Vui lòng chuyển vai
          trò sang ADMIN ở góc trên bên phải màn hình để thử nghiệm.
        </Alert>
      </Container>
    );
  }

  // Calculate statistics from bookings
  const totalBookings = bookings.length;
  const checkedInBookings = bookings.filter((b) => b.status === 'CHECKED_IN').length;
  const cancelledBookings = bookings.filter((b) => b.status === 'CANCELLED').length;
  const autoCancelledBookings = bookings.filter((b) => b.status === 'AUTO_CANCELLED').length;
  const confirmedBookings = bookings.filter((b) => b.status === 'CONFIRMED').length;

  // Utilization by room
  const roomUsageCount: Record<string, number> = {};
  rooms.forEach((r) => {
    roomUsageCount[r.id] = 0;
  });
  bookings.forEach((b) => {
    if (b.status !== 'CANCELLED') {
      roomUsageCount[b.room_id] = (roomUsageCount[b.room_id] || 0) + 1;
    }
  });

  const roomStats = rooms.map((room) => {
    const count = roomUsageCount[room.id] || 0;
    const rate = totalBookings > 0 ? Math.round((count / totalBookings) * 100) : 0;
    return {
      ...room,
      usageCount: count,
      utilizationRate: rate,
    };
  }).sort((a, b) => b.usageCount - a.usageCount);

  const topRoom = roomStats[0] || null;

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 700 }}>
          Báo cáo & Thống kê hệ thống (FR-07)
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Phân tích tần suất sử dụng phòng họp, tỷ lệ check-in và hiệu suất khai thác tài nguyên doanh nghiệp.
        </Typography>
      </Box>

      {/* 4 Metric Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Total Bookings */}
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 600 }}>
                  TỔNG SỐ CUỘC HỌP
                </Typography>
                <TrendingUpIcon color="primary" />
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 800 }}>
                {totalBookings}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Đã đặt: {confirmedBookings} sắp diễn ra
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Check-in Count */}
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 600 }}>
                  ĐÃ CHECK-IN
                </Typography>
                <CheckCircleIcon color="success" />
              </Box>
              <Typography variant="h4" color="success.main" sx={{ fontWeight: 800 }}>
                {checkedInBookings}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Tỷ lệ tuân thủ: {totalBookings > 0 ? Math.round((checkedInBookings / totalBookings) * 100) : 0}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Cancelled Count */}
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 600 }}>
                  LỊCH HỦY CHỦ ĐỘNG
                </Typography>
                <CancelIcon color="error" />
              </Box>
              <Typography variant="h4" color="error.main" sx={{ fontWeight: 800 }}>
                {cancelledBookings}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Giải phóng phòng thành công
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Auto Cancelled Count */}
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 600 }}>
                  TỰ ĐỘNG HỦY (QUÁ HẠN)
                </Typography>
                <TimerOffIcon color="warning" />
              </Box>
              <Typography variant="h4" color="warning.main" sx={{ fontWeight: 800 }}>
                {autoCancelledBookings}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Không check-in sau 15 phút
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Highlights: Top Room & Peak Hours */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 3, borderRadius: 3, height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <StarIcon color="warning" />
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                Phòng được sử dụng nhiều nhất
              </Typography>
            </Box>
            {topRoom ? (
              <Box sx={{ bgcolor: '#F8FAFC', p: 2.5, borderRadius: 2 }}>
                <Typography variant="h6" color="primary.main" sx={{ fontWeight: 700 }}>
                  {topRoom.name}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                  {topRoom.location} • Sức chứa {topRoom.capacity} người
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Chip label={`${topRoom.usageCount} lượt họp`} color="primary" sx={{ fontWeight: 600 }} />
                  <Typography variant="body2" color="text.secondary">
                    Chiếm {topRoom.utilizationRate}% tổng nhu cầu họp
                  </Typography>
                </Box>
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                Chưa có dữ liệu thống kê
              </Typography>
            )}
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 3, borderRadius: 3, height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <AccessTimeIcon color="info" />
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                Khung giờ cao điểm nhất
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    09:00 – 11:00 (Buổi sáng)
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Rất cao (65% công suất)
                  </Typography>
                </Box>
                <LinearProgress variant="determinate" value={65} color="primary" sx={{ height: 8, borderRadius: 4 }} />
              </Box>

              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    14:00 – 16:00 (Buổi chiều)
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Cao (50% công suất)
                  </Typography>
                </Box>
                <LinearProgress variant="determinate" value={50} color="secondary" sx={{ height: 8, borderRadius: 4 }} />
              </Box>

              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    16:00 – 18:00 (Cuối ngày)
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Trung bình (25% công suất)
                  </Typography>
                </Box>
                <LinearProgress variant="determinate" value={25} color="info" sx={{ height: 8, borderRadius: 4 }} />
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Utilization Rate by Room Table */}
      <Paper sx={{ p: 3, borderRadius: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ fontWeight: 700 }}>
          Tỷ lệ sử dụng của từng phòng họp
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Đánh giá mức độ hiệu quả phân bổ phòng theo sức chứa và vị trí.
        </Typography>

        <TableContainer>
          <Table>
            <TableHead sx={{ bgcolor: '#F8FAFC' }}>
              <TableRow>
                <TableCell sx={{ fontWeight: 700 }}>Phòng họp</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Vị trí</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Sức chứa</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Số lượt họp</TableCell>
                <TableCell sx={{ fontWeight: 700, width: '35%' }}>Tỷ lệ sử dụng</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {roomStats.map((item) => (
                <TableRow key={item.id} hover>
                  <TableCell sx={{ fontWeight: 600 }}>{item.name}</TableCell>
                  <TableCell>{item.location}</TableCell>
                  <TableCell>{item.capacity} người</TableCell>
                  <TableCell>{item.usageCount} cuộc họp</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Box sx={{ width: '100%', mr: 1 }}>
                        <LinearProgress
                          variant="determinate"
                          value={item.utilizationRate}
                          sx={{ height: 8, borderRadius: 4 }}
                        />
                      </Box>
                      <Box sx={{ minWidth: 35 }}>
                        <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 600 }}>
                          {item.utilizationRate}%
                        </Typography>
                      </Box>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Container>
  );
};
