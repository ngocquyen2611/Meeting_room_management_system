import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  MenuItem,
  Alert,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Build as BuildIcon,
  CheckCircle as AvailableIcon,
} from '@mui/icons-material';
import { useAuth } from '../../context/AuthContext';
import type { Room, RoomStatus } from '../../types';

export const RoomManagementPage: React.FC = () => {
  const { rooms, addRoom, updateRoom, deleteRoom, role } = useAuth();

  const [openAddDialog, setOpenAddDialog] = useState(false);
  const [name, setName] = useState('');
  const [location, setLocation] = useState('');
  const [capacity, setCapacity] = useState(10);
  const [imageUrl, setImageUrl] = useState('');
  const [status, setStatus] = useState<RoomStatus>('AVAILABLE');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState<string | null>(null);

  // RBAC Guard
  if (role !== 'ROOM_MANAGER' && role !== 'ADMIN') {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Alert severity="error" sx={{ p: 3, borderRadius: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            Truy cập bị từ chối (403 Forbidden)
          </Typography>
          Bạn không có quyền truy cập trang Quản lý phòng họp. Tính năng này chỉ dành cho{' '}
          <strong>ROOM_MANAGER</strong> hoặc <strong>ADMIN</strong>. Vui lòng chuyển vai trò ở góc
          phải màn hình để thử nghiệm.
        </Alert>
      </Container>
    );
  }

  const handleCreateRoom = () => {
    setError(null);
    if (!name.trim() || !location.trim()) {
      setError('Vui lòng điền đầy đủ tên phòng và vị trí.');
      return;
    }

    addRoom({
      name: name.trim(),
      location: location.trim(),
      capacity: Number(capacity) || 1,
      status,
      image_url:
        imageUrl.trim() ||
        'https://images.unsplash.com/photo-1497366216548-37526070297c?w=800',
      notes: notes.trim() || undefined,
      equipments: [],
    });

    setName('');
    setLocation('');
    setCapacity(10);
    setImageUrl('');
    setNotes('');
    setOpenAddDialog(false);
  };

  const handleToggleStatus = (room: Room) => {
    const nextStatus: RoomStatus =
      room.status === 'AVAILABLE' ? 'MAINTENANCE' : 'AVAILABLE';
    updateRoom(room.id, { status: nextStatus });
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom sx={{ fontWeight: 700 }}>
            Quản trị phòng họp (FR-02)
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Thêm mới, sửa đổi thông tin, chuyển chế độ bảo trì và quản lý thiết bị phòng họp.
          </Typography>
        </Box>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => setOpenAddDialog(true)}
        >
          Thêm phòng họp mới
        </Button>
      </Box>

      {/* Room Table */}
      <TableContainer component={Paper} sx={{ borderRadius: 3 }}>
        <Table>
          <TableHead sx={{ bgcolor: '#F8FAFC' }}>
            <TableRow>
              <TableCell sx={{ fontWeight: 700 }}>Tên phòng</TableCell>
              <TableCell sx={{ fontWeight: 700 }}>Vị trí</TableCell>
              <TableCell sx={{ fontWeight: 700 }}>Sức chứa</TableCell>
              <TableCell sx={{ fontWeight: 700 }}>Thiết bị</TableCell>
              <TableCell sx={{ fontWeight: 700 }}>Trạng thái</TableCell>
              <TableCell align="right" sx={{ fontWeight: 700 }}>Thao tác</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rooms.map((room) => (
              <TableRow key={room.id} hover>
                <TableCell>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                    {room.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {room.notes || 'Không có ghi chú'}
                  </Typography>
                </TableCell>
                <TableCell>{room.location}</TableCell>
                <TableCell>{room.capacity} người</TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    {room.equipments.map((e) => (
                      <Chip key={e.equipment.id} label={e.equipment.code} size="small" variant="outlined" />
                    ))}
                  </Box>
                </TableCell>
                <TableCell>
                  {room.status === 'AVAILABLE' ? (
                    <Chip label="Sẵn sàng" color="success" size="small" sx={{ fontWeight: 600 }} />
                  ) : room.status === 'MAINTENANCE' ? (
                    <Chip label="Bảo trì" color="warning" size="small" sx={{ fontWeight: 600 }} />
                  ) : (
                    <Chip label="Vô hiệu" size="small" />
                  )}
                </TableCell>
                <TableCell align="right">
                  <Tooltip title={room.status === 'AVAILABLE' ? 'Chuyển sang Bảo trì' : 'Chuyển sang Sẵn sàng'}>
                    <IconButton color={room.status === 'AVAILABLE' ? 'warning' : 'success'} onClick={() => handleToggleStatus(room)}>
                      {room.status === 'AVAILABLE' ? <BuildIcon /> : <AvailableIcon />}
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Xóa phòng (Soft Delete)">
                    <IconButton color="error" onClick={() => deleteRoom(room.id)}>
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Add Room Modal Dialog */}
      <Dialog open={openAddDialog} onClose={() => setOpenAddDialog(false)} maxWidth="sm" fullWidth slotProps={{ paper: { sx: { borderRadius: 3 } } }}>
        <DialogTitle sx={{ fontWeight: 700 }}>Thêm phòng họp mới</DialogTitle>
        <DialogContent dividers>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <Grid container spacing={2}>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Tên phòng họp *"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 8 }}>
              <TextField
                fullWidth
                label="Vị trí / Tầng *"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <TextField
                fullWidth
                label="Sức chứa *"
                type="number"
                value={capacity}
                onChange={(e) => setCapacity(Number(e.target.value))}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Link ảnh phòng họp (Image URL)"
                placeholder="https://..."
                value={imageUrl}
                onChange={(e) => setImageUrl(e.target.value)}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                select
                label="Trạng thái ban đầu"
                value={status}
                onChange={(e) => setStatus(e.target.value as RoomStatus)}
              >
                <MenuItem value="AVAILABLE">Sẵn sàng (Available)</MenuItem>
                <MenuItem value="MAINTENANCE">Bảo trì (Maintenance)</MenuItem>
                <MenuItem value="DISABLED">Vô hiệu hóa (Disabled)</MenuItem>
              </TextField>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Ghi chú thêm"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ p: 2.5 }}>
          <Button onClick={() => setOpenAddDialog(false)} color="inherit">
            Hủy
          </Button>
          <Button onClick={handleCreateRoom} variant="contained" color="primary">
            Lưu phòng họp
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};
