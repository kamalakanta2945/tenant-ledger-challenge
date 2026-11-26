from decimal import Decimal
from uuid import uuid4

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import AuditLog, Tenant, Transaction, TransactionType
from app.schemas import TransactionCreate


def create_transaction(
    db: Session,
    tenant: Tenant,
    payload: TransactionCreate,
) -> Transaction:
    existing = db.query(Transaction).filter(
        Transaction.tenant_id == tenant.id,
        Transaction.idempotency_key == payload.idempotency_key,
    ).first()
    if existing:
        raise LookupError("Duplicate idempotency key")

    if payload.external_reference:
        existing_reference = db.query(Transaction).filter(
            Transaction.tenant_id == tenant.id,
            Transaction.external_reference == payload.external_reference,
        ).first()
        if existing_reference:
            raise LookupError("Duplicate external reference")

    transaction = Transaction(
        tenant_id=tenant.id,
        client_ref=payload.client_ref,
        related_client_ref=payload.related_client_ref,
        transaction_type=TransactionType(payload.transaction_type),
        amount=payload.amount,
        currency=payload.currency,
        transaction_date=payload.transaction_date,
        idempotency_key=payload.idempotency_key,
        external_reference=payload.external_reference,
        status="ACTIVE",
    )
    db.add(transaction)
    db.flush()
    db.add(AuditLog(
        tenant_id=tenant.id,
        transaction_id=transaction.id,
        action="CREATED",
        actor="tenant-api-key",
    ))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise LookupError("Duplicate transaction key") from exc
    db.refresh(transaction)
    return transaction


def calculate_balance(
    db: Session,
    tenant: Tenant,
    client_ref: str,
    currency: str,
) -> Decimal:
    transactions = db.query(Transaction).filter(
        Transaction.tenant_id == tenant.id,
        Transaction.currency == currency,
        or_(
            Transaction.client_ref == client_ref,
            Transaction.related_client_ref == client_ref,
        ),
    ).all()

    balance = Decimal("0.00")
    for transaction in transactions:
        if transaction.transaction_type == TransactionType.DEPOSIT:
            if transaction.client_ref == client_ref:
                balance += transaction.amount
        elif transaction.transaction_type == TransactionType.WITHDRAWAL:
            if transaction.client_ref == client_ref:
                balance -= transaction.amount
        elif transaction.transaction_type == TransactionType.FEE:
            if transaction.client_ref == client_ref:
                balance -= transaction.amount
        elif transaction.transaction_type == TransactionType.TRANSFER:
            if transaction.client_ref == client_ref:
                balance -= transaction.amount
            if transaction.related_client_ref == client_ref:
                balance += transaction.amount
    return balance.quantize(Decimal("0.01"))


def reverse_transaction(db: Session, tenant: Tenant, transaction_id: str) -> Transaction:
    original = db.query(Transaction).filter(
        Transaction.tenant_id == tenant.id,
        Transaction.id == transaction_id,
    ).first()
    if original is None:
        raise LookupError("Transaction not found")
    if original.status == "REVERSED":
        raise LookupError("Transaction already reversed")

    if original.transaction_type == TransactionType.DEPOSIT:
        reversal_type = TransactionType.WITHDRAWAL
        related_ref = None
    elif original.transaction_type in (TransactionType.WITHDRAWAL, TransactionType.FEE):
        reversal_type = TransactionType.DEPOSIT
        related_ref = None
    else:
        reversal_type = TransactionType.TRANSFER
        related_ref = original.related_client_ref

    reversal = Transaction(
        tenant_id=tenant.id,
        client_ref=(
            original.related_client_ref
            if original.transaction_type == TransactionType.TRANSFER
            else original.client_ref
        ),
        related_client_ref=(
            original.client_ref
            if original.transaction_type == TransactionType.TRANSFER
            else related_ref
        ),
        transaction_type=reversal_type,
        amount=original.amount,
        currency=original.currency,
        transaction_date=original.transaction_date,
        idempotency_key=f"reverse:{original.id}:{uuid4()}",
        external_reference=None,
        reversal_of_id=original.id,
        status="ACTIVE",
    )
    db.add(reversal)
    db.flush()
    original.status = "REVERSED"
    db.add(AuditLog(
        tenant_id=tenant.id,
        transaction_id=original.id,
        action="REVERSAL_REQUESTED",
        actor="tenant-api-key",
    ))
    db.add(AuditLog(
        tenant_id=tenant.id,
        transaction_id=reversal.id,
        action="REVERSAL_CREATED",
        actor="tenant-api-key",
    ))
    db.commit()
    db.refresh(reversal)
    return reversal
