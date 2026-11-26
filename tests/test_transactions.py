from datetime import date, timedelta

from tests.conftest import headers


def transaction_payload(**overrides):
    payload = {
        "client_ref": "client-1",
        "transaction_type": "DEPOSIT",
        "amount": "100.25",
        "currency": "USD",
        "transaction_date": date.today().isoformat(),
        "idempotency_key": "tx-001",
    }
    payload.update(overrides)
    return payload


def test_deposit_and_withdrawal_creation(client):
    deposit = client.post("/transactions", headers=headers("key-a"), json=transaction_payload())
    assert deposit.status_code == 201
    assert deposit.json()["amount"] == "100.25"

    withdrawal = client.post(
        "/transactions",
        headers=headers("key-a"),
        json=transaction_payload(
            transaction_type="WITHDRAWAL",
            idempotency_key="tx-002",
            amount="25.10",
        ),
    )
    assert withdrawal.status_code == 201
    assert withdrawal.json()["transaction_type"] == "WITHDRAWAL"


def test_reject_negative_and_zero_amount(client):
    negative = client.post(
        "/transactions",
        headers=headers("key-a"),
        json=transaction_payload(amount="-1"),
    )
    zero = client.post(
        "/transactions",
        headers=headers("key-a"),
        json=transaction_payload(amount="0", idempotency_key="zero"),
    )
    assert negative.status_code == 422
    assert zero.status_code == 422


def test_reject_invalid_currency_and_future_date(client):
    invalid_currency = client.post(
        "/transactions",
        headers=headers("key-a"),
        json=transaction_payload(currency="JPY", idempotency_key="bad-currency"),
    )
    future = client.post(
        "/transactions",
        headers=headers("key-a"),
        json=transaction_payload(
            transaction_date=(date.today() + timedelta(days=1)).isoformat(),
            idempotency_key="future",
        ),
    )
    assert invalid_currency.status_code == 422
    assert future.status_code == 422


def test_duplicate_idempotency_key_is_conflict(client):
    first = client.post("/transactions", headers=headers("key-a"), json=transaction_payload())
    second = client.post(
        "/transactions",
        headers=headers("key-a"),
        json=transaction_payload(amount="999.99"),
    )
    assert first.status_code == 201
    assert second.status_code == 409


def test_idempotency_is_scoped_per_tenant(client):
    first = client.post("/transactions", headers=headers("key-a"), json=transaction_payload())
    second = client.post("/transactions", headers=headers("key-b"), json=transaction_payload())
    assert first.status_code == 201
    assert second.status_code == 201
