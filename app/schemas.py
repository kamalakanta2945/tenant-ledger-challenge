from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ALLOWED_CURRENCIES = {"USD", "EUR", "GBP"}


class TransactionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_ref: str = Field(min_length=1, max_length=200)
    transaction_type: Literal["DEPOSIT", "WITHDRAWAL", "FEE", "TRANSFER"]
    amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    transaction_date: date
    idempotency_key: str = Field(min_length=1, max_length=200)
    external_reference: str | None = Field(default=None, max_length=200)
    related_client_ref: str | None = Field(default=None, max_length=200)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        value = value.upper()
        if value not in ALLOWED_CURRENCIES:
            raise ValueError("currency must be one of USD, EUR, GBP")
        return value

    @field_validator("transaction_date")
    @classmethod
    def validate_not_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("transaction_date cannot be in the future")
        return value

    @field_validator("related_client_ref")
    @classmethod
    def validate_related_ref(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("related_client_ref cannot be empty")
        return value


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    client_ref: str
    related_client_ref: str | None
    transaction_type: str
    amount: Decimal
    currency: str
    transaction_date: date
    idempotency_key: str
    external_reference: str | None
    reversal_of_id: str | None
    status: str
    created_at: datetime


class BalanceRead(BaseModel):
    client_ref: str
    currency: str
    balance: Decimal


class AuditRead(BaseModel):
    id: str
    transaction_id: str | None
    action: str
    actor: str
    occurred_at: datetime
