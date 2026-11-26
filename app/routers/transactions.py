from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_authenticated_tenant
from app.models import Tenant, Transaction
from app.schemas import ALLOWED_CURRENCIES, TransactionCreate, TransactionRead
from app.services.ledger_service import create_transaction, reverse_transaction

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def post_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_authenticated_tenant),
) -> Transaction:
    try:
        return create_transaction(db, tenant, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_authenticated_tenant),
) -> Transaction:
    transaction = db.query(Transaction).filter(
        Transaction.tenant_id == tenant.id,
        Transaction.id == transaction_id,
    ).first()
    if transaction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return transaction


@router.post("/{transaction_id}/reverse", response_model=TransactionRead)
def reverse(
    transaction_id: str,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_authenticated_tenant),
) -> Transaction:
    try:
        return reverse_transaction(db, tenant, transaction_id)
    except LookupError as exc:
        message = str(exc)
        status_code = status.HTTP_409_CONFLICT if "already" in message else status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=status_code, detail=message) from exc
