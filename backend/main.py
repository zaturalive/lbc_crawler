import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.database import create_tables
from routers import admin, listings, patterns, search, vehicles
from routers.history import router as history_router
from routers.analysis import router as analysis_router
from routers.auth import router as auth_router
from routers.likes import router as likes_router
from routers.users import router as users_router
from routers.payments import router as payments_router
from routers.credits import router as credits_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(title="find_my_car API", version="1.0.0", lifespan=lifespan)

cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=(cors_origins != ["*"]),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(listings.router)
app.include_router(vehicles.router)
app.include_router(patterns.router)
app.include_router(admin.router)
app.include_router(likes_router, tags=["likes"])
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(analysis_router)
app.include_router(history_router)
app.include_router(payments_router)
app.include_router(credits_router)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
