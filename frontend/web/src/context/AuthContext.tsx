import React, { createContext, useContext, useState } from 'react';
import type { Booking, Role, Room, User, AppNotification } from '../types';
import { MOCK_BOOKINGS, MOCK_NOTIFICATIONS, MOCK_ROOMS, MOCK_USERS } from '../mock/data';

interface AuthContextType {
  currentUser: User | null;
  users: User[];
  role: Role;
  setRole: (role: Role) => void;
  login: () => void;
  logout: () => void;
  rooms: Room[];
  bookings: Booking[];
  notifications: AppNotification[];
  unreadNotificationCount: number;
  markAllNotificationsAsRead: () => void;
  addBooking: (booking: Omit<Booking, 'id' | 'created_at' | 'version' | 'status'>) => void;
  cancelBooking: (id: string, reason?: string) => void;
  checkinBooking: (id: string) => boolean;
  addRoom: (room: Omit<Room, 'id'>) => void;
  updateRoom: (id: string, updated: Partial<Room>) => void;
  deleteRoom: (id: string) => void;
  updateUserRole: (userId: string, newRole: Role) => void;
  updateUserStatus: (userId: string, newStatus: 'ACTIVE' | 'INACTIVE') => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [users, setUsers] = useState<User[]>(MOCK_USERS);
  const [currentUser, setCurrentUser] = useState<User | null>(MOCK_USERS[0]);
  const [rooms, setRooms] = useState<Room[]>(MOCK_ROOMS);
  const [bookings, setBookings] = useState<Booking[]>(MOCK_BOOKINGS);
  const [notifications, setNotifications] = useState<AppNotification[]>(MOCK_NOTIFICATIONS);

  const unreadNotificationCount = notifications.filter((n) => !n.is_read).length;

  const markAllNotificationsAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
  };

  const setRole = (newRole: Role) => {
    const found = users.find((u) => u.role === newRole) || {
      ...MOCK_USERS[0],
      role: newRole,
      name: `Tài khoản (${newRole})`,
    };
    setCurrentUser(found);
  };

  const login = () => {
    setCurrentUser(MOCK_USERS[0]);
  };

  const logout = () => {
    setCurrentUser(null);
  };

  const addBooking = (newBookingData: Omit<Booking, 'id' | 'created_at' | 'version' | 'status'>) => {
    const newBooking: Booking = {
      ...newBookingData,
      id: `b-${Date.now()}`,
      status: 'CONFIRMED',
      version: 1,
      created_at: new Date().toISOString(),
    };
    setBookings((prev) => [newBooking, ...prev]);
  };

  const cancelBooking = (id: string, reason?: string) => {
    setBookings((prev) =>
      prev.map((b) =>
        b.id === id
          ? { ...b, status: 'CANCELLED', cancellation_reason: reason || 'Người dùng hủy' }
          : b
      )
    );
  };

  const checkinBooking = (id: string): boolean => {
    let success = false;
    setBookings((prev) =>
      prev.map((b) => {
        if (b.id === id) {
          success = true;
          return {
            ...b,
            status: 'CHECKED_IN',
            checked_in_at: new Date().toISOString(),
          };
        }
        return b;
      })
    );
    return success;
  };

  const addRoom = (newRoomData: Omit<Room, 'id'>) => {
    const room: Room = {
      ...newRoomData,
      id: `room-${Date.now()}`,
    };
    setRooms((prev) => [...prev, room]);
  };

  const updateRoom = (id: string, updated: Partial<Room>) => {
    setRooms((prev) => prev.map((r) => (r.id === id ? { ...r, ...updated } : r)));
  };

  const deleteRoom = (id: string) => {
    setRooms((prev) => prev.filter((r) => r.id !== id));
  };

  const updateUserRole = (userId: string, newRole: Role) => {
    setUsers((prev) =>
      prev.map((u) => (u.id === userId ? { ...u, role: newRole } : u))
    );
    if (currentUser?.id === userId) {
      setCurrentUser((prev) => (prev ? { ...prev, role: newRole } : null));
    }
  };

  const updateUserStatus = (userId: string, newStatus: 'ACTIVE' | 'INACTIVE') => {
    setUsers((prev) =>
      prev.map((u) => (u.id === userId ? { ...u, status: newStatus } : u))
    );
  };

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        users,
        role: currentUser?.role || 'EMPLOYEE',
        setRole,
        login,
        logout,
        rooms,
        bookings,
        notifications,
        unreadNotificationCount,
        markAllNotificationsAsRead,
        addBooking,
        cancelBooking,
        checkinBooking,
        addRoom,
        updateRoom,
        deleteRoom,
        updateUserRole,
        updateUserStatus,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
