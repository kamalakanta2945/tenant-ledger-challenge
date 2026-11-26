from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_authenticated_tenant
from app.models import Tenant, Transaction
from app.schemas import ALLOWED_CURRENCIES, BalanceRead, TransactionRead
from app.services.ledger_service import calculate_balance

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("/{client_ref}/balance", response_model=BalanceRead)
def get_balance(
    client_ref: str,
    currency: str = Query(default="USD", min_length=3, max_length=3),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_authenticated_tenant),
) -> BalanceRead:
    currency = currency.upper()
    if currency not in ALLOWED_CURRENCIES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported currency")
    balance = calculate_balance(db, tenant, client_ref, currency)
    return BalanceRead(client_ref=client_ref, currency=currency, balance=balance)


@router.get("/{client_ref}/transactions", response_model=list[TransactionRead])
def list_transactions(
    client_ref: str,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_authenticated_tenant),
) -> list[Transaction]:
    return (
        db.query(Transaction)
        .filter(
            Transaction.tenant_id == tenant.id,
            (Transaction.client_ref == client_ref)
            | (Transaction.related_client_ref == client_ref),
        )
        .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
