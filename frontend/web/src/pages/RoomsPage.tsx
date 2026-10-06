import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Grid,
  TextField,
  InputAdornment,
  MenuItem,
  Snackbar,
  Alert,
  Paper,
  Button,
} from '@mui/material';
import {
  Search as SearchIcon,
  CalendarMonth as CalendarIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import type { Room } from '../types';
import { useAuth } from '../context/AuthContext';
import { RoomCard } from '../components/RoomCard';
import { BookingDialog } from '../components/BookingDialog';

export const RoomsPage: React.FC = () => {
  const navigate = useNavigate();
  const { rooms } = useAuth();

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLocation, setSelectedLocation] = useState('ALL');
  const [minCapacity, setMinCapacity] = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState('ALL');

  const [bookingRoom, setBookingRoom] = useState<Room | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);

  const handleOpenBooking = (room: Room) => {
    setBookingRoom(room);
    setIsDialogOpen(true);
  };

  const handleBookingSuccess = () => {
    setSnackbarOpen(true);
  };

  const filteredRooms = rooms.filter((r) => {
    const matchQuery =
      r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.location.toLowerCase().includes(searchQuery.toLowerCase());
    const matchLocation =
      selectedLocation === 'ALL' || r.location.includes(selectedLocation);
    const matchCapacity =
      minCapacity === 'ALL' || r.capacity >= parseInt(minCapacity, 10);
    const matchStatus = selectedStatus === 'ALL' || r.status === selectedStatus;

    return matchQuery && matchLocation && matchCapacity && matchStatus;
  });

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header Banner */}
      <Box
        sx={{
          mb: 4,
          display: 'flex',
          flexDirection: { xs: 'column', md: 'row' },
          justifyContent: 'space-between',
          alignItems: { xs: 'flex-start', md: 'center' },
          gap: 2,
        }}
      >
        <Box>
          <Typography variant="h4" gutterBottom sx={{ fontWeight: 700 }}>
            Danh sách phòng họp
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Tìm kiếm không gian làm việc và đặt lịch hội họp nhanh chóng, hiện đại.
          </Typography>
        </Box>
        <Button
          variant="contained"
          color="secondary"
          startIcon={<CalendarIcon />}
          onClick={() => navigate('/search')}
          sx={{ whiteSpace: 'nowrap' }}
        >
          Tìm phòng theo giờ trống
        </Button>
      </Box>

      {/* Filter Toolbar */}
      <Paper sx={{ p: 2.5, mb: 4, borderRadius: 3 }}>
        <Grid container spacing={2} sx={{ alignItems: 'center' }}>
          {/* Search by text */}
          <Grid size={{ xs: 12, md: 4 }}>
            <TextField
              fullWidth
              size="small"
              placeholder="Tìm theo tên phòng hoặc vị trí..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon color="action" />
                    </InputAdornment>
                  ),
                },
              }}
            />
          </Grid>

          {/* Location filter */}
          <Grid size={{ xs: 6, sm: 4, md: 2.5 }}>
            <TextField
              fullWidth
              size="small"
              select
              label="Tòa nhà / Vị trí"
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
            >
              <MenuItem value="ALL">Tất cả vị trí</MenuItem>
              <MenuItem value="Tòa Nhà A">Tòa Nhà A</MenuItem>
              <MenuItem value="Tòa Nhà B">Tòa Nhà B</MenuItem>
            </TextField>
          </Grid>

          {/* Min Capacity */}
          <Grid size={{ xs: 6, sm: 4, md: 2.5 }}>
            <TextField
              fullWidth
              size="small"
              select
              label="Sức chứa tối thiểu"
              value={minCapacity}
              onChange={(e) => setMinCapacity(e.target.value)}
            >
              <MenuItem value="ALL">Tất cả sức chứa</MenuItem>
              <MenuItem value="6">Từ 6 người</MenuItem>
              <MenuItem value="10">Từ 10 người</MenuItem>
              <MenuItem value="20">Từ 20 người</MenuItem>
            </TextField>
          </Grid>

          {/* Status filter */}
          <Grid size={{ xs: 12, sm: 4, md: 3 }}>
            <TextField
              fullWidth
              size="small"
              select
              label="Trạng thái"
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
            >
              <MenuItem value="ALL">Tất cả trạng thái</MenuItem>
              <MenuItem value="AVAILABLE">Sẵn sàng (Available)</MenuItem>
              <MenuItem value="MAINTENANCE">Đang bảo trì</MenuItem>
            </TextField>
          </Grid>
        </Grid>
      </Paper>

      {/* Room Grid */}
      {filteredRooms.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary">
            Không tìm thấy phòng họp phù hợp với bộ lọc.
          </Typography>
        </Box>
      ) : (
        <Grid container spacing={3}>
          {filteredRooms.map((room) => (
            <Grid key={room.id} size={{ xs: 12, sm: 6, md: 4 }}>
              <RoomCard room={room} onBook={handleOpenBooking} />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Booking Dialog Modal */}
      <BookingDialog
        open={isDialogOpen}
        room={bookingRoom}
        onClose={() => setIsDialogOpen(false)}
        onSuccess={handleBookingSuccess}
      />

      {/* Success Notification */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={4000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity="success" variant="filled" sx={{ width: '100%' }}>
          Đặt phòng thành công! Lịch họp đã được lưu vào danh sách của bạn.
        </Alert>
      </Snackbar>
    </Container>
  );
};
