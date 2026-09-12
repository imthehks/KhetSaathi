import pytest
from app.models import Equipment

def test_unauthenticated_request_blocked(client):
    """Test unauthenticated request to protected endpoint returns 401."""
    response = client.get("/api/users/me")
    assert response.status_code == 401

def test_farmer_blocked_from_owner_endpoint(client, farmer_headers):
    """Test farmer attempting to list equipment is blocked with 403."""
    response = client.post(
        "/api/equipment",
        headers=farmer_headers,
        json={
            "name": "Unauthorized Tractor",
            "category": "Tractor",
            "rental_rate": 1200.0,
            "location": "Ludhiana"
        }
    )
    assert response.status_code == 403
    assert "Access forbidden" in response.json()["detail"]

def test_farmer_blocked_from_admin_endpoint(client, farmer_headers):
    """Test farmer attempting to access admin stats is blocked with 403."""
    response = client.get("/api/admin/stats", headers=farmer_headers)
    assert response.status_code == 403

def test_admin_allowed_access_to_admin_endpoint(client, admin_headers):
    """Test admin has access to admin stats with 200."""
    response = client.get("/api/admin/stats", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_users" in data
    assert "total_bookings" in data

def test_owner_cannot_modify_other_owner_equipment(client, db_session, owner_headers, test_users):
    """Test owner cannot update an equipment listing belonging to another owner."""
    other_owner_item = Equipment(
        owner_id=test_users["admin"].id,  # Owned by admin/other user
        name="Other Owner Harvester",
        category="Harvester",
        rental_rate=3000.0,
        location="Amritsar"
    )
    db_session.add(other_owner_item)
    db_session.commit()
    db_session.refresh(other_owner_item)

    response = client.put(
        f"/api/equipment/{other_owner_item.id}",
        headers=owner_headers,
        json={"rental_rate": 2500.0}
    )
    assert response.status_code == 403
    assert "do not have permission" in response.json()["detail"]
