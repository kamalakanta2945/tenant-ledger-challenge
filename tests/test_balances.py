from app.models import AuditLog
from tests.conftest import headers
from tests.test_transactions import transaction_payload


def test_deposit_withdrawal_and_fee_balance(client):
    client.post("/transactions", headers=headers("key-a"), json=transaction_payload())
    client.post(
        "/transactions",
        headers=headers("key-a"),
        json=transaction_payload(
            transaction_type="WITHDRAWAL",
            amount="20.25",
            idempotency_key="withdraw",
        ),
    )
    client.post(
        "/transactions",
        headers=headers("key-a"),
        json=transaction_payload(
            transaction_type="FEE",
            amount="5",
            idempotency_key="fee",
        ),
    )
    response = client.get(
        "/clients/client-1/balance?currency=USD",
        headers=headers("key-a"),
    )
    assert response.status_code == 200
    assert response.json()["balance"] == "75.00"


def test_transfer_changes_source_and_destination(client):
    payload = transaction_payload(
        transaction_type="TRANSFER",
        amount="40",
        idempotency_key="transfer",
        related_client_ref="client-2",
    )
    created = client.post("/transactions", headers=headers("key-a"), json=payload)
    assert created.status_code == 201

    source = client.get(
        "/clients/client-1/balance?currency=USD",
        headers=headers("key-a"),
    )
    destination = client.get(
        "/clients/client-2/balance?currency=USD",
        headers=headers("key-a"),
    )
    assert source.json()["balance"] == "-40.00"
    assert destination.json()["balance"] == "40.00"


def test_reversal_preserves_history_and_reverses_balance(client):
    created = client.post(
        "/transactions",
        headers=headers("key-a"),
        json=transaction_payload(),
    )
    original_id = created.json()["id"]

    reversed_response = client.post(
        f"/transactions/{original_id}/reverse",
        headers=headers("key-a"),
    )
    assert reversed_response.status_code == 200
    assert reversed_response.json()["reversal_of_id"] == original_id

    balance = client.get(
        "/clients/client-1/balance?currency=USD",
        headers=headers("key-a"),
    )
    assert balance.json()["balance"] == "0.00"

    repeat = client.post(
        f"/transactions/{original_id}/reverse",
        headers=headers("key-a"),
    )
    assert repeat.status_code == 409


def test_reversal_is_preserved_in_audit_history(client, test_db):
    created = client.post(
        "/transactions",
        headers=headers("key-a"),
        json=transaction_payload(idempotency_key="audit-reversal"),
    )
    original_id = created.json()["id"]
    client.post(
        f"/transactions/{original_id}/reverse",
        headers=headers("key-a"),
    )

    db, tenants = test_db
    audit_rows = (
        db.query(AuditLog)
        .filter(AuditLog.tenant_id == tenants["a"].id)
        .order_by(AuditLog.occurred_at)
        .all()
    )
    actions = {row.action for row in audit_rows}
    assert "CREATED" in actions
    assert "REVERSAL_REQUESTED" in actions
    assert "REVERSAL_CREATED" in actions
