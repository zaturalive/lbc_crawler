from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from models import Vehicle
from schemas import VehicleResponse

router = APIRouter()


@router.get("/vehicles", response_model=VehicleResponse)
async def get_vehicle(brand: str, model: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Vehicle).where(Vehicle.brand == brand, Vehicle.model == model).limit(1)
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return VehicleResponse.model_validate(vehicle)
