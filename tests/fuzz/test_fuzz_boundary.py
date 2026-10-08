import pytest
from hypothesis import given, strategies as st, settings
from fastapi.testclient import TestClient
from app.main import app

test_client = TestClient(app)

@settings(max_examples=100, deadline=None)
@given(
    qty=st.integers(),
    sku=st.text(min_size=0, max_size=100)
)
def test_fuzz_order_payload_boundary(qty, sku):
    """
    FZ-01: Property-based boundary fuzzing on order placement payload.
    Asserts system never crashes with unhandled 500 Internal Server Error,
    properly rejecting negative, zero, huge numbers, and malformed SKUs with 401 or 422.
    """
    # Issue request with fuzzed payload
    response = test_client.post(
        "/orders",
        headers={"Idempotency-Key": "fuzz-key-123"},
        json={"items": [{"sku": sku, "quantity": qty}]}
    )
    # The server must return either 401 (Unauthorized if no token) or 422 (Validation error)
    # Crucially, it must NEVER return 500 Internal Server Error.
    assert response.status_code in [401, 403, 404, 409, 422]
    assert response.status_code != 500
