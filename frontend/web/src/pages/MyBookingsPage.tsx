import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Tabs,
  Tab,
  Card,
  CardContent,
  Grid,
  Chip,
  Button,
  Stack,
  Snackbar,
  Alert,
  Tooltip,
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  Schedule as ScheduleIcon,
  LocationOn as LocationIcon,
  People as PeopleIcon,
  VideoCameraFront as VideoIcon,
  OpenInNew as OpenLinkIcon,
  MeetingRoom as RoomIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import type { Booking, BookingStatus } from '../types';
import { useAuth } from '../context/AuthContext';
import { CancelDialog } from '../components/CancelDialog';

export const MyBookingsPage: React.FC = () => {
  const { bookings, cancelBooking, checkinBooking } = useAuth();

  const [tabValue, setTabValue] = useState(0);
  const [selectedBookingForCancel, setSelectedBookingForCancel] = useState<Booking | null>(null);
  const [cancelModalOpen, setCancelModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const now = new Date().getTime();

  const upcomingBookings = bookings.filter((b) => {
    const isFuture = new Date(b.end_time).getTime() > now;
    return isFuture && b.status !== 'CANCELLED' && b.status !== 'AUTO_CANCELLED';
  });

  const displayedBookings = tabValue === 0 ? upcomingBookings : bookings;

  const handleCheckin = (bookingId: string) => {
    const success = checkinBooking(bookingId);
    if (success) {
      setToastMessage('Check-in thành công! Phòng họp đã chính thức kích hoạt.');
    }
  };

  const handleOpenCancel = (booking: Booking) => {
    setSelectedBookingForCancel(booking);
    setCancelModalOpen(true);
  };

  const handleConfirmCancel = (id: string, reason: string) => {
    cancelBooking(id, reason);
    setToastMessage('Đã hủy cuộc họp thành công. Phòng đã được giải phóng.');
  };

  const getStatusChip = (status: BookingStatus, reason?: string) => {
    switch (status) {
      case 'CHECKED_IN':
        return (
          <Chip
            icon={<CheckIcon fontSize="small" />}
            label="ĐÃ CHECK-IN"
            color="success"
            size="small"
            sx={{ fontWeight: 700 }}
          />
        );
      case 'CONFIRMED':
        return (
          <Chip
            icon={<ScheduleIcon fontSize="small" />}
            label="ĐÃ XÁC NHẬN"
            color="primary"
            size="small"
            sx={{ fontWeight: 700 }}
          />
        );
      case 'CANCELLED':
        return (
          <Tooltip title={`Lý do: ${reason || 'Không có'}`}>
            <Chip
              icon={<CancelIcon fontSize="small" />}
              label="ĐÃ HỦY"
              color="error"
              variant="outlined"
              size="small"
              sx={{ fontWeight: 700 }}
            />
          </Tooltip>
        );
      case 'AUTO_CANCELLED':
        return (
          <Tooltip title="Tự động hủy do không check-in trong vòng 15 phút">
            <Chip
              icon={<InfoIcon fontSize="small" />}
              label="TỰ ĐỘNG HỦY (QUÁ HẠN)"
              color="warning"
              variant="outlined"
              size="small"
              sx={{ fontWeight: 700 }}
            />
          </Tooltip>
        );
      default:
        return <Chip label={status} size="small" />;
    }
  };

  const formatDateTime = (isoString: string) => {
    const d = new Date(isoString);
    return `${d.toLocaleDateString('vi-VN')} lúc ${d.toLocaleTimeString('vi-VN', {
      hour: '2-digit',
      minute: '2-digit',
    })}`;
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 700 }}>
          Lịch họp của tôi
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Theo dõi các cuộc họp đã đăng ký, thực hiện check-in hoặc hủy lịch khi cần thiết.
        </Typography>
      </Box>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={(_, newVal) => setTabValue(newVal)}>
          <Tab label={`Sắp tới (${upcomingBookings.length})`} sx={{ fontWeight: 600 }} />
          <Tab label={`Toàn bộ lịch sử (${bookings.length})`} sx={{ fontWeight: 600 }} />
        </Tabs>
      </Box>

      {/* Booking List */}
      {displayedBookings.length === 0 ? (
        <Card sx={{ p: 5, textAlign: 'center', bgcolor: '#F8FAFC' }}>
          <Typography variant="h6" color="text.secondary">
            {tabValue === 0
              ? 'Bạn không có cuộc họp nào sắp tới.'
              : 'Chưa có lịch sử đặt phòng họp nào.'}
          </Typography>
        </Card>
      ) : (
        <Stack spacing={2.5}>
          {displayedBookings.map((item) => {
            const isConfirmed = item.status === 'CONFIRMED';
            return (
              <Card key={item.id} sx={{ p: 1 }}>
                <CardContent>
                  <Grid container spacing={2} sx={{ alignItems: 'center' }}>
                    {/* Time & Room Info */}
                    <Grid size={{ xs: 12, md: 8 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1, flexWrap: 'wrap' }}>
                        {getStatusChip(item.status, item.cancellation_reason)}
                        <Chip
                          label={item.meeting_type}
                          size="small"
                          variant="filled"
                          color={item.meeting_type === 'ONLINE' ? 'secondary' : 'default'}
                          sx={{ fontWeight: 600 }}
                        />
                        <Typography variant="caption" color="text.secondary">
                          Tạo lúc: {formatDateTime(item.created_at)}
                        </Typography>
                      </Box>

                      <Typography variant="h6" gutterBottom sx={{ fontWeight: 700 }}>
                        {item.title}
                      </Typography>

                      {item.description && (
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                          {item.description}
                        </Typography>
                      )}

                      <Stack direction="row" spacing={3} sx={{ flexWrap: 'wrap', color: 'text.secondary', fontSize: '0.9rem' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <ScheduleIcon fontSize="small" color="primary" />
                          <span>
                            {formatDateTime(item.start_time)} –{' '}
                            {new Date(item.end_time).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </Box>

                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <RoomIcon fontSize="small" color="primary" />
                          <span>{item.room?.name || 'Phòng họp'}</span>
                        </Box>

                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <LocationIcon fontSize="small" color="action" />
                          <span>{item.room?.location}</span>
                        </Box>

                        {item.attendees.length > 0 && (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <PeopleIcon fontSize="small" color="action" />
                            <span>{item.attendees.length} khách mời</span>
                          </Box>
                        )}
                      </Stack>

                      {/* Online meeting link */}
                      {item.meeting_link && (
                        <Box sx={{ mt: 1.5 }}>
                          <Button
                            size="small"
                            variant="text"
                            color="secondary"
                            startIcon={<VideoIcon />}
                            endIcon={<OpenLinkIcon />}
                            href={item.meeting_link}
                            target="_blank"
                            sx={{ p: 0 }}
                          >
                            Tham gia họp trực tuyến ({item.meeting_link})
                          </Button>
                        </Box>
                      )}
                    </Grid>

                    {/* Action buttons */}
                    <Grid size={{ xs: 12, md: 4 }} sx={{ display: 'flex', justifyContent: { xs: 'flex-start', md: 'flex-end' }, gap: 1.5 }}>
                      {/* Check-in button */}
                      {isConfirmed && (
                        <Button
                          variant="contained"
                          color="success"
                          startIcon={<CheckIcon />}
                          onClick={() => handleCheckin(item.id)}
                          sx={{ whiteSpace: 'nowrap' }}
                        >
                          Check-in ngay
                        </Button>
                      )}

                      {/* Cancel button */}
                      {isConfirmed && (
                        <Button
                          variant="outlined"
                          color="error"
                          startIcon={<CancelIcon />}
                          onClick={() => handleOpenCancel(item)}
                          sx={{ whiteSpace: 'nowrap' }}
                        >
                          Hủy lịch
                        </Button>
                      )}
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            );
          })}
        </Stack>
      )}

      {/* Cancel Modal */}
      <CancelDialog
        open={cancelModalOpen}
        booking={selectedBookingForCancel}
        onClose={() => setCancelModalOpen(false)}
        onConfirm={handleConfirmCancel}
      />

      {/* Notification Toast */}
      <Snackbar
        open={Boolean(toastMessage)}
        autoHideDuration={4000}
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
