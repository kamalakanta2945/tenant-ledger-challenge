from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, SessionLocal, engine
from app.dependencies import api_key_hash
from app.models import Tenant
from app.routers import clients, transactions


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        demos = (
            ("Tenant A", "tenant-a-demo-key"),
            ("Tenant B", "tenant-b-demo-key"),
        )
        for name, api_key in demos:
            existing = db.query(Tenant).filter(
                Tenant.api_key_hash == api_key_hash(api_key)
            ).first()
            if existing is None:
                db.add(Tenant(name=name, api_key_hash=api_key_hash(api_key)))
        db.commit()
    yield


app = FastAPI(
    title="Tenant Ledger API",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(transactions.router)
app.include_router(clients.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
