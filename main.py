from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Auth routers
from services.auth.wallet.auth_router import router as wallet_auth_router
from services.auth.email.auth_router import router as email_auth_router
from services.auth.protected_routes import router as protected_router

# Endpoint routers
from services.endpoint.recycle import router as recycle_router
from services.endpoint.analytics import router as analytics_router
from services.endpoint.schedule import router as schedule_router
from services.endpoint.thumbnail import router as thumbnail_router
from services.endpoint.content import router as content_router
from services.endpoint.ab_test import router as ab_test_router
from services.endpoint.engage import router as engage_router
from services.endpoint.customize import router as customize_router

# Database setup
from services.database.database import Base, engine
from services.database import postgresql, mongodb, redis

app = FastAPI()

# -------------------------------
# 🔌 Connect to External Services
# -------------------------------
@app.on_event("startup")
async def connect_services():
    # Initialize PostgreSQL pool
    await postgresql.init_db_pool()
    print("✅ PostgreSQL Connected")

    # MongoDB is initialized on import
    print("✅ MongoDB Connected:", mongodb.db.name)

    # Test Redis connection
    print("✅ Redis Connected:", await redis.redis.ping())

# -------------------------------
# 🔌 Graceful Shutdown
# -------------------------------
@app.on_event("shutdown")
async def shutdown_services():
    await postgresql.close_db_pool()
    print("🔌 PostgreSQL Connection Closed")

# -------------------------------
# Database Table Initialization
# -------------------------------
Base.metadata.create_all(bind=engine)

# -------------------------------
# Enable CORS for Frontend
# -------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://social-suit-landing.vercel.app/"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# Include Routers
# -------------------------------
app.include_router(content_router, prefix="/api/v1")
app.include_router(schedule_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(recycle_router, prefix="/api/v1")
app.include_router(ab_test_router, prefix="/api/v1")
app.include_router(thumbnail_router, prefix="/api/v1")
app.include_router(engage_router, prefix="/api/v1")
app.include_router(customize_router, prefix="/api/v1")

# Auth routes
app.include_router(wallet_auth_router, prefix="/auth")
app.include_router(email_auth_router, prefix="/auth")
app.include_router(protected_router, prefix="/auth")

# -------------------------------
# Root Endpoint
# -------------------------------
@app.get("/")
def home():
    return {"msg": "🚀 Social Suit Backend Running"}



