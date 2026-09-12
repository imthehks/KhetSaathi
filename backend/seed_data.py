import sys
import os
from datetime import date, timedelta

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, init_db
from app.models import User, Equipment, Labor, Booking, Payment, Notification, UserRole, BookingStatus, PaymentStatus
from app.auth import get_password_hash

def seed_database():
    print("🌱 Initializing database schema...")
    init_db()
    db = SessionLocal()

    try:
        print("Synchronizing users...")
        # Core users
        user_specs = [
            ("Ramesh Kumar", "farmer@khetsaathi.com", "farmer123", UserRole.FARMER, "+91 98765 43210", "Village Taraori, Karnal, Haryana"),
            ("Sardar Harpreet Singh", "owner@khetsaathi.com", "owner123", UserRole.OWNER, "+91 98123 45678", "GT Road, Ludhiana, Punjab"),
            ("Sunita Devi", "laborer@khetsaathi.com", "labor123", UserRole.LABORER, "+91 97111 22334", "Dauralla, Meerut, Uttar Pradesh"),
            ("KhetSaathi Admin", "admin@khetsaathi.com", "admin123", UserRole.ADMIN, "+91 99999 88888", "HQ Krishi Bhawan, New Delhi"),
            ("Vikram Patil", "owner2@khetsaathi.com", "owner123", UserRole.OWNER, "+91 98234 56789", "Dindori Road, Nashik, Maharashtra"),
            ("Raju Yadav", "laborer2@khetsaathi.com", "labor123", UserRole.LABORER, "+91 98345 67890", "Danapur, Patna, Bihar"),
            ("Balwinder Singh Dhillon", "owner3@khetsaathi.com", "owner123", UserRole.OWNER, "+91 98789 12345", "Malwa Region, Sangrur, Punjab"),
        ]

        for name, email, pwd, role, phone, address in user_specs:
            u = db.query(User).filter(User.email == email).first()
            if not u:
                u = User(
                    name=name,
                    email=email,
                    password_hash=get_password_hash(pwd),
                    role=role,
                    phone=phone,
                    address=address,
                    is_active=True
                )
                db.add(u)
        db.commit()

        owner1 = db.query(User).filter(User.email == "owner@khetsaathi.com").first()
        owner2 = db.query(User).filter(User.email == "owner2@khetsaathi.com").first() or owner1
        owner3 = db.query(User).filter(User.email == "owner3@khetsaathi.com").first() or owner1
        farmer = db.query(User).filter(User.email == "farmer@khetsaathi.com").first()
        labor1 = db.query(User).filter(User.email == "laborer@khetsaathi.com").first()
        labor2 = db.query(User).filter(User.email == "laborer2@khetsaathi.com").first() or labor1

        print("Updating Farm Equipment with suitable images and captions...")
        
        equipment_data = [
            {
                "owner_id": owner1.id,
                "name": "Mahindra 575 DI XP Plus Tractor (47 HP)",
                "category": "Tractor",
                "rental_rate": 1400.0,
                "location": "Ludhiana, Punjab",
                "description": "47 HP direct-injection diesel tractor with dual-acting power steering and standard 540 RPM PTO. Optimized for 7-foot rotavators, disc harrows, and heavy haulage trolleys.",
                "image_url": "/img/tractor_red.svg",
                "is_available": True
            },
            {
                "owner_id": owner3.id,
                "name": "John Deere 5310 4WD Heavy Duty Tractor (55 HP)",
                "category": "Tractor",
                "rental_rate": 1850.0,
                "location": "Sangrur, Punjab",
                "description": "55 HP 4-Wheel Drive turbo engine tractor with synchromesh transmission and self-equalizing disc brakes. Superior traction in wet paddy puddling and deep black soil.",
                "image_url": "/img/tractor_green.svg",
                "is_available": True
            },
            {
                "owner_id": owner1.id,
                "name": "Swaraj 855 FE Power Steering Tractor (52 HP)",
                "category": "Tractor",
                "rental_rate": 1500.0,
                "location": "Karnal, Haryana",
                "description": "52 HP 3-cylinder diesel tractor with multi-speed reverse PTO and heavy front ballast weights. Renowned for low fuel consumption during laser leveling and deep tillage.",
                "image_url": "/img/tractor_blue.svg",
                "is_available": True
            },
            {
                "owner_id": owner1.id,
                "name": "John Deere W70 Multi-Crop Combine Harvester",
                "category": "Harvester",
                "rental_rate": 4500.0,
                "location": "Ludhiana, Punjab",
                "description": "Self-propelled multi-crop combine harvester with 14-foot cutter bar. High-output threshing drum ensures clean grain tank fill with <1% breakage in wheat, paddy, and soybean. Includes operator.",
                "image_url": "/img/harvester.svg",
                "is_available": True
            },
            {
                "owner_id": owner1.id,
                "name": "Shaktiman Semi-Champion Rotavator (7 Feet)",
                "category": "Rotavator & Tillage",
                "rental_rate": 850.0,
                "location": "Karnal, Haryana",
                "description": "Heavy-duty 7-foot PTO-driven rotary tiller with Boron steel L-shaped curved blades. Efficiently pulverizes crop stubble and prepares an optimal seedbed in a single pass.",
                "image_url": "/img/rotavator.svg",
                "is_available": True
            },
            {
                "owner_id": owner1.id,
                "name": "Precision Dual-Slope Laser Land Leveler",
                "category": "Laser Land Leveler",
                "rental_rate": 1800.0,
                "location": "Karnal, Haryana",
                "description": "Dual-slope rotary laser transmitter with digital receiver mast and 7-foot hydraulic bucket scraper. Saves up to 30% irrigation water and increases crop yield via uniform grading.",
                "image_url": "/img/laser_leveler.svg",
                "is_available": True
            },
            {
                "owner_id": owner2.id,
                "name": "Shakti 5HP Solar Powered Agricultural Water Pump",
                "category": "Irrigation & Pumps",
                "rental_rate": 600.0,
                "location": "Nashik, Maharashtra",
                "description": "Portable 5 HP solar photovoltaic DC water pump set with 100m layflat hose pipe. High discharge rate of 50,000 liters/hour for irrigation with zero diesel or electricity charges.",
                "image_url": "/img/solar_pump.svg",
                "is_available": True
            },
            {
                "owner_id": owner2.id,
                "name": "Garuda Agri-Drone Precision Spraying System (10L)",
                "category": "Sprayer",
                "rental_rate": 2200.0,
                "location": "Nashik, Maharashtra",
                "description": "Certified agricultural hexacopter drone with 10-liter tank and micron atomizing mist nozzles. Covers 1 acre in 7 minutes with GPS waypoint tracking and uniform canopy coverage. Includes pilot.",
                "image_url": "/img/drone_sprayer.svg",
                "is_available": True
            },
            {
                "owner_id": owner2.id,
                "name": "Aspee 16L Battery Operated Knapsack Sprayer",
                "category": "Sprayer",
                "rental_rate": 300.0,
                "location": "Nashik, Maharashtra",
                "description": "16-liter knapsack sprayer equipped with dual high-pressure diaphragm pump, 12V 12Ah rechargeable battery (6 hours runtime), pressure regulator, and telescopic brass lance.",
                "image_url": "/img/knapsack_sprayer.svg",
                "is_available": True
            },
            {
                "owner_id": owner1.id,
                "name": "National Agro Pneumatic Zero-Till Seed Drill",
                "category": "Seeder & Planter",
                "rental_rate": 1100.0,
                "location": "Ludhiana, Punjab",
                "description": "9-row zero-tillage seed-cum-fertilizer drill. Sows wheat and mustard directly into standing paddy stubble without burning residue, preserving critical soil moisture.",
                "image_url": "/img/seed_drill.svg",
                "is_available": True
            },
            {
                "owner_id": owner2.id,
                "name": "VST Shakti MT 180D Fieldstar Power Tiller (18 HP)",
                "category": "Rotavator & Tillage",
                "rental_rate": 750.0,
                "location": "Pune, Maharashtra",
                "description": "Compact 18 HP single-cylinder diesel power tiller with rotary tines. Highly maneuverable for sugarcane earthing up, vegetable inter-row cultivation, and orchards.",
                "image_url": "/img/power_tiller.svg",
                "is_available": True
            },
            {
                "owner_id": owner2.id,
                "name": "Automatic Multi-Crop High-Output Grain Thresher",
                "category": "Other",
                "rental_rate": 1200.0,
                "location": "Indore, Madhya Pradesh",
                "description": "Tractor PTO-driven multi-crop thresher for wheat, chickpea, soybean, and mustard. High capacity output of 15 to 20 quintals per hour with twin-blower chaff cleaner and safety reverse feed hopper.",
                "image_url": "/img/grain_thresher.svg",
                "is_available": True
            }
        ]

        # Clear existing equipment so all listings have the new suitable images and captions
        db.query(Equipment).delete()
        db.commit()

        for item in equipment_data:
            eq = Equipment(**item)
            db.add(eq)
        db.commit()

        print("Seeding / Updating Labor profiles...")
        db.query(Labor).delete()
        db.commit()

        labor_catalog = [
            {
                "user_id": labor1.id,
                "skill_type": "Tractor Driver & Machinery Operator",
                "wage_rate": 650.0,
                "location": "Meerut, Uttar Pradesh",
                "description": "10+ years commercial experience operating 35HP to 60HP tractors, laser levelers, rotavators, and seed drills with safety focus.",
                "is_available": True
            },
            {
                "user_id": labor2.id,
                "skill_type": "Paddy Sowing & Transplanting Specialist",
                "wage_rate": 500.0,
                "location": "Danapur, Patna, Bihar",
                "description": "Expertise in System of Rice Intensification (SRI) technique, precision nursery raising, and mat nursery preparation.",
                "is_available": True
            }
        ]

        for l_data in labor_catalog:
            db.add(Labor(**l_data))
        db.commit()

        print("Creating active demo bookings...")
        db.query(Booking).delete()
        db.query(Payment).delete()
        db.commit()

        tractor = db.query(Equipment).filter(Equipment.name.like("%Mahindra%")).first()
        today = date.today()

        # Ongoing booking
        b1 = Booking(
            farmer_id=farmer.id,
            owner_id=owner1.id,
            item_type="equipment",
            item_id=tractor.id,
            start_date=today - timedelta(days=1),
            end_date=today + timedelta(days=2),
            status=BookingStatus.ONGOING,
            total_amount=5600.0,
            extension_days=0,
            late_fee=0.0
        )
        db.add(b1)
        db.commit()
        db.refresh(b1)

        p1 = Payment(
            booking_id=b1.id,
            amount=5600.0,
            method="razorpay",
            status=PaymentStatus.SUCCESS,
            razorpay_order_id=f"order_live_{b1.id}",
            razorpay_payment_id=f"pay_live_{b1.id}",
            razorpay_signature="seed_signature_verified"
        )
        db.add(p1)

        # Pending booking
        harvester = db.query(Equipment).filter(Equipment.name.like("%Harvester%")).first()
        b2 = Booking(
            farmer_id=farmer.id,
            owner_id=owner1.id,
            item_type="equipment",
            item_id=harvester.id,
            start_date=today + timedelta(days=4),
            end_date=today + timedelta(days=6),
            status=BookingStatus.PENDING,
            total_amount=13500.0,
            extension_days=0,
            late_fee=0.0
        )
        db.add(b2)
        db.commit()
        db.refresh(b2)

        p2 = Payment(
            booking_id=b2.id,
            amount=13500.0,
            method="razorpay",
            status=PaymentStatus.PENDING,
            razorpay_order_id=f"order_pending_{b2.id}"
        )
        db.add(p2)

        # Clear and re-add notifications
        db.query(Notification).delete()
        db.add(Notification(
            user_id=farmer.id,
            message="Welcome to KhetSaathi! Explore certified farm machinery and skilled operators in your district."
        ))
        db.add(Notification(
            user_id=farmer.id,
            message=f"Booking #{b1.id} for Mahindra 575 DI XP Plus Tractor is currently ONGOING."
        ))
        db.add(Notification(
            user_id=owner1.id,
            message=f"Booking #{b1.id} payment verified (₹5,600.00). Item handed over to Ramesh Kumar."
        ))
        db.commit()

        total_eq = db.query(Equipment).count()
        print(f"✅ Seeding finished! Total Verified Farm Equipment: {total_eq}")

    except Exception as e:
        db.rollback()
        print(f"❌ Seeding error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
