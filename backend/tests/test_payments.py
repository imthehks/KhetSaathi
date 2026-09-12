import pytest
import hmac
import hashlib
from datetime import date, timedelta
from app.config import settings
from app.models import Booking, Payment, BookingStatus, PaymentStatus

def test_create_razorpay_order(client, db_session, farmer_headers, test_users, test_equipment):
    """Test generating a Razorpay order for a pending booking."""
    booking = Booking(
        farmer_id=test_users["farmer"].id,
        owner_id=test_users["owner"].id,
        item_type="equipment",
        item_id=test_equipment.id,
        start_date=date.today() + timedelta(days=1),
        end_date=date.today() + timedelta(days=2),
        status=BookingStatus.PENDING,
        total_amount=2000.0
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)

    response = client.post(
        "/api/payments/create-order",
        headers=farmer_headers,
        json={"booking_id": booking.id}
    )
    assert response.status_code == 200
    data = response.json()
    assert "order_id" in data
    assert data["amount"] == 200000  # 2000 INR = 200,000 paise
    assert data["booking_id"] == booking.id

def test_payment_signature_verification_success(client, db_session, farmer_headers, test_users, test_equipment):
    """Test valid Razorpay signature confirms the booking."""
    booking = Booking(
        farmer_id=test_users["farmer"].id,
        owner_id=test_users["owner"].id,
        item_type="equipment",
        item_id=test_equipment.id,
        start_date=date.today() + timedelta(days=1),
        end_date=date.today() + timedelta(days=2),
        status=BookingStatus.PENDING,
        total_amount=2000.0
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)

    order_id = f"order_test_{booking.id}"
    payment_id = "pay_test_12345"

    # Compute valid signature
    message = f"{order_id}|{payment_id}"
    valid_sig = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    payment = Payment(
        booking_id=booking.id,
        amount=2000.0,
        razorpay_order_id=order_id,
        status=PaymentStatus.PENDING
    )
    db_session.add(payment)
    db_session.commit()

    response = client.post(
        "/api/payments/verify",
        headers=farmer_headers,
        json={
            "booking_id": booking.id,
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": valid_sig
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["booking_status"] == "confirmed"

    # Verify state in DB
    db_session.refresh(booking)
    db_session.refresh(payment)
    assert booking.status == BookingStatus.CONFIRMED
    assert payment.status == PaymentStatus.SUCCESS

def test_payment_signature_verification_failure(client, db_session, farmer_headers, test_users, test_equipment):
    """Test invalid signature fails verification and returns 400."""
    booking = Booking(
        farmer_id=test_users["farmer"].id,
        owner_id=test_users["owner"].id,
        item_type="equipment",
        item_id=test_equipment.id,
        start_date=date.today() + timedelta(days=1),
        end_date=date.today() + timedelta(days=2),
        status=BookingStatus.PENDING,
        total_amount=2000.0
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)

    payment = Payment(
        booking_id=booking.id,
        amount=2000.0,
        razorpay_order_id="order_tampered",
        status=PaymentStatus.PENDING
    )
    db_session.add(payment)
    db_session.commit()

    response = client.post(
        "/api/payments/verify",
        headers=farmer_headers,
        json={
            "booking_id": booking.id,
            "razorpay_order_id": "order_tampered",
            "razorpay_payment_id": "pay_fake",
            "razorpay_signature": "invalid_forged_signature"
        }
    )
    assert response.status_code == 400
    assert "Invalid payment signature" in response.json()["detail"]

    # Verify booking remains pending and payment is marked failed
    db_session.refresh(booking)
    db_session.refresh(payment)
    assert booking.status == BookingStatus.PENDING
    assert payment.status == PaymentStatus.FAILED
