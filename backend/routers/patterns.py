import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from models import RegexPattern
from schemas import PatternCreate, PatternResponse

router = APIRouter()


@router.get("/patterns", response_model=list[PatternResponse])
async def list_patterns(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RegexPattern).order_by(RegexPattern.is_default.desc(), RegexPattern.id))
    return [PatternResponse.model_validate(p) for p in result.scalars().all()]


@router.post("/patterns", response_model=PatternResponse, status_code=201)
async def create_pattern(data: PatternCreate, db: AsyncSession = Depends(get_db)):
    try:
        re.compile(data.pattern)
    except re.error as exc:
        raise HTTPException(status_code=422, detail=f"Invalid regex: {exc}")

    pattern = RegexPattern(name=data.name, pattern=data.pattern, description=data.description)
    db.add(pattern)
    await db.commit()
    await db.refresh(pattern)
    return PatternResponse.model_validate(pattern)


@router.delete("/patterns/{pattern_id}", status_code=204)
async def delete_pattern(pattern_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RegexPattern).where(RegexPattern.id == pattern_id))
    pattern = result.scalar_one_or_none()
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    if pattern.is_default:
        raise HTTPException(status_code=403, detail="Cannot delete a default pattern")
    await db.delete(pattern)
    await db.commit()
