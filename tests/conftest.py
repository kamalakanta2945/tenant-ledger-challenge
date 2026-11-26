from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.dependencies import api_key_hash
from app.main import app
from app.models import Tenant


@pytest.fixture
def test_db(tmp_path) -> Iterator[tuple[Session, dict[str, Tenant]]]:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    with TestingSession() as db:
        tenant_a = Tenant(name="Tenant A", api_key_hash=api_key_hash("key-a"))
        tenant_b = Tenant(name="Tenant B", api_key_hash=api_key_hash("key-b"))
        db.add_all([tenant_a, tenant_b])
        db.commit()
        yield db, {"a": tenant_a, "b": tenant_b}


@pytest.fixture
def client(test_db) -> Iterator[TestClient]:
    _, _ = test_db
    engine = test_db[0].get_bind()
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        with TestingSession() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def headers(key: str) -> dict[str, str]:
    return {"X-Tenant-API-Key": key}
