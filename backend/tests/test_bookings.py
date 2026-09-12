import pytest
from datetime import date, timedelta
from app.models import Booking, BookingStatus

def test_create_booking_valid(client, farmer_headers, test_equipment):
    """Test creating a valid booking request for equipment."""
    today = date.today()
    start = today + timedelta(days=1)
    end = today + timedelta(days=3)  # 3 days inclusive

    response = client.post(
        "/api/bookings",
        headers=farmer_headers,
        json={
            "item_type": "equipment",
            "item_id": test_equipment.id,
            "start_date": start.isoformat(),
            "end_date": end.isoformat()
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    # rate is 1000/day, 3 days = 3000.0
    assert data["total_amount"] == 3000.0
    assert data["item_type"] == "equipment"

def test_booking_end_before_start_rejected(client, farmer_headers, test_equipment):
    """Test that end_date earlier than start_date is rejected with 422."""
    today = date.today()
    start = today + timedelta(days=5)
    end = today + timedelta(days=2)  # Invalid: before start

    response = client.post(
        "/api/bookings",
        headers=farmer_headers,
        json={
            "item_type": "equipment",
            "item_id": test_equipment.id,
            "start_date": start.isoformat(),
            "end_date": end.isoformat()
        }
    )
    assert response.status_code == 422
    assert "end_date cannot be earlier than start_date" in response.json()["detail"]

def test_booking_conflict_overlap_rejected(client, db_session, farmer_headers, test_users, test_equipment):
    """Test that overlapping booking dates for an already confirmed booking are rejected with 409 Conflict."""
    today = date.today()
    start = today + timedelta(days=2)
    end = today + timedelta(days=6)

    # Insert an existing confirmed booking
    existing = Booking(
        farmer_id=test_users["farmer"].id,
        owner_id=test_users["owner"].id,
        item_type="equipment",
        item_id=test_equipment.id,
        start_date=start,
        end_date=end,
        status=BookingStatus.CONFIRMED,
        total_amount=5000.0
    )
    db_session.add(existing)
    db_session.commit()

    # Attempt to book overlapping dates (e.g. days 4 to 8)
    response = client.post(
        "/api/bookings",
        headers=farmer_headers,
        json={
            "item_type": "equipment",
            "item_id": test_equipment.id,
            "start_date": (today + timedelta(days=4)).isoformat(),
            "end_date": (today + timedelta(days=8)).isoformat()
        }
    )
    assert response.status_code == 409
    assert "already booked" in response.json()["detail"]

def test_owner_approve_booking(client, db_session, owner_headers, test_users, test_equipment):
    """Test owner transitioning a confirmed booking to ongoing."""
    today = date.today()
    booking = Booking(
        farmer_id=test_users["farmer"].id,
        owner_id=test_users["owner"].id,
        item_type="equipment",
        item_id=test_equipment.id,
        start_date=today,
        end_date=today + timedelta(days=2),
        status=BookingStatus.CONFIRMED,
        total_amount=3000.0
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)

    response = client.patch(
        f"/api/bookings/{booking.id}/status",
        headers=owner_headers,
        json={"status": "ongoing"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ongoing"

def test_late_fee_calculation_on_return(client, db_session, owner_headers, test_users, test_equipment):
    """
    Test equipment return calculates late fees when overdue.
    Daily rate = 1000. Penalty = 1.5x = 1500/day.
    Returned 2 days late -> late_fee = 3000.
    """
    past_start = date.today() - timedelta(days=5)
    past_end = date.today() - timedelta(days=2)  # was due 2 days ago

    booking = Booking(
        farmer_id=test_users["farmer"].id,
        owner_id=test_users["owner"].id,
        item_type="equipment",
        item_id=test_equipment.id,
        start_date=past_start,
        end_date=past_end,
        status=BookingStatus.ONGOING,
        total_amount=4000.0
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)

    # Return today (2 days late)
    response = client.post(
        f"/api/bookings/{booking.id}/return",
        headers=owner_headers,
        json={"return_date": date.today().isoformat()}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["late_fee"] == 3000.0  # 2 days * (1000 * 1.5)
    assert data["total_amount"] == 7000.0  # 4000 + 3000
