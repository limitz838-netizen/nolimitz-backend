from app.routes.licenses import router as license_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.clients import router as clients_router
from app.routes.signals import router as signals_router

from app.database import Base, engine
from app.routes.admin_auth import router as admin_auth_router
from app.routes.profile import router as profile_router
from app.routes.ea import router as ea_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Nolimitz SaaS Backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://nolimitz-client-5bv1v4fbx-limitz838-2833s-projects.vercel.app",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_auth_router)
app.include_router(profile_router)
app.include_router(ea_router)
app.include_router(license_router)
app.include_router(clients_router)
app.include_router(signals_router)

@app.get("/")
def root():
    return {
        "message": "Nolimitz SaaS Backend is running"
    }