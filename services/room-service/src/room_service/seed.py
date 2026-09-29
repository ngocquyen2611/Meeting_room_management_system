import sys

# Fix Windows console UTF-8 printing
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from room_service.database import SessionLocal
from room_service.models import (
    BookingPolicy,
    Equipment,
    Room,
    RoomEquipment,
    User,
)


def seed_users(db):
    users_data = [
        {
            "auth0_user_id": "auth0|demo-admin",
            "email": "admin@demo.com",
            "name": "System Admin",
            "role": "ADMIN",
            "status": "ACTIVE",
        },
        {
            "auth0_user_id": "auth0|demo-manager",
            "email": "manager@demo.com",
            "name": "Room Manager",
            "role": "ROOM_MANAGER",
            "status": "ACTIVE",
        },
        {
            "auth0_user_id": "auth0|demo-employee",
            "email": "employee@demo.com",
            "name": "Employee",
            "role": "EMPLOYEE",
            "status": "ACTIVE",
        },
    ]

    created_count = 0

    for data in users_data:
        user = (
            db.query(User)
            .filter(User.email == data["email"])
            .first()
        )

        if user is None:
            user = User(**data)
            db.add(user)
            created_count += 1

    db.flush()

    print(f"[INFO] Users: tao moi {created_count} record.")


def seed_equipments(db):
    equipments_data = [
        {
            "code": "TV",
            "name": "Man hinh TV 65 inch 4K",
            "description": "Ket noi HDMI va khong day AirPlay/Miracast",
        },
        {
            "code": "PROJECTOR",
            "name": "May chieu Epson Full HD",
            "description": "Do sang cao, thich hop phong hoi thao",
        },
        {
            "code": "CAMERA",
            "name": "Camera hoi nghi 4K Logitech Rally",
            "description": "Auto zoom va tracking nguoi noi",
        },
        {
            "code": "MIC",
            "name": "He thong Micro da huong Polycom",
            "description": "Khu on AI, thu am 360 do",
        },
        {
            "code": "WHITEBOARD",
            "name": "Bang trang viet but da",
            "description": "Bang tu 2.4m x 1.2m",
        },
    ]

    equipment_map = {}

    for item in equipments_data:
        equipment = (
            db.query(Equipment)
            .filter(Equipment.code == item["code"])
            .first()
        )

        if equipment is None:
            equipment = Equipment(
                code=item["code"],
                name=item["name"],
                description=item["description"],
            )
            db.add(equipment)
            db.flush()

        equipment_map[item["code"]] = equipment

    print("[INFO] Equipments: da san sang 5 thiet bi.")

    return equipment_map


def seed_rooms(db, equipment_map):
    rooms_data = [
        {
            "name": "Phong hop Tokyo (Hop nhom)",
            "location": "Tang 2 - Toa A",
            "capacity": 8,
            "status": "AVAILABLE",
            "notes": "Phu hop hop sprint, retrospective hoac 1-on-1",
            "equipments": [
                ("TV", 1),
                ("WHITEBOARD", 1),
            ],
        },
        {
            "name": "Phong hop Sai Gon (Tieu chuan)",
            "location": "Tang 3 - Toa A",
            "capacity": 16,
            "status": "AVAILABLE",
            "notes": "Trang bi day du he thong hop Hybrid chat luong cao",
            "equipments": [
                ("TV", 1),
                ("CAMERA", 1),
                ("MIC", 1),
                ("WHITEBOARD", 1),
            ],
        },
        {
            "name": "Hoi truong Grand Hall (Hoi nghi)",
            "location": "Tang 5 - Toa B",
            "capacity": 50,
            "status": "AVAILABLE",
            "notes": "Hoi thao toan cong ty (Townhall), su kien khach hang",
            "equipments": [
                ("PROJECTOR", 1),
                ("CAMERA", 1),
                ("MIC", 4),
                ("WHITEBOARD", 1),
            ],
        },
        {
            "name": "Phong hop Seoul (Thao luan nhanh)",
            "location": "Tang 2 - Toa A",
            "capacity": 6,
            "status": "AVAILABLE",
            "notes": "Phong nho rieng tu",
            "equipments": [
                ("TV", 1),
            ],
        },
        {
            "name": "Phong hop New York (Bao tri)",
            "location": "Tang 4 - Toa B",
            "capacity": 12,
            "status": "MAINTENANCE",
            "notes": "Dang bao duong he thong dieu hoa va cach am",
            "equipments": [
                ("TV", 1),
                ("CAMERA", 1),
            ],
        },
    ]

    created_rooms = 0
    created_room_equipment = 0

    for room_data in rooms_data:
        room = (
            db.query(Room)
            .filter(Room.name == room_data["name"])
            .first()
        )

        if room is None:
            room = Room(
                name=room_data["name"],
                location=room_data["location"],
                capacity=room_data["capacity"],
                status=room_data["status"],
                notes=room_data["notes"],
            )
            db.add(room)
            db.flush()
            created_rooms += 1

        for eq_code, quantity in room_data["equipments"]:
            equipment = equipment_map[eq_code]

            room_equipment = (
                db.query(RoomEquipment)
                .filter(
                    RoomEquipment.room_id == room.id,
                    RoomEquipment.equipment_id == equipment.id,
                )
                .first()
            )

            if room_equipment is None:
                db.add(
                    RoomEquipment(
                        room_id=room.id,
                        equipment_id=equipment.id,
                        quantity=quantity,
                    )
                )
                created_room_equipment += 1

    print(f"[INFO] Rooms: tao moi {created_rooms} phong.")
    print(
        "[INFO] Room equipments: "
        f"tao moi {created_room_equipment} quan he."
    )


def seed_booking_policy(db):
    policy = db.query(BookingPolicy).filter(BookingPolicy.id == 1).first()

    if policy is None:
        policy = BookingPolicy(
            id=1,
            max_booking_duration_hours=4,
            max_advance_days=30,
            checkin_grace_period_minutes=15,
            require_checkin=True,
        )
        db.add(policy)
        print("[INFO] Booking policy: tao moi policy mac dinh.")
    else:
        print("[INFO] Booking policy: da ton tai, bo qua.")


def seed_data():
    db = SessionLocal()

    try:
        print("[INFO] Dang nap seed data vao PostgreSQL...")

        seed_users(db)

        equipment_map = seed_equipments(db)

        seed_rooms(
            db,
            equipment_map,
        )

        seed_booking_policy(db)

        db.commit()

        print("[SUCCESS] Seed data thanh cong.")
        print("[INFO] Users: ADMIN / ROOM_MANAGER / EMPLOYEE")
        print("[INFO] Rooms: 5")
        print("[INFO] Equipments: 5")
        print("[INFO] Booking Policy: 1")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Loi khi seed data: {e}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_data()