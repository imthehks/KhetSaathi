import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import User, Equipment, Labor, Booking, Payment, UserRole, BookingStatus, PaymentStatus
from app.auth import get_password_hash, create_access_token

# In-memory SQLite engine for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Creates a fresh test database schema for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_users(db_session):
    """Seed test users for each role."""
    users = {
        "farmer": User(
            name="Test Farmer",
            email="farmer_test@khetsaathi.com",
            password_hash=get_password_hash("pass123"),
            role=UserRole.FARMER,
            phone="9876543210",
            address="Test Village",
            is_active=True
        ),
        "owner": User(
            name="Test Owner",
            email="owner_test@khetsaathi.com",
            password_hash=get_password_hash("pass123"),
            role=UserRole.OWNER,
            phone="9876543211",
            address="Test Town",
            is_active=True
        ),
        "laborer": User(
            name="Test Laborer",
            email="laborer_test@khetsaathi.com",
            password_hash=get_password_hash("pass123"),
            role=UserRole.LABORER,
            phone="9876543212",
            address="Test District",
            is_active=True
        ),
        "admin": User(
            name="Test Admin",
            email="admin_test@khetsaathi.com",
            password_hash=get_password_hash("pass123"),
            role=UserRole.ADMIN,
            phone="9876543213",
            address="Test City",
            is_active=True
        ),
    }
    for u in users.values():
        db_session.add(u)
    db_session.commit()
    for u in users.values():
        db_session.refresh(u)
    return users

@pytest.fixture(scope="function")
def farmer_token(test_users):
    user = test_users["farmer"]
    return create_access_token({"sub": user.email, "role": user.role, "id": user.id})

@pytest.fixture(scope="function")
def owner_token(test_users):
    user = test_users["owner"]
    return create_access_token({"sub": user.email, "role": user.role, "id": user.id})

@pytest.fixture(scope="function")
def laborer_token(test_users):
    user = test_users["laborer"]
    return create_access_token({"sub": user.email, "role": user.role, "id": user.id})

@pytest.fixture(scope="function")
def admin_token(test_users):
    user = test_users["admin"]
    return create_access_token({"sub": user.email, "role": user.role, "id": user.id})

@pytest.fixture(scope="function")
def farmer_headers(farmer_token):
    return {"Authorization": f"Bearer {farmer_token}"}

@pytest.fixture(scope="function")
def owner_headers(owner_token):
    return {"Authorization": f"Bearer {owner_token}"}

@pytest.fixture(scope="function")
def laborer_headers(laborer_token):
    return {"Authorization": f"Bearer {laborer_token}"}

@pytest.fixture(scope="function")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture(scope="function")
def test_equipment(db_session, test_users):
    """Seed test equipment."""
    owner = test_users["owner"]
    equipment = Equipment(
        owner_id=owner.id,
        name="Test Swaraj Tractor",
        category="Tractor",
        rental_rate=1000.0,
        location="Amritsar, Punjab",
        description="Reliable test tractor",
        image_url=None,
        is_available=True
    )
    db_session.add(equipment)
    db_session.commit()
    db_session.refresh(equipment)
    return equipment

@pytest.fixture(scope="function")
def test_labor(db_session, test_users):
    """Seed test labor profile."""
    laborer = test_users["laborer"]
    labor = Labor(
        user_id=laborer.id,
        skill_type="Tractor Driver",
        wage_rate=500.0,
        location="Meerut, UP",
        description="Expert operator",
        is_available=True
    )
    db_session.add(labor)
    db_session.commit()
    db_session.refresh(labor)
    return labor
