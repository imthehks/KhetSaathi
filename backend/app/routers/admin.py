from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import User, Equipment, Labor, Booking, Payment, UserRole, BookingStatus, PaymentStatus
from app.schemas import StatsSummary, UserResponse, BookingResponse, PaymentResponse
from app.auth import require_role
from app.routers.bookings import enrich_booking_item_details

router = APIRouter(prefix="/api/admin", tags=["Admin Operations"])

@router.get("/stats", response_model=StatsSummary)
def get_system_stats(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Retrieve platform-wide operational statistics and performance metrics."""
    total_users = db.query(User).count()
    total_equipment = db.query(Equipment).count()
    active_equipment = db.query(Equipment).filter(Equipment.is_available == True).count()
    total_labor = db.query(Labor).count()
    active_labor = db.query(Labor).filter(Labor.is_available == True).count()
    total_bookings = db.query(Booking).count()

    # Booking status counts
    pending_bookings = db.query(Booking).filter(Booking.status == BookingStatus.PENDING).count()
    confirmed_bookings = db.query(Booking).filter(Booking.status == BookingStatus.CONFIRMED).count()
    ongoing_bookings = db.query(Booking).filter(Booking.status == BookingStatus.ONGOING).count()
    completed_bookings = db.query(Booking).filter(Booking.status == BookingStatus.COMPLETED).count()

    # Total revenue from successful payments
    revenue_sum = db.query(func.sum(Payment.amount)).filter(Payment.status == PaymentStatus.SUCCESS).scalar()
    total_revenue = float(revenue_sum or 0.0)

    return StatsSummary(
        total_users=total_users,
        total_equipment=total_equipment,
        active_equipment=active_equipment,
        total_labor=total_labor,
        active_labor=active_labor,
        total_bookings=total_bookings,
        total_revenue=total_revenue,
        pending_bookings=pending_bookings,
        confirmed_bookings=confirmed_bookings,
        ongoing_bookings=ongoing_bookings,
        completed_bookings=completed_bookings
    )

@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    role: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """List all registered users with administrative search and role filters."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role.lower().strip())
    if q:
        search_pattern = f"%{q.strip()}%"
        query = query.filter(
            (User.name.ilike(search_pattern)) |
            (User.email.ilike(search_pattern)) |
            (User.phone.ilike(search_pattern))
        )
    return query.order_by(User.id.desc()).offset(skip).limit(limit).all()

@router.patch("/users/{user_id}/toggle-status", response_model=UserResponse)
def toggle_user_active_status(
    user_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Activate or suspend user account."""
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate your own admin account")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user

@router.get("/bookings", response_model=List[BookingResponse])
def get_all_bookings_audit(
    status_filter: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Retrieve full audit log of all bookings across the platform."""
    query = db.query(Booking)
    if status_filter:
        query = query.filter(Booking.status == status_filter.lower().strip())

    bookings = query.order_by(Booking.id.desc()).offset(skip).limit(limit).all()
    result = []
    for b in bookings:
        item_schema = BookingResponse.model_validate(b)
        item_schema.item_details = enrich_booking_item_details(b, db)
        result.append(item_schema)
    return result

@router.get("/payments", response_model=List[PaymentResponse])
def get_all_payments_audit(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Retrieve all payment records for financial reconciliation."""
    return db.query(Payment).order_by(Payment.id.desc()).offset(skip).limit(limit).all()
