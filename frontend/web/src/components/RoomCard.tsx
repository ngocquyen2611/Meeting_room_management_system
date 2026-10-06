import React from 'react';
import {
  Card,
  CardMedia,
  CardContent,
  CardActions,
  Typography,
  Box,
  Chip,
  Button,
  Stack,
  Tooltip,
} from '@mui/material';
import {
  People as PeopleIcon,
  LocationOn as LocationIcon,
  Tv as TvIcon,
  Videocam as CameraIcon,
  Mic as MicIcon,
  CoPresent as ProjectorIcon,
  Draw as WhiteboardIcon,
  EventAvailable as BookIcon,
  Build as BuildIcon,
} from '@mui/icons-material';
import type { Room } from '../types';

interface RoomCardProps {
  room: Room;
  onBook: (room: Room) => void;
}

export const RoomCard: React.FC<RoomCardProps> = ({ room, onBook }) => {
  const getStatusBadge = () => {
    switch (room.status) {
      case 'AVAILABLE':
        return <Chip label="Sẵn sàng" color="success" size="small" sx={{ fontWeight: 600 }} />;
      case 'MAINTENANCE':
        return <Chip label="Bảo trì" color="warning" size="small" icon={<BuildIcon fontSize="small" />} sx={{ fontWeight: 600 }} />;
      default:
        return <Chip label="Ngừng hoạt động" color="default" size="small" sx={{ fontWeight: 600 }} />;
    }
  };

  const getEquipmentIcon = (code: string) => {
    switch (code) {
      case 'TV':
        return <TvIcon fontSize="small" />;
      case 'PROJECTOR':
        return <ProjectorIcon fontSize="small" />;
      case 'CAMERA':
        return <CameraIcon fontSize="small" />;
      case 'MIC':
        return <MicIcon fontSize="small" />;
      case 'WHITEBOARD':
        return <WhiteboardIcon fontSize="small" />;
      default:
        return undefined;
    }
  };

  const isBookable = room.status === 'AVAILABLE';

  return (
    <Card sx={{ display: 'flex', flexDirection: 'column', height: '100%', position: 'relative' }}>
      {/* Room Photo */}
      <Box sx={{ position: 'relative' }}>
        <CardMedia
          component="img"
          height="190"
          image={room.image_url}
          alt={room.name}
          sx={{ objectFit: 'cover' }}
        />
        <Box sx={{ position: 'absolute', top: 12, right: 12 }}>
          {getStatusBadge()}
        </Box>
        <Box
          sx={{
            position: 'absolute',
            bottom: 12,
            left: 12,
            bgcolor: 'rgba(15, 23, 42, 0.75)',
            backdropFilter: 'blur(4px)',
            color: 'white',
            px: 1.5,
            py: 0.5,
            borderRadius: 2,
            display: 'flex',
            alignItems: 'center',
            gap: 0.5,
            fontSize: '0.85rem',
            fontWeight: 600,
          }}
        >
          <PeopleIcon sx={{ fontSize: 16 }} /> {room.capacity} chỗ ngồi
        </Box>
      </Box>

      {/* Room Details */}
      <CardContent sx={{ flexGrow: 1, pb: 1 }}>
        <Typography variant="h6" gutterBottom noWrap sx={{ fontWeight: 700 }}>
          {room.name}
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', color: 'text.secondary', mb: 1.5, gap: 0.5 }}>
          <LocationIcon fontSize="small" color="primary" />
          <Typography variant="body2">{room.location}</Typography>
        </Box>

        {room.notes && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2, lineClamp: 2, overflow: 'hidden' }}>
            {room.notes}
          </Typography>
        )}

        {/* Equipments chips */}
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5, fontWeight: 600 }}>
          THIẾT BỊ SẴN CÓ:
        </Typography>
        <Stack direction="row" sx={{ flexWrap: 'wrap', gap: 0.8 }}>
          {room.equipments.map((item) => (
            <Tooltip key={item.equipment.id} title={`${item.equipment.name} (x${item.quantity})`}>
              <Chip
                icon={getEquipmentIcon(item.equipment.code)}
                label={`${item.equipment.code}${item.quantity > 1 ? ` x${item.quantity}` : ''}`}
                size="small"
                variant="outlined"
                sx={{ fontSize: '0.75rem', bgcolor: '#F1F5F9' }}
              />
            </Tooltip>
          ))}
        </Stack>
      </CardContent>

      {/* Action button */}
      <CardActions sx={{ p: 2, pt: 0 }}>
        <Button
          fullWidth
          variant="contained"
          color="primary"
          startIcon={<BookIcon />}
          disabled={!isBookable}
          onClick={() => onBook(room)}
        >
          {isBookable ? 'Đặt phòng ngay' : 'Không thể đặt'}
        </Button>
      </CardActions>
    </Card>
  );
};
