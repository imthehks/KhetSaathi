from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, ConfigDict
from app.models import UserRole, BookingStatus, PaymentStatus

# --- USER SCHEMAS ---

class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=255)

class UserRegister(UserBase):
    password: str = Field(..., min_length=6, max_length=100)
    role: str = Field(default=UserRole.FARMER)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        role_clean = v.lower().strip()
        if role_clean not in [UserRole.FARMER, UserRole.OWNER, UserRole.LABORER, UserRole.ADMIN]:
            raise ValueError(f"Invalid role. Must be one of: {UserRole.ALL}")
        return role_clean

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=255)

class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None


# --- EQUIPMENT SCHEMAS ---

class EquipmentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    category: str = Field(..., min_length=2, max_length=50)
    rental_rate: float = Field(..., gt=0, description="Rental rate per day in INR")
    location: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_available: bool = True

class EquipmentCreate(EquipmentBase):
    pass

class EquipmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    category: Optional[str] = Field(None, min_length=2, max_length=50)
    rental_rate: Optional[float] = Field(None, gt=0)
    location: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_available: Optional[bool] = None

class EquipmentResponse(EquipmentBase):
    id: int
    owner_id: int
    created_at: datetime
    owner: Optional[UserResponse] = None
    model_config = ConfigDict(from_attributes=True)


# --- LABOR SCHEMAS ---

class LaborBase(BaseModel):
    skill_type: str = Field(..., min_length=2, max_length=100)
    wage_rate: float = Field(..., gt=0, description="Wage rate per day in INR")
    location: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    is_available: bool = True

class LaborCreate(LaborBase):
    pass

class LaborUpdate(BaseModel):
    skill_type: Optional[str] = Field(None, min_length=2, max_length=100)
    wage_rate: Optional[float] = Field(None, gt=0)
    location: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    is_available: Optional[bool] = None

class LaborResponse(LaborBase):
    id: int
    user_id: int
    created_at: datetime
    user: Optional[UserResponse] = None
    model_config = ConfigDict(from_attributes=True)


# --- BOOKING SCHEMAS ---

class BookingCreate(BaseModel):
    item_type: str = Field(..., description="'equipment' or 'labor'")
    item_id: int = Field(..., gt=0)
    start_date: date
    end_date: date

    @field_validator("item_type")
    @classmethod
    def validate_item_type(cls, v: str) -> str:
        clean = v.lower().strip()
        if clean not in ["equipment", "labor"]:
            raise ValueError("item_type must be either 'equipment' or 'labor'")
        return clean

    @model_validator(mode="after")
    def validate_dates(self) -> "BookingCreate":
        if self.end_date < self.start_date:
            raise ValueError("end_date cannot be earlier than start_date")
        today = date.today()
        if self.start_date < today:
            raise ValueError("start_date cannot be in the past")
        return self

class BookingExtend(BaseModel):
    extension_days: int = Field(..., gt=0, le=30, description="Number of additional days to extend")

class BookingReturn(BaseModel):
    return_date: Optional[date] = None

class BookingStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        clean = v.lower().strip()
        if clean not in BookingStatus.ALL:
            raise ValueError(f"Invalid status. Must be one of: {BookingStatus.ALL}")
        return clean

class BookingResponse(BaseModel):
    id: int
    farmer_id: int
    owner_id: int
    item_type: str
    item_id: int
    start_date: date
    end_date: date
    status: str
    total_amount: float
    extension_days: int
    late_fee: float
    return_date: Optional[date] = None
    created_at: datetime
    farmer: Optional[UserResponse] = None
    owner: Optional[UserResponse] = None
    item_details: Optional[Any] = None
    model_config = ConfigDict(from_attributes=True)


# --- PAYMENT SCHEMAS ---

class RazorpayOrderCreate(BaseModel):
    booking_id: int

class RazorpayOrderResponse(BaseModel):
    order_id: str
    amount: int  # in paise
    currency: str = "INR"
    key_id: str
    booking_id: int

class RazorpayVerify(BaseModel):
    booking_id: int
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

class PaymentResponse(BaseModel):
    id: int
    booking_id: int
    amount: float
    method: str
    status: str
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- NOTIFICATION SCHEMAS ---

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    message: str
    is_read: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- ADMIN & STATS SCHEMAS ---

class StatsSummary(BaseModel):
    total_users: int
    total_equipment: int
    total_labor: int
    total_bookings: int
    total_revenue: float
    pending_bookings: int
    confirmed_bookings: int
    ongoing_bookings: int
    completed_bookings: int
    active_equipment: int
    active_labor: int
