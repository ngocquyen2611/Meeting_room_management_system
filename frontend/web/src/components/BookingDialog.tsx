import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Grid,
  MenuItem,
  Typography,
  Box,
  Alert,
  Chip,
  OutlinedInput,
  Select,
  FormControl,
  InputLabel,
} from '@mui/material';
import type { SelectChangeEvent } from '@mui/material';
import {
  MeetingRoom as MeetingRoomIcon,
  People as PeopleIcon,
} from '@mui/icons-material';
import type { MeetingType, Room } from '../types';
import { useAuth } from '../context/AuthContext';

interface BookingDialogProps {
  open: boolean;
  room: Room | null;
  onClose: () => void;
  onSuccess: () => void;
}

export const BookingDialog: React.FC<BookingDialogProps> = ({
  open,
  room,
  onClose,
  onSuccess,
}) => {
  const { currentUser, users, addBooking } = useAuth();

  const defaultDate = new Date().toISOString().split('T')[0];
  const [date, setDate] = useState(defaultDate);
  const [startTime, setStartTime] = useState('09:00');
  const [endTime, setEndTime] = useState('10:00');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [meetingType, setMeetingType] = useState<MeetingType>('OFFLINE');
  const [meetingLink, setMeetingLink] = useState('');
  const [selectedAttendeeIds, setSelectedAttendeeIds] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  if (!room) return null;

  const handleAttendeeChange = (event: SelectChangeEvent<string[]>) => {
    const value = event.target.value;
    setSelectedAttendeeIds(typeof value === 'string' ? value.split(',') : value);
  };

  const handleSubmit = () => {
    setError(null);

    if (!title.trim()) {
      setError('Vui lòng nhập tiêu đề cuộc họp.');
      return;
    }

    if (endTime <= startTime) {
      setError('Thời gian kết thúc phải sau thời gian bắt đầu.');
      return;
    }

    const totalPeople = 1 + selectedAttendeeIds.length;
    if (totalPeople > room.capacity) {
      setError(
        `Vượt quá sức chứa phòng! Phòng này tối đa ${room.capacity} chỗ, nhưng bạn đang mời ${totalPeople} người.`
      );
      return;
    }

    const startDateTime = new Date(`${date}T${startTime}:00Z`).toISOString();
    const endDateTime = new Date(`${date}T${endTime}:00Z`).toISOString();

    addBooking({
      room_id: room.id,
      room,
      organizer_id: currentUser?.id || 'u-1',
      organizer: currentUser || undefined,
      title: title.trim(),
      description: description.trim() || undefined,
      start_time: startDateTime,
      end_time: endDateTime,
      meeting_type: meetingType,
      meeting_link: meetingType !== 'OFFLINE' ? meetingLink.trim() : undefined,
      attendees: selectedAttendeeIds.map((uid) => ({
        user_id: uid,
        user: users.find((u) => u.id === uid),
        status: 'INVITED',
      })),
    });

    setTitle('');
    setDescription('');
    setSelectedAttendeeIds([]);
    setMeetingLink('');
    onSuccess();
    onClose();
  };

  const otherUsers = users.filter((u) => u.id !== currentUser?.id);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth slotProps={{ paper: { sx: { borderRadius: 3 } } }}>
      <DialogTitle sx={{ pb: 1 }}>
        <Typography variant="h6" sx={{ fontWeight: 700 }}>
          Đặt phòng họp
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5, color: 'text.secondary' }}>
          <MeetingRoomIcon fontSize="small" color="primary" />
          <Typography variant="body2" color="text.primary" sx={{ fontWeight: 600 }}>
            {room.name}
          </Typography>
          <span>•</span>
          <PeopleIcon fontSize="small" />
          <Typography variant="body2">Tối đa {room.capacity} người</Typography>
        </Box>
      </DialogTitle>

      <DialogContent dividers sx={{ pt: 2 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Grid container spacing={2}>
          <Grid size={{ xs: 12 }}>
            <TextField
              fullWidth
              label="Tiêu đề cuộc họp *"
              placeholder="VD: Họp báo cáo tiến độ tuần"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </Grid>

          <Grid size={{ xs: 12, sm: 4 }}>
            <TextField
              fullWidth
              label="Ngày họp"
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              slotProps={{ inputLabel: { shrink: true } }}
            />
          </Grid>

          <Grid size={{ xs: 6, sm: 4 }}>
            <TextField
              fullWidth
              label="Bắt đầu"
              type="time"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              slotProps={{ inputLabel: { shrink: true } }}
            />
          </Grid>

          <Grid size={{ xs: 6, sm: 4 }}>
            <TextField
              fullWidth
              label="Kết thúc"
              type="time"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              slotProps={{ inputLabel: { shrink: true } }}
            />
          </Grid>

          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth
              select
              label="Hình thức cuộc họp"
              value={meetingType}
              onChange={(e) => setMeetingType(e.target.value as MeetingType)}
            >
              <MenuItem value="OFFLINE">Trực tiếp tại phòng (Offline)</MenuItem>
              <MenuItem value="ONLINE">Trực tuyến (Online)</MenuItem>
              <MenuItem value="HYBRID">Kết hợp (Hybrid)</MenuItem>
            </TextField>
          </Grid>

          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth
              label="Link phòng họp online"
              placeholder="Google Meet / Zoom link"
              disabled={meetingType === 'OFFLINE'}
              value={meetingLink}
              onChange={(e) => setMeetingLink(e.target.value)}
            />
          </Grid>

          <Grid size={{ xs: 12 }}>
            <FormControl fullWidth>
              <InputLabel id="attendees-label">Mời thành viên tham dự</InputLabel>
              <Select
                labelId="attendees-label"
                multiple
                value={selectedAttendeeIds}
                onChange={handleAttendeeChange}
                input={<OutlinedInput label="Mời thành viên tham dự" />}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map((val) => {
                      const u = users.find((item) => item.id === val);
                      return <Chip key={val} label={u?.name || val} size="small" />;
                    })}
                  </Box>
                )}
              >
                {otherUsers.map((user) => (
                  <MenuItem key={user.id} value={user.id}>
                    {user.name} ({user.email})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid size={{ xs: 12 }}>
            <TextField
              fullWidth
              multiline
              rows={2}
              label="Nội dung / Ghi chú cuộc họp"
              placeholder="Chương trình nghị sự hoặc tài liệu chuẩn bị..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </Grid>
        </Grid>
      </DialogContent>

      <DialogActions sx={{ p: 2.5 }}>
        <Button onClick={onClose} color="inherit">
          Hủy bỏ
        </Button>
        <Button onClick={handleSubmit} variant="contained" color="primary">
          Xác nhận đặt phòng
        </Button>
      </DialogActions>
    </Dialog>
  );
};
