import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Alert,
} from '@mui/material';
import type { Booking } from '../types';

interface CancelDialogProps {
  open: boolean;
  booking: Booking | null;
  onClose: () => void;
  onConfirm: (bookingId: string, reason: string) => void;
}

export const CancelDialog: React.FC<CancelDialogProps> = ({
  open,
  booking,
  onClose,
  onConfirm,
}) => {
  const [reason, setReason] = useState('');

  if (!booking) return null;

  const handleConfirm = () => {
    onConfirm(booking.id, reason.trim() || 'Người dùng hủy');
    setReason('');
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth slotProps={{ paper: { sx: { borderRadius: 3 } } }}>
      <DialogTitle sx={{ fontWeight: 700, color: 'error.main' }}>
        Xác nhận hủy cuộc họp?
      </DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Bạn có chắc chắn muốn hủy cuộc họp: <strong>"{booking.title}"</strong> không?
        </Typography>
        <Alert severity="warning" sx={{ my: 1.5, fontSize: '0.85rem' }}>
          Phòng sẽ được giải phóng ngay lập tức trên hệ thống cho các nhân viên khác đặt.
        </Alert>
        <TextField
          fullWidth
          multiline
          rows={2}
          label="Lý do hủy (không bắt buộc)"
          placeholder="VD: Dời lịch sang tuần sau, đối tác bận..."
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          sx={{ mt: 1 }}
        />
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} color="inherit">
          Giữ lại lịch
        </Button>
        <Button onClick={handleConfirm} variant="contained" color="error">
          Xác nhận hủy
        </Button>
      </DialogActions>
    </Dialog>
  );
};
