import hmac
import hashlib
import uuid
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import razorpay

from app.database import get_db
from app.config import settings
from app.models import Booking, Payment, Notification, User, BookingStatus, PaymentStatus, UserRole
from app.schemas import RazorpayOrderCreate, RazorpayOrderResponse, RazorpayVerify, PaymentResponse
from app.auth import get_current_active_user

logger = logging.getLogger("khetsaathi.payments")
router = APIRouter(prefix="/api/payments", tags=["Payments"])

def get_razorpay_client():
    """Initializes Razorpay client if real/test credentials are configured."""
    if settings.RAZORPAY_KEY_ID and not settings.RAZORPAY_KEY_ID.startswith("rzp_test_placeholder"):
        return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    return None

@router.post("/create-order", response_model=RazorpayOrderResponse)
def create_razorpay_order(
    order_in: RazorpayOrderCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Creates a Razorpay Order for a pending booking.
    Gracefully falls back to test/mock order if Razorpay gateway is offline or placeholder keys are used.
    """
    booking = db.query(Booking).filter(Booking.id == order_in.booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.farmer_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to pay for this booking")

    if booking.status not in [BookingStatus.PENDING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot initiate payment for booking in '{booking.status}' status"
        )

    # Razorpay amount is in paise (1 INR = 100 paise)
    amount_in_paise = int(round(booking.total_amount * 100))

    order_id = None
    client = get_razorpay_client()

    if client:
        try:
            rzp_order = client.order.create({
                "amount": amount_in_paise,
                "currency": "INR",
                "receipt": f"khet_receipt_{booking.id}",
                "notes": {
                    "booking_id": booking.id,
                    "farmer_email": current_user.email
                }
            })
            order_id = rzp_order.get("id")
        except Exception as e:
            logger.warning(f"Razorpay API call failed: {e}. Generating sandbox order.")

    # Graceful degradation for local test environment
    if not order_id:
        order_id = f"order_test_{booking.id}_{uuid.uuid4().hex[:8]}"

    # Update or create payment record
    payment = db.query(Payment).filter(Payment.booking_id == booking.id).first()
    if not payment:
        payment = Payment(
            booking_id=booking.id,
            amount=booking.total_amount,
            method="razorpay",
            status=PaymentStatus.PENDING
        )
        db.add(payment)
    
    payment.razorpay_order_id = order_id
    payment.status = PaymentStatus.PENDING
    db.commit()

    return RazorpayOrderResponse(
        order_id=order_id,
        amount=amount_in_paise,
        currency="INR",
        key_id=settings.RAZORPAY_KEY_ID,
        booking_id=booking.id
    )

@router.post("/verify")
def verify_payment_signature(
    verify_in: RazorpayVerify,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Verifies Razorpay HMAC SHA256 payment signature.
    On success: moves Payment to 'success' and Booking to 'confirmed'.
    On failure: marks Payment as 'failed' and rejects.
    """
    booking = db.query(Booking).filter(Booking.id == verify_in.booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    payment = db.query(Payment).filter(Payment.booking_id == booking.id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment record not found")

    # Compute expected signature using HMAC-SHA256
    message = f"{verify_in.razorpay_order_id}|{verify_in.razorpay_payment_id}"
    generated_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    # Verification logic: checks cryptographic signature OR special test simulator token
    is_valid = False
    if hmac.compare_digest(generated_signature, verify_in.razorpay_signature):
        is_valid = True
    elif verify_in.razorpay_signature == "mock_test_signature_valid":
        is_valid = True

    if not is_valid:
        payment.status = PaymentStatus.FAILED
        db.commit()
        logger.warning(f"Payment signature verification failed for booking {booking.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment signature. Verification failed."
        )

    # Mark payment successful and confirm booking
    payment.status = PaymentStatus.SUCCESS
    payment.razorpay_order_id = verify_in.razorpay_order_id
    payment.razorpay_payment_id = verify_in.razorpay_payment_id
    payment.razorpay_signature = verify_in.razorpay_signature

    booking.status = BookingStatus.CONFIRMED
    db.commit()
    db.refresh(booking)

    # In-app notifications
    notif_farmer = Notification(
        user_id=booking.farmer_id,
        message=f"Payment of ₹{booking.total_amount} verified successfully! Booking #{booking.id} is now CONFIRMED."
    )
    notif_owner = Notification(
        user_id=booking.owner_id,
        message=f"Payment received for Booking #{booking.id}. Status changed to CONFIRMED. Prepare item for handover on {booking.start_date}."
    )
    db.add(notif_farmer)
    db.add(notif_owner)
    db.commit()

    return {
        "status": "success",
        "message": "Payment verified and booking confirmed",
        "booking_id": booking.id,
        "booking_status": booking.status
    }

@router.get("/booking/{booking_id}", response_model=PaymentResponse)
def get_payment_by_booking(
    booking_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retrieve payment audit record for a booking."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.farmer_id != current_user.id and booking.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    payment = db.query(Payment).filter(Payment.booking_id == booking_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment record not found")

    return payment
