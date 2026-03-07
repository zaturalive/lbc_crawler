from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from models import Vehicle
from schemas import VehicleResponse

router = APIRouter()


@router.get("/vehicles", response_model=list[VehicleResponse])
async def list_vehicles(
    brand: str | None = None,
    model: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Sans paramètres : retourne tous les véhicules (max 500).
    Avec brand + model : retourne le véhicule correspondant (liste d'un élément ou vide).
    """
    query = select(Vehicle)
    if brand:
        query = query.where(Vehicle.brand == brand)
    if model:
        query = query.where(Vehicle.model == model)
    query = query.limit(500)
    result = await db.execute(query)
    vehicles = result.scalars().all()
    if brand and model and not vehicles:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return [VehicleResponse.model_validate(v) for v in vehicles]
