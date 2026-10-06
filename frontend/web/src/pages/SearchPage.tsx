import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  TextField,
  Button,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Divider,
  Alert,
  Chip,
  Snackbar,
} from '@mui/material';
import {
  Search as SearchIcon,
  EventAvailable as AvailableIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import type { Room } from '../types';
import { useAuth } from '../context/AuthContext';
import { RoomCard } from '../components/RoomCard';
import { BookingDialog } from '../components/BookingDialog';

export const SearchPage: React.FC = () => {
  const { rooms, bookings } = useAuth();

  const defaultDate = new Date().toISOString().split('T')[0];
  const [date, setDate] = useState(defaultDate);
  const [startTime, setStartTime] = useState('14:00');
  const [endTime, setEndTime] = useState('16:00');
  const [minCapacity, setMinCapacity] = useState<number>(8);
  const [selectedLocation, setSelectedLocation] = useState('');
  const [selectedEquipments, setSelectedEquipments] = useState<string[]>(['TV']);

  const [hasSearched, setHasSearched] = useState(false);
  const [searchResults, setSearchResults] = useState<Room[]>([]);
  const [bookingRoom, setBookingRoom] = useState<Room | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);

  const handleEquipmentToggle = (code: string) => {
    setSelectedEquipments((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    );
  };

  const handleSearch = () => {
    setHasSearched(true);

    const slotStart = new Date(`${date}T${startTime}:00Z`).getTime();
    const slotEnd = new Date(`${date}T${endTime}:00Z`).getTime();

    const conflictingRoomIds = new Set<string>();
    bookings.forEach((b) => {
      if (b.status === 'CONFIRMED' || b.status === 'CHECKED_IN') {
        const bStart = new Date(b.start_time).getTime();
        const bEnd = new Date(b.end_time).getTime();
        if (slotStart < bEnd && slotEnd > bStart) {
          conflictingRoomIds.add(b.room_id);
        }
      }
    });

    const results = rooms.filter((room) => {
      if (room.status !== 'AVAILABLE') return false;
      if (conflictingRoomIds.has(room.id)) return false;
      if (minCapacity && room.capacity < minCapacity) return false;
      if (selectedLocation && !room.location.toLowerCase().includes(selectedLocation.toLowerCase())) {
        return false;
      }
      if (selectedEquipments.length > 0) {
        const roomEquipCodes = room.equipments.map((e) => e.equipment.code);
        const hasAll = selectedEquipments.every((code) => roomEquipCodes.includes(code as any));
        if (!hasAll) return false;
      }
      return true;
    });

    setSearchResults(results);
  };

  const handleOpenBooking = (room: Room) => {
    setBookingRoom(room);
    setIsDialogOpen(true);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 700 }}>
          Tìm kiếm phòng họp khả dụng (FR-03)
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Kiểm tra lịch trống theo ngày, khung giờ và danh sách thiết bị yêu cầu.
        </Typography>
      </Box>

      {/* Search Filter Form */}
      <Paper sx={{ p: 3, mb: 4, borderRadius: 3 }}>
        <Typography variant="subtitle1" gutterBottom color="primary.main" sx={{ fontWeight: 700 }}>
          THÔNG SỐ TÌM KIẾM
        </Typography>
        <Divider sx={{ mb: 2.5 }} />

        <Grid container spacing={2.5}>
          {/* Date */}
          <Grid size={{ xs: 12, sm: 4 }}>
            <TextField
              fullWidth
              label="Ngày họp *"
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              slotProps={{ inputLabel: { shrink: true } }}
            />
          </Grid>

          {/* Start Time */}
          <Grid size={{ xs: 6, sm: 4 }}>
            <TextField
              fullWidth
              label="Giờ bắt đầu *"
              type="time"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              slotProps={{ inputLabel: { shrink: true } }}
            />
          </Grid>

          {/* End Time */}
          <Grid size={{ xs: 6, sm: 4 }}>
            <TextField
              fullWidth
              label="Giờ kết thúc *"
              type="time"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              slotProps={{ inputLabel: { shrink: true } }}
            />
          </Grid>

          {/* Capacity */}
          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth
              label="Sức chứa tối thiểu (người)"
              type="number"
              value={minCapacity}
              onChange={(e) => setMinCapacity(parseInt(e.target.value, 10) || 1)}
            />
          </Grid>

          {/* Location */}
          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth
              label="Vị trí / Tòa nhà mong muốn"
              placeholder="VD: Tòa Nhà A"
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
            />
          </Grid>

          {/* Equipments checkbox */}
          <Grid size={{ xs: 12 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom sx={{ fontWeight: 600 }}>
              Thiết bị bắt buộc phải có:
            </Typography>
            <FormGroup row sx={{ gap: 1 }}>
              {[
                { code: 'TV', label: 'Smart TV' },
                { code: 'PROJECTOR', label: 'Máy chiếu' },
                { code: 'CAMERA', label: 'Webcam họp' },
                { code: 'MIC', label: 'Micro hội nghị' },
                { code: 'WHITEBOARD', label: 'Bảng trắng' },
              ].map((item) => (
                <FormControlLabel
                  key={item.code}
                  control={
                    <Checkbox
                      checked={selectedEquipments.includes(item.code)}
                      onChange={() => handleEquipmentToggle(item.code)}
                      color="secondary"
                    />
                  }
                  label={item.label}
                />
              ))}
            </FormGroup>
          </Grid>

          {/* Submit Search */}
          <Grid size={{ xs: 12 }}>
            <Button
              variant="contained"
              size="large"
              color="primary"
              startIcon={<SearchIcon />}
              onClick={handleSearch}
              sx={{ px: 4, py: 1.2 }}
            >
              Kiểm tra phòng còn trống
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Results Section */}
      {hasSearched && (
        <Box sx={{ mt: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
            <AvailableIcon color="success" />
            <Typography variant="h5" sx={{ fontWeight: 700 }}>
              Kết quả: {searchResults.length} phòng khả dụng
            </Typography>
            <Chip
              icon={<ScheduleIcon />}
              label={`${date} | ${startTime} - ${endTime}`}
              color="info"
              variant="outlined"
            />
          </Box>

          {searchResults.length === 0 ? (
            <Alert severity="warning" sx={{ p: 2.5, borderRadius: 2 }}>
              Không có phòng nào còn trống hoặc thỏa mãn toàn bộ tiêu chí trong khung giờ đã chọn.
              Vui lòng thử chọn khung giờ khác hoặc giảm bớt yêu cầu thiết bị.
            </Alert>
          ) : (
            <Grid container spacing={3}>
              {searchResults.map((room) => (
                <Grid key={room.id} size={{ xs: 12, sm: 6, md: 4 }}>
                  <RoomCard room={room} onBook={handleOpenBooking} />
                </Grid>
              ))}
            </Grid>
          )}
        </Box>
      )}

      {/* Booking Dialog Modal */}
      <BookingDialog
        open={isDialogOpen}
        room={bookingRoom}
        onClose={() => setIsDialogOpen(false)}
        onSuccess={() => setSnackbarOpen(true)}
      />

      <Snackbar
        open={snackbarOpen}
        autoHideDuration={4000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity="success" variant="filled">
          Đặt phòng thành công!
        </Alert>
      </Snackbar>
    </Container>
  );
};
