import sys

# Fix Windows console utf-8 printing
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from room_service.database import SessionLocal
from room_service.models import Equipment, Room, RoomEquipment


def seed_data():
    db = SessionLocal()
    try:
        if db.query(Room).first() is not None:
            print("[INFO] Du lieu phong da ton tai trong database, bo qua seed.")
            return

        print("[INFO] Dang nap du lieu mau vao PostgreSQL...")

        equipments_data = [
            {"code": "TV", "name": "Man hinh TV 65 inch 4K", "description": "Ket noi HDMI va khong day AirPlay/Miracast"},
            {"code": "PROJECTOR", "name": "May chieu Epson Full HD", "description": "Do sang cao, thich hop phong hoi thao"},
            {"code": "CAMERA", "name": "Camera hoi nghi 4K Logitech Rally", "description": "Auto zoom va tracking nguoi noi"},
            {"code": "MIC", "name": "He thong Micro da huong Polycom", "description": "Khu on AI, thu am 360 do"},
            {"code": "WHITEBOARD", "name": "Bang trang viet but da", "description": "Bang tu 2.4m x 1.2m"},
        ]

        equipment_map = {}
        for item in equipments_data:
            eq = Equipment(code=item["code"], name=item["name"], description=item["description"])
            db.add(eq)
            equipment_map[item["code"]] = eq

        db.flush()

        rooms_data = [
            {
                "name": "Phong hop Tokyo (Hop nhom)",
                "location": "Tang 2 - Toa A",
                "capacity": 8,
                "status": "AVAILABLE",
                "notes": "Phu hop hop sprint, retrospective hoac 1-on-1",
                "equipments": [("TV", 1), ("WHITEBOARD", 1)],
            },
            {
                "name": "Phong hop Sai Gon (Tieu chuan)",
                "location": "Tang 3 - Toa A",
                "capacity": 16,
                "status": "AVAILABLE",
                "notes": "Trang bi day du he thong hop Hybrid chat luong cao",
                "equipments": [("TV", 1), ("CAMERA", 1), ("MIC", 1), ("WHITEBOARD", 1)],
            },
            {
                "name": "Hoi truong Grand Hall (Hoi nghi)",
                "location": "Tang 5 - Toa B",
                "capacity": 50,
                "status": "AVAILABLE",
                "notes": "Hoi thao toan cong ty (Townhall), su kien khach hang",
                "equipments": [("PROJECTOR", 1), ("CAMERA", 1), ("MIC", 4), ("WHITEBOARD", 1)],
            },
            {
                "name": "Phong hop Seoul (Thao luan nhanh)",
                "location": "Tang 2 - Toa A",
                "capacity": 6,
                "status": "AVAILABLE",
                "notes": "Phong nho rieng tu",
                "equipments": [("TV", 1)],
            },
            {
                "name": "Phong hop New York (Bao tri)",
                "location": "Tang 4 - Toa B",
                "capacity": 12,
                "status": "MAINTENANCE",
                "notes": "Dang bao duong he thong dieu hoa va cach am",
                "equipments": [("TV", 1), ("CAMERA", 1)],
            },
        ]

        for r_info in rooms_data:
            room = Room(
                name=r_info["name"],
                location=r_info["location"],
                capacity=r_info["capacity"],
                status=r_info["status"],
                notes=r_info["notes"],
            )
            db.add(room)
            db.flush()

            for eq_code, qty in r_info["equipments"]:
                re = RoomEquipment(
                    room_id=room.id,
                    equipment_id=equipment_map[eq_code].id,
                    quantity=qty,
                )
                db.add(re)

        db.commit()
        print("[SUCCESS] Nap seed data thanh cong! Da tao 5 phong hop va 5 thiet bi.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Loi khi nap du lieu: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
