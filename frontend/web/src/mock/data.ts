import type { Equipment, Room, User, Booking, AppNotification } from '../types';

export const MOCK_USERS: User[] = [
  {
    id: 'u-1',
    auth0_user_id: 'auth0|employee-01',
    email: 'nhanvien@company.com',
    name: 'Nguyễn Văn An (Employee)',
    role: 'EMPLOYEE',
    status: 'ACTIVE',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150',
    created_at: '2026-01-15T08:00:00Z',
  },
  {
    id: 'u-2',
    auth0_user_id: 'auth0|manager-01',
    email: 'quanly@company.com',
    name: 'Trần Thị Bình (Room Manager)',
    role: 'ROOM_MANAGER',
    status: 'ACTIVE',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150',
    created_at: '2026-01-10T08:00:00Z',
  },
  {
    id: 'u-3',
    auth0_user_id: 'auth0|admin-01',
    email: 'admin@company.com',
    name: 'Lê Hoàng Cường (Administrator)',
    role: 'ADMIN',
    status: 'ACTIVE',
    avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150',
    created_at: '2026-01-01T08:00:00Z',
  },
  {
    id: 'u-4',
    auth0_user_id: 'auth0|employee-02',
    email: 'duy.pham@company.com',
    name: 'Phạm Quốc Duy',
    role: 'EMPLOYEE',
    status: 'ACTIVE',
    avatar: 'https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=150',
    created_at: '2026-02-01T08:00:00Z',
  },
];

export const MOCK_EQUIPMENTS: Equipment[] = [
  { id: 'eq-1', code: 'TV', name: 'Smart TV 65"', description: 'Màn hình 4K HDR hỗ trợ AirPlay & Miracast' },
  { id: 'eq-2', code: 'PROJECTOR', name: 'Máy chiếu Epson 4K', description: 'Máy chiếu độ sáng cao cho phòng họp lớn' },
  { id: 'eq-3', code: 'CAMERA', name: 'Webcam Hội Nghị 360', description: 'Logitech MeetUp HD camera góc rộng' },
  { id: 'eq-4', code: 'MIC', name: 'Micro Hội Nghị Đa Hướng', description: 'Micro lọc ồn phòng họp bán kính 5m' },
  { id: 'eq-5', code: 'WHITEBOARD', name: 'Bảng Trắng Từ Tính', description: 'Bảng viết bút lông có từ tính kèm bút viết' },
];

export const MOCK_ROOMS: Room[] = [
  {
    id: 'room-1',
    name: 'Phòng Hội Nghị Thăng Long',
    location: 'Tầng 3 - Tòa Nhà A',
    capacity: 25,
    status: 'AVAILABLE',
    image_url: 'https://images.unsplash.com/photo-1517502884422-41eaead166d4?w=800&auto=format&fit=crop&q=60',
    notes: 'Phòng họp lớn dành cho ban giám đốc, hội nghị toàn thể.',
    equipments: [
      { equipment: MOCK_EQUIPMENTS[0], quantity: 2 },
      { equipment: MOCK_EQUIPMENTS[1], quantity: 1 },
      { equipment: MOCK_EQUIPMENTS[2], quantity: 1 },
      { equipment: MOCK_EQUIPMENTS[3], quantity: 4 },
      { equipment: MOCK_EQUIPMENTS[4], quantity: 1 },
    ],
  },
  {
    id: 'room-2',
    name: 'Phòng Sáng Tạo Sài Gòn',
    location: 'Tầng 2 - Tòa Nhà A',
    capacity: 10,
    status: 'AVAILABLE',
    image_url: 'https://images.unsplash.com/photo-1497366216548-37526070297c?w=800&auto=format&fit=crop&q=60',
    notes: 'Phù hợp thảo luận nhóm, brainstorming dự án mới.',
    equipments: [
      { equipment: MOCK_EQUIPMENTS[0], quantity: 1 },
      { equipment: MOCK_EQUIPMENTS[2], quantity: 1 },
      { equipment: MOCK_EQUIPMENTS[4], quantity: 2 },
    ],
  },
  {
    id: 'room-3',
    name: 'Phòng Họp Nhanh Đà Nẵng',
    location: 'Tầng 2 - Tòa Nhà B',
    capacity: 6,
    status: 'AVAILABLE',
    image_url: 'https://images.unsplash.com/photo-1505409859467-3a796fd5798e?w=800&auto=format&fit=crop&q=60',
    notes: 'Không gian họp nhanh 1-1 hoặc nhóm scrum nhỏ.',
    equipments: [
      { equipment: MOCK_EQUIPMENTS[0], quantity: 1 },
      { equipment: MOCK_EQUIPMENTS[4], quantity: 1 },
    ],
  },
  {
    id: 'room-4',
    name: 'Phòng Họp Trực Tuyến Cần Thơ',
    location: 'Tầng 4 - Tòa Nhà B',
    capacity: 8,
    status: 'AVAILABLE',
    image_url: 'https://images.unsplash.com/photo-1542744173-8e7e53415bb0?w=800&auto=format&fit=crop&q=60',
    notes: 'Trang bị hệ thống cách âm và chuyên họp đối tác quốc tế.',
    equipments: [
      { equipment: MOCK_EQUIPMENTS[0], quantity: 1 },
      { equipment: MOCK_EQUIPMENTS[2], quantity: 1 },
      { equipment: MOCK_EQUIPMENTS[3], quantity: 2 },
    ],
  },
  {
    id: 'room-5',
    name: 'Phòng Đào Tạo Hạ Long',
    location: 'Tầng 5 - Tòa Nhà A',
    capacity: 35,
    status: 'MAINTENANCE',
    image_url: 'https://images.unsplash.com/photo-1431540015161-0bf868a2d407?w=800&auto=format&fit=crop&q=60',
    notes: 'Đang bảo trì định kỳ hệ thống điều hòa không khí đến hết tuần.',
    equipments: [
      { equipment: MOCK_EQUIPMENTS[1], quantity: 2 },
      { equipment: MOCK_EQUIPMENTS[3], quantity: 4 },
      { equipment: MOCK_EQUIPMENTS[4], quantity: 2 },
    ],
  },
];

const today = new Date();
const formatDate = (date: Date) => date.toISOString();

const inMinutes = (min: number) => {
  const d = new Date(today.getTime() + min * 60 * 1000);
  return formatDate(d);
};

export const MOCK_BOOKINGS: Booking[] = [
  {
    id: 'b-1',
    room_id: 'room-2',
    room: MOCK_ROOMS[1],
    organizer_id: 'u-1',
    organizer: MOCK_USERS[0],
    title: 'Họp Sprint Review & Kế hoạch tuần',
    description: 'Đánh giá tiến độ đồ án và phân công nhiệm vụ tuần tiếp theo.',
    start_time: inMinutes(5),
    end_time: inMinutes(65),
    meeting_type: 'HYBRID',
    meeting_link: 'https://meet.google.com/abc-xyz-meeting',
    status: 'CONFIRMED',
    version: 1,
    attendees: [
      { user_id: 'u-4', user: MOCK_USERS[3], status: 'ACCEPTED' },
      { user_id: 'u-2', user: MOCK_USERS[1], status: 'INVITED' },
    ],
    created_at: inMinutes(-120),
  },
  {
    id: 'b-2',
    room_id: 'room-1',
    room: MOCK_ROOMS[0],
    organizer_id: 'u-1',
    organizer: MOCK_USERS[0],
    title: 'Gặp gỡ khách hàng chiến lược',
    description: 'Thuyết trình giải pháp chuyển đổi số cho khối doanh nghiệp.',
    start_time: inMinutes(180),
    end_time: inMinutes(270),
    meeting_type: 'OFFLINE',
    status: 'CONFIRMED',
    version: 1,
    attendees: [
      { user_id: 'u-2', user: MOCK_USERS[1], status: 'ACCEPTED' },
      { user_id: 'u-3', user: MOCK_USERS[2], status: 'INVITED' },
    ],
    created_at: inMinutes(-300),
  },
  {
    id: 'b-3',
    room_id: 'room-3',
    room: MOCK_ROOMS[2],
    organizer_id: 'u-1',
    organizer: MOCK_USERS[0],
    title: '1-on-1 Đánh giá định kỳ Q3',
    description: 'Trao đổi mục tiêu cá nhân và định hướng quý mới.',
    start_time: inMinutes(-120),
    end_time: inMinutes(-60),
    meeting_type: 'OFFLINE',
    status: 'CHECKED_IN',
    checked_in_at: inMinutes(-118),
    version: 1,
    attendees: [],
    created_at: inMinutes(-400),
  },
  {
    id: 'b-4',
    room_id: 'room-4',
    room: MOCK_ROOMS[3],
    organizer_id: 'u-1',
    organizer: MOCK_USERS[0],
    title: 'Họp với chi nhánh Singapore',
    description: 'Thảo luận hợp tác kỹ thuật online.',
    start_time: inMinutes(-240),
    end_time: inMinutes(-180),
    meeting_type: 'ONLINE',
    meeting_link: 'https://zoom.us/j/999888777',
    status: 'CANCELLED',
    cancellation_reason: 'Đối tác bận việc đột xuất dời sang tuần sau',
    version: 1,
    attendees: [],
    created_at: inMinutes(-500),
  },
];

export const MOCK_NOTIFICATIONS: AppNotification[] = [
  {
    id: 'notif-1',
    user_id: 'u-1',
    type: 'REMINDER',
    title: 'Nhắc nhở: Cuộc họp sắp bắt đầu',
    content: 'Cuộc họp "Họp Sprint Review & Kế hoạch tuần" tại Phòng Sáng Tạo Sài Gòn sẽ bắt đầu trong 5 phút. Vui lòng check-in!',
    is_read: false,
    created_at: inMinutes(-2),
  },
  {
    id: 'notif-2',
    user_id: 'u-1',
    type: 'BOOKING_CREATED',
    title: 'Đặt phòng thành công',
    content: 'Bạn đã đặt thành công phòng "Phòng Hội Nghị Thăng Long" cho cuộc họp "Gặp gỡ khách hàng chiến lược".',
    is_read: false,
    created_at: inMinutes(-300),
  },
  {
    id: 'notif-3',
    user_id: 'u-1',
    type: 'BOOKING_CANCELLED',
    title: 'Lịch họp đã hủy',
    content: 'Cuộc họp "Họp với chi nhánh Singapore" đã được hủy thành công.',
    is_read: true,
    created_at: inMinutes(-500),
  },
];

