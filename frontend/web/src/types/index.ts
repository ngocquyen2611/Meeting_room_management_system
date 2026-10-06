export type Role = 'EMPLOYEE' | 'ROOM_MANAGER' | 'ADMIN';

export type UserStatus = 'ACTIVE' | 'INACTIVE';

export interface User {
  id: string;
  auth0_user_id: string;
  email: string;
  name: string;
  role: Role;
  status: UserStatus;
  avatar?: string;
  created_at?: string;
}

export type RoomStatus = 'AVAILABLE' | 'MAINTENANCE' | 'DISABLED';

export interface Equipment {
  id: string;
  code: 'TV' | 'PROJECTOR' | 'CAMERA' | 'MIC' | 'WHITEBOARD';
  name: string;
  description?: string;
}

export interface RoomEquipment {
  equipment: Equipment;
  quantity: number;
}

export interface Room {
  id: string;
  name: string;
  location: string;
  capacity: number;
  status: RoomStatus;
  image_url: string;
  notes?: string;
  equipments: RoomEquipment[];
}

export type MeetingType = 'OFFLINE' | 'ONLINE' | 'HYBRID';

export type BookingStatus =
  | 'CONFIRMED'
  | 'CHECKED_IN'
  | 'CANCELLED'
  | 'AUTO_CANCELLED'
  | 'COMPLETED';

export interface Attendee {
  user_id: string;
  user?: User;
  status: 'INVITED' | 'ACCEPTED' | 'DECLINED';
  responded_at?: string;
}

export interface Booking {
  id: string;
  room_id: string;
  room?: Room;
  organizer_id: string;
  organizer?: User;
  title: string;
  description?: string;
  start_time: string; // ISO string
  end_time: string;   // ISO string
  meeting_type: MeetingType;
  meeting_link?: string;
  status: BookingStatus;
  checked_in_at?: string;
  cancellation_reason?: string;
  version: number;
  attendees: Attendee[];
  created_at: string;
}

export interface AppNotification {
  id: string;
  user_id: string;
  type: 'BOOKING_CREATED' | 'BOOKING_CANCELLED' | 'AUTO_CANCELLED' | 'REMINDER';
  title: string;
  content: string;
  is_read: boolean;
  created_at: string;
}
