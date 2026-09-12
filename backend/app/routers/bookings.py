from datetime import date, datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.database import get_db
from app.models import Booking, Equipment, Labor, User, Payment, Notification, UserRole, BookingStatus, PaymentStatus
from app.schemas import BookingCreate, BookingExtend, BookingReturn, BookingStatusUpdate, BookingResponse
from app.auth import get_current_active_user, require_role

router = APIRouter(prefix="/api/bookings", tags=["Bookings"])

def enrich_booking_item_details(booking: Booking, db: Session) -> dict:
    """Helper to attach equipment or labor details to booking dictionary."""
    if booking.item_type == "equipment":
        item = db.query(Equipment).filter(Equipment.id == booking.item_id).first()
        if item:
            return {
                "name": item.name,
                "category": item.category,
                "image_url": item.image_url,
                "location": item.location,
                "rate": item.rental_rate,
                "rate_unit": "per day"
            }
    elif booking.item_type == "labor":
        item = db.query(Labor).filter(Labor.id == booking.item_id).first()
        if item:
            return {
                "name": item.skill_type,
                "category": "Agricultural Labor",
                "image_url": None,
                "location": item.location,
                "rate": item.wage_rate,
                "rate_unit": "per day"
            }
    return {}

@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking_in: BookingCreate,
    current_user: User = Depends(require_role([UserRole.FARMER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """
    Create a new booking request with concurrency and conflict protection.
    Checks overlapping active bookings and calculates total cost.
    """
    # 1. Resolve item and owner
    if booking_in.item_type == "equipment":
        item = db.query(Equipment).filter(Equipment.id == booking_in.item_id).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
        if not item.is_available:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Equipment is currently not available for booking")
        owner_id = item.owner_id
        daily_rate = item.rental_rate
        item_title = item.name
    elif booking_in.item_type == "labor":
        item = db.query(Labor).filter(Labor.id == booking_in.item_id).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Labor profile not found")
        if not item.is_available:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Laborer is currently marked as not available")
        owner_id = item.user_id
        daily_rate = item.wage_rate
        item_title = f"{item.skill_type} (Labor)"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid item_type")

    # Farmer cannot rent their own listing
    if owner_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot book your own equipment or labor profile")

    # 2. Concurrency check: Ensure no overlapping confirmed or ongoing bookings
    conflict = db.query(Booking).filter(
        Booking.item_type == booking_in.item_type,
        Booking.item_id == booking_in.item_id,
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.ONGOING]),
        Booking.start_date <= booking_in.end_date,
        Booking.end_date >= booking_in.start_date
    ).first()

    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This {booking_in.item_type} is already booked from {conflict.start_date} to {conflict.end_date}. Please choose different dates."
        )

    # 3. Calculate total amount
    duration_days = (booking_in.end_date - booking_in.start_date).days + 1
    total_amount = round(duration_days * daily_rate, 2)

    # 4. Create booking
    booking = Booking(
        farmer_id=current_user.id,
        owner_id=owner_id,
        item_type=booking_in.item_type,
        item_id=booking_in.item_id,
        start_date=booking_in.start_date,
        end_date=booking_in.end_date,
        status=BookingStatus.PENDING,
        total_amount=total_amount,
        extension_days=0,
        late_fee=0.0
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    # 5. Create initial payment record
    payment = Payment(
        booking_id=booking.id,
        amount=total_amount,
        method="razorpay",
        status=PaymentStatus.PENDING
    )
    db.add(payment)

    # 6. Notifications
    notif_owner = Notification(
        user_id=owner_id,
        message=f"New booking request #{booking.id} from {current_user.name} for {item_title} ({booking.start_date} to {booking.end_date}). Total: ₹{total_amount}."
    )
    notif_farmer = Notification(
        user_id=current_user.id,
        message=f"Booking #{booking.id} created for {item_title}. Please complete payment of ₹{total_amount} to confirm."
    )
    db.add(notif_owner)
    db.add(notif_farmer)
    db.commit()

    # Response with enriched details
    res = BookingResponse.model_validate(booking)
    res.item_details = enrich_booking_item_details(booking, db)
    return res

@router.get("", response_model=List[BookingResponse])
def get_user_bookings(
    role_view: Optional[str] = Query(None, description="'farmer' or 'owner' perspective"),
    status_filter: Optional[str] = Query(None, description="Filter by booking status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retrieve all bookings related to the currently logged in user."""
    query = db.query(Booking)

    if current_user.role == UserRole.ADMIN:
        # Admin can view all or filter
        if role_view == "farmer":
            query = query.filter(Booking.farmer_id == current_user.id)
        elif role_view == "owner":
            query = query.filter(Booking.owner_id == current_user.id)
    elif current_user.role == UserRole.FARMER:
        query = query.filter(Booking.farmer_id == current_user.id)
    elif current_user.role in [UserRole.OWNER, UserRole.LABORER]:
        query = query.filter(Booking.owner_id == current_user.id)
    
    if status_filter:
        query = query.filter(Booking.status == status_filter.lower().strip())

    bookings = query.order_by(Booking.id.desc()).all()
    
    result = []
    for b in bookings:
        item_schema = BookingResponse.model_validate(b)
        item_schema.item_details = enrich_booking_item_details(b, db)
        result.append(item_schema)
    return result

@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking_by_id(
    booking_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retrieve details of a single booking with security authorization check."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.farmer_id != current_user.id and booking.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this booking")

    res = BookingResponse.model_validate(booking)
    res.item_details = enrich_booking_item_details(booking, db)
    return res

@router.patch("/{booking_id}/status", response_model=BookingResponse)
def update_booking_status(
    booking_id: int,
    status_update: BookingStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update booking lifecycle state.
    Owners/laborers approve handover ('ongoing'), mark complete ('completed'), or reject ('cancelled').
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the equipment owner or laborer can update this booking status"
        )

    target_status = status_update.status.lower().strip()
    old_status = booking.status

    # State transition validation
    if target_status == BookingStatus.ONGOING:
        if old_status not in [BookingStatus.CONFIRMED, BookingStatus.PENDING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot start booking from state '{old_status}'. Must be confirmed."
            )
    elif target_status == BookingStatus.COMPLETED:
        if old_status != BookingStatus.ONGOING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot complete booking from state '{old_status}'. Must be ongoing."
            )
        booking.return_date = date.today()

    booking.status = target_status
    db.commit()
    db.refresh(booking)

    # In-app notifications
    notif = Notification(
        user_id=booking.farmer_id,
        message=f"Your booking #{booking.id} status was updated to '{target_status.capitalize()}' by {current_user.name}."
    )
    db.add(notif)
    db.commit()

    res = BookingResponse.model_validate(booking)
    res.item_details = enrich_booking_item_details(booking, db)
    return res

@router.post("/{booking_id}/extend", response_model=BookingResponse)
def extend_booking(
    booking_id: int,
    extend_in: BookingExtend,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Extend an active booking by N days and recalculate additional fees."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.farmer_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the booking farmer can request extensions")

    if booking.status not in [BookingStatus.CONFIRMED, BookingStatus.ONGOING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Confirmed or Ongoing bookings can be extended"
        )

    new_end_date = booking.end_date + timedelta(days=extend_in.extension_days)

    # Check for conflict with upcoming bookings
    conflict = db.query(Booking).filter(
        Booking.id != booking.id,
        Booking.item_type == booking.item_type,
        Booking.item_id == booking.item_id,
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.ONGOING]),
        Booking.start_date <= new_end_date,
        Booking.end_date >= booking.end_date
    ).first()

    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot extend: Equipment is already booked by another farmer starting {conflict.start_date}."
        )

    # Determine daily rate
    if booking.item_type == "equipment":
        item = db.query(Equipment).filter(Equipment.id == booking.item_id).first()
        rate = item.rental_rate if item else 0
    else:
        item = db.query(Labor).filter(Labor.id == booking.item_id).first()
        rate = item.wage_rate if item else 0

    extra_fee = round(extend_in.extension_days * rate, 2)
    booking.end_date = new_end_date
    booking.extension_days += extend_in.extension_days
    booking.total_amount += extra_fee

    db.commit()
    db.refresh(booking)

    # Notify owner
    notif = Notification(
        user_id=booking.owner_id,
        message=f"Booking #{booking.id} has been extended by {extend_in.extension_days} day(s) until {booking.end_date}. Added fee: ₹{extra_fee}."
    )
    db.add(notif)
    db.commit()

    res = BookingResponse.model_validate(booking)
    res.item_details = enrich_booking_item_details(booking, db)
    return res

