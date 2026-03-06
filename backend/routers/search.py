from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from schemas import SearchRequest, SearchResult
from services.search_service import run_search

router = APIRouter()


@router.post("/search", response_model=SearchResult)
async def search(req: SearchRequest, db: AsyncSession = Depends(get_db)):
    result = await run_search(req, db)
    return result
