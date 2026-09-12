import pytest

def test_register_valid_user(client):
    """Test valid user registration with role."""
    response = client.post(
        "/api/users/register",
        json={
            "name": "New Farmer",
            "email": "newfarmer@example.com",
            "password": "strongpassword123",
            "role": "farmer",
            "phone": "+91 91234 56789",
            "address": "Sonipat, Haryana"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newfarmer@example.com"
    assert data["role"] == "farmer"
    assert "password_hash" not in data

def test_register_duplicate_email_rejected(client, test_users):
    """Test registration with duplicate email is rejected with 400."""
    response = client.post(
        "/api/users/register",
        json={
            "name": "Duplicate Farmer",
            "email": "farmer_test@khetsaathi.com",  # already exists in fixture
            "password": "password123",
            "role": "farmer"
        }
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_login_valid_credentials(client, test_users):
    """Test login with valid email and password returns JWT token."""
    response = client.post(
        "/api/users/login",
        json={
            "email": "farmer_test@khetsaathi.com",
            "password": "pass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "farmer_test@khetsaathi.com"

def test_login_invalid_password(client, test_users):
    """Test login with invalid password is rejected with 401."""
    response = client.post(
        "/api/users/login",
        json={
            "email": "farmer_test@khetsaathi.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

def test_get_current_user_profile(client, farmer_headers):
    """Test fetching /me profile with valid Bearer token."""
    response = client.get("/api/users/me", headers=farmer_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "farmer_test@khetsaathi.com"
    assert data["role"] == "farmer"
