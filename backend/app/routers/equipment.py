from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Equipment, User, UserRole
from app.schemas import EquipmentCreate, EquipmentUpdate, EquipmentResponse
from app.auth import get_current_active_user, require_role
from app.cloudinary_util import upload_image

router = APIRouter(prefix="/api/equipment", tags=["Equipment"])

@router.get("", response_model=List[EquipmentResponse])
def list_equipment(
    q: Optional[str] = Query(None, description="Search query in name or description"),
    category: Optional[str] = Query(None, description="Filter by category"),
    location: Optional[str] = Query(None, description="Filter by location"),
    min_rate: Optional[float] = Query(None, ge=0, description="Minimum rental rate"),
    max_rate: Optional[float] = Query(None, ge=0, description="Maximum rental rate"),
    available_only: bool = Query(False, description="Filter by availability"),
    owner_id: Optional[int] = Query(None, description="Filter by owner ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List and search farm equipment with multi-parameter filtering."""
    query = db.query(Equipment)

    if q:
        search_pattern = f"%{q.strip()}%"
        query = query.filter(
            (Equipment.name.ilike(search_pattern)) | 
            (Equipment.description.ilike(search_pattern))
        )
    if category:
        query = query.filter(Equipment.category.ilike(f"%{category.strip()}%"))
    if location:
        query = query.filter(Equipment.location.ilike(f"%{location.strip()}%"))
    if min_rate is not None:
        query = query.filter(Equipment.rental_rate >= min_rate)
    if max_rate is not None:
        query = query.filter(Equipment.rental_rate <= max_rate)
    if available_only:
        query = query.filter(Equipment.is_available == True)
    if owner_id is not None:
        query = query.filter(Equipment.owner_id == owner_id)

    equipment_list = query.order_by(Equipment.id.desc()).offset(skip).limit(limit).all()
    return equipment_list

@router.get("/categories", response_model=List[str])
def get_equipment_categories(db: Session = Depends(get_db)):
    """Return all unique equipment categories currently available."""
    categories = db.query(Equipment.category).distinct().all()
    standard_categories = ["Tractor", "Harvester", "Seeder & Planter", "Rotavator & Tillage", "Irrigation & Pumps", "Sprayer", "Laser Land Leveler", "Other"]
    db_categories = [c[0] for c in categories if c[0]]
    combined = sorted(list(set(standard_categories + db_categories)))
    return combined

@router.get("/{equipment_id}", response_model=EquipmentResponse)
def get_equipment_by_id(equipment_id: int, db: Session = Depends(get_db)):
    """Retrieve details of a specific piece of equipment."""
    item = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    return item

@router.post("", response_model=EquipmentResponse, status_code=status.HTTP_201_CREATED)
def create_equipment(
    equipment_in: EquipmentCreate,
    current_user: User = Depends(require_role([UserRole.OWNER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Create a new equipment listing. Only accessible to Equipment Owners and Admins."""
    item = Equipment(
        owner_id=current_user.id,
        name=equipment_in.name.strip(),
        category=equipment_in.category.strip(),
        rental_rate=equipment_in.rental_rate,
        location=equipment_in.location.strip(),
        description=equipment_in.description.strip() if equipment_in.description else None,
        image_url=equipment_in.image_url.strip() if equipment_in.image_url else None,
        is_available=equipment_in.is_available
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.post("/upload-image")
def upload_equipment_image(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role([UserRole.OWNER, UserRole.ADMIN]))
):
    """Upload an equipment image to Cloudinary (or local fallback)."""
    image_url = upload_image(file)
    if not image_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to upload image. Please try again."
        )
    return {"image_url": image_url}

@router.put("/{equipment_id}", response_model=EquipmentResponse)
def update_equipment(
    equipment_id: int,
    equipment_update: EquipmentUpdate,
    current_user: User = Depends(require_role([UserRole.OWNER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Update equipment details with strict ownership verification."""
    item = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    
    # Ownership check: only the owner or an admin can modify
    if item.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this equipment"
        )

    if equipment_update.name is not None:
        item.name = equipment_update.name.strip()
    if equipment_update.category is not None:
        item.category = equipment_update.category.strip()
    if equipment_update.rental_rate is not None:
        item.rental_rate = equipment_update.rental_rate
    if equipment_update.location is not None:
        item.location = equipment_update.location.strip()
    if equipment_update.description is not None:
        item.description = equipment_update.description.strip()
    if equipment_update.image_url is not None:
        item.image_url = equipment_update.image_url.strip()
    if equipment_update.is_available is not None:
        item.is_available = equipment_update.is_available

    db.commit()
    db.refresh(item)
    return item

@router.patch("/{equipment_id}/toggle-availability", response_model=EquipmentResponse)
def toggle_equipment_availability(
    equipment_id: int,
    current_user: User = Depends(require_role([UserRole.OWNER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Toggle whether equipment is currently available for rent."""
    item = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    
    if item.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this equipment"
        )

    item.is_available = not item.is_available
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipment(
    equipment_id: int,
    current_user: User = Depends(require_role([UserRole.OWNER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Delete an equipment listing with ownership check."""
    item = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    
    if item.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this equipment"
        )

    db.delete(item)
    db.commit()
    return None
