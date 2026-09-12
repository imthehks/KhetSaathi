from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date,
    ForeignKey, Text, Enum
)
from sqlalchemy.orm import relationship
from app.database import Base

class UserRole:
    FARMER = "farmer"
    OWNER = "owner"
    LABORER = "laborer"
    ADMIN = "admin"
    ALL = [FARMER, OWNER, LABORER, ADMIN]

class BookingStatus:
    PENDING = "pending"
    CONFIRMED = "confirmed"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ALL = [PENDING, CONFIRMED, ONGOING, COMPLETED, CANCELLED]

class PaymentStatus:
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    ALL = [PENDING, SUCCESS, FAILED]

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default=UserRole.FARMER)
    phone = Column(String(20), nullable=True)
    address = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    equipment = relationship("Equipment", back_populates="owner", cascade="all, delete-orphan")
    labor_profile = relationship("Labor", back_populates="user", uselist=False, cascade="all, delete-orphan")
    farmer_bookings = relationship("Booking", foreign_keys="[Booking.farmer_id]", back_populates="farmer")
    owner_bookings = relationship("Booking", foreign_keys="[Booking.owner_id]", back_populates="owner")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(150), index=True, nullable=False)
    category = Column(String(50), index=True, nullable=False)  # Tractor, Harvester, Seeder, Tillage, Irrigation, Sprayer, etc.
    rental_rate = Column(Float, nullable=False)  # Daily rate in INR
    location = Column(String(100), index=True, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    is_available = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    owner = relationship("User", back_populates="equipment")


class Labor(Base):
    __tablename__ = "labor"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    skill_type = Column(String(100), index=True, nullable=False)  # Tractor Driver, Harvesting, Sowing, Spraying, General
    wage_rate = Column(Float, nullable=False)  # Daily wage in INR
    location = Column(String(100), index=True, nullable=False)
    description = Column(Text, nullable=True)
    is_available = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    user = relationship("User", back_populates="labor_profile")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_type = Column(String(20), nullable=False)  # 'equipment' or 'labor'
    item_id = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(20), default=BookingStatus.PENDING, nullable=False)
    total_amount = Column(Float, nullable=False)
    extension_days = Column(Integer, default=0, nullable=False)
    late_fee = Column(Float, default=0.0, nullable=False)
    return_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    farmer = relationship("User", foreign_keys=[farmer_id], back_populates="farmer_bookings")
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owner_bookings")
    payments = relationship("Payment", back_populates="booking", cascade="all, delete-orphan")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    method = Column(String(50), default="razorpay", nullable=False)
    status = Column(String(20), default=PaymentStatus.PENDING, nullable=False)
    razorpay_order_id = Column(String(100), nullable=True)
    razorpay_payment_id = Column(String(100), nullable=True)
    razorpay_signature = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    booking = relationship("Booking", back_populates="payments")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    user = relationship("User", back_populates="notifications")
