from tests.conftest import headers
from tests.test_transactions import transaction_payload


def test_missing_and_invalid_api_key(client):
    missing = client.post("/transactions", json=transaction_payload())
    invalid = client.post(
        "/transactions",
        headers=headers("wrong-key"),
        json=transaction_payload(),
    )
    assert missing.status_code == 401
    assert invalid.status_code == 401


def test_cross_tenant_transaction_access_is_not_found(client):
    created = client.post(
        "/transactions",
        headers=headers("key-a"),
        json=transaction_payload(),
    )
    transaction_id = created.json()["id"]

    cross_tenant = client.get(
        f"/transactions/{transaction_id}",
        headers=headers("key-b"),
    )
    assert cross_tenant.status_code == 404


def test_cross_tenant_balance_is_not_leaked(client):
    client.post(
        "/transactions",
        headers=headers("key-a"),
        json=transaction_payload(client_ref="private-client"),
    )
    response = client.get(
        "/clients/private-client/balance?currency=USD",
        headers=headers("key-b"),
    )
    assert response.status_code == 200
    assert response.json()["balance"] == "0.00"
