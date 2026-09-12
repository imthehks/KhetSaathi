from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Labor, User, UserRole
from app.schemas import LaborCreate, LaborUpdate, LaborResponse
from app.auth import get_current_active_user, require_role

router = APIRouter(prefix="/api/labor", tags=["Labor"])

@router.get("", response_model=List[LaborResponse])
def list_labor(
    q: Optional[str] = Query(None, description="Search query in skill or description"),
    skill_type: Optional[str] = Query(None, description="Filter by skill type"),
    location: Optional[str] = Query(None, description="Filter by location"),
    max_wage: Optional[float] = Query(None, ge=0, description="Maximum wage rate per day"),
    available_only: bool = Query(False, description="Filter by availability"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List and search farm laborers by skill, wage, and location."""
    query = db.query(Labor).join(User, Labor.user_id == User.id).filter(User.is_active == True)

    if q:
        search_pattern = f"%{q.strip()}%"
        query = query.filter(
            (Labor.skill_type.ilike(search_pattern)) | 
            (Labor.description.ilike(search_pattern)) |
            (User.name.ilike(search_pattern))
        )
    if skill_type:
        query = query.filter(Labor.skill_type.ilike(f"%{skill_type.strip()}%"))
    if location:
        query = query.filter(Labor.location.ilike(f"%{location.strip()}%"))
    if max_wage is not None:
        query = query.filter(Labor.wage_rate <= max_wage)
    if available_only:
        query = query.filter(Labor.is_available == True)

    labor_list = query.order_by(Labor.id.desc()).offset(skip).limit(limit).all()
    return labor_list

@router.get("/skills", response_model=List[str])
def get_available_skills(db: Session = Depends(get_db)):
    """Return all unique labor skills currently listed."""
    skills = db.query(Labor.skill_type).distinct().all()
    standard_skills = [
        "Tractor Driver & Operator",
        "Harvesting Expert",
        "Sowing & Transplanting",
        "Pesticide & Fertilizer Spraying",
        "General Farm Labor",
        "Irrigation & Drip Specialist",
        "Crop Pruning & Weeding"
    ]
    db_skills = [s[0] for s in skills if s[0]]
    combined = sorted(list(set(standard_skills + db_skills)))
    return combined

@router.get("/me", response_model=LaborResponse)
def get_my_labor_profile(
    current_user: User = Depends(require_role([UserRole.LABORER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Retrieve the labor profile for the currently logged-in laborer."""
    profile = db.query(Labor).filter(Labor.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Labor profile not found. Please create one."
        )
    return profile

@router.get("/{labor_id}", response_model=LaborResponse)
def get_labor_by_id(labor_id: int, db: Session = Depends(get_db)):
    """Retrieve details of a specific laborer profile."""
    profile = db.query(Labor).filter(Labor.id == labor_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Labor profile not found")
    return profile

@router.post("", response_model=LaborResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_labor_profile(
    labor_in: LaborCreate,
    current_user: User = Depends(require_role([UserRole.LABORER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Create or update a labor profile. Each laborer has one profile."""
    existing = db.query(Labor).filter(Labor.user_id == current_user.id).first()
    if existing:
        existing.skill_type = labor_in.skill_type.strip()
        existing.wage_rate = labor_in.wage_rate
        existing.location = labor_in.location.strip()
        existing.description = labor_in.description.strip() if labor_in.description else None
        existing.is_available = labor_in.is_available
        db.commit()
        db.refresh(existing)
        return existing

    profile = Labor(
        user_id=current_user.id,
        skill_type=labor_in.skill_type.strip(),
        wage_rate=labor_in.wage_rate,
        location=labor_in.location.strip(),
        description=labor_in.description.strip() if labor_in.description else None,
        is_available=labor_in.is_available
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

@router.put("/{labor_id}", response_model=LaborResponse)
def update_labor_profile(
    labor_id: int,
    labor_update: LaborUpdate,
    current_user: User = Depends(require_role([UserRole.LABORER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Update laborer details with ownership verification."""
    profile = db.query(Labor).filter(Labor.id == labor_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Labor profile not found")

    if profile.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this profile"
        )

    if labor_update.skill_type is not None:
        profile.skill_type = labor_update.skill_type.strip()
    if labor_update.wage_rate is not None:
        profile.wage_rate = labor_update.wage_rate
    if labor_update.location is not None:
        profile.location = labor_update.location.strip()
    if labor_update.description is not None:
        profile.description = labor_update.description.strip()
    if labor_update.is_available is not None:
        profile.is_available = labor_update.is_available

    db.commit()
    db.refresh(profile)
    return profile

@router.patch("/{labor_id}/toggle-availability", response_model=LaborResponse)
def toggle_labor_availability(
    labor_id: int,
    current_user: User = Depends(require_role([UserRole.LABORER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Toggle laborer's work availability status."""
    profile = db.query(Labor).filter(Labor.id == labor_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Labor profile not found")

    if profile.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this profile"
        )

    profile.is_available = not profile.is_available
    db.commit()
    db.refresh(profile)
    return profile