@router.post("/{booking_id}/return", response_model=BookingResponse)
def return_equipment(
    booking_id: int,
    return_in: BookingReturn,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Process equipment return and calculate late fees if overdue.
    Formula: late_fee = max(0, (return_date - end_date).days) * (rental_rate * 1.5)
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.owner_id != current_user.id and booking.farmer_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to process return")

    actual_return_date = return_in.return_date or date.today()
    booking.return_date = actual_return_date

    # Determine daily rate
    if booking.item_type == "equipment":
        item = db.query(Equipment).filter(Equipment.id == booking.item_id).first()
        rate = item.rental_rate if item else 0
    else:
        item = db.query(Labor).filter(Labor.id == booking.item_id).first()
        rate = item.wage_rate if item else 0

    if actual_return_date > booking.end_date:
        days_late = (actual_return_date - booking.end_date).days
        # Fixed penalty: 1.5x daily rental rate per late day
        late_fee = round(days_late * (rate * 1.5), 2)
        booking.late_fee = late_fee
        booking.total_amount += late_fee
    else:
        booking.late_fee = 0.0

    booking.status = BookingStatus.COMPLETED
    db.commit()
    db.refresh(booking)

    # Notify both farmer and owner
    msg = f"Booking #{booking.id} marked Completed on {actual_return_date}."
    if booking.late_fee > 0:
        msg += f" Overdue late fee applied: ₹{booking.late_fee}."
    
    db.add(Notification(user_id=booking.farmer_id, message=msg))
    db.add(Notification(user_id=booking.owner_id, message=msg))
    db.commit()

    res = BookingResponse.model_validate(booking)
    res.item_details = enrich_booking_item_details(booking, db)
    return res

@router.post("/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(
    booking_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancel booking with authorization checks."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.farmer_id != current_user.id and booking.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to cancel this booking")

    if booking.status in [BookingStatus.COMPLETED, BookingStatus.CANCELLED]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot cancel a booking that is already {booking.status}")

    booking.status = BookingStatus.CANCELLED
    db.commit()
    db.refresh(booking)

    # Notify other party
    other_party_id = booking.owner_id if current_user.id == booking.farmer_id else booking.farmer_id
    notif = Notification(
        user_id=other_party_id,
        message=f"Booking #{booking.id} was cancelled by {current_user.name}."
    )
    db.add(notif)
    db.commit()

    res = BookingResponse.model_validate(booking)
    res.item_details = enrich_booking_item_details(booking, db)
    return res
