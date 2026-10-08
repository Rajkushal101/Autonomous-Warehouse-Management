import pytest
from app.models.entities import User, Session as UserSession
from app.domain.models import Role, WarehouseSecurityException
from app.services.policy import AccessPolicy
from app.services.auth_service import AuthService
from app.core.security import verify_password, hash_password, get_utc_now
from datetime import timedelta

def test_password_hashing():
    pw = "SuperSecurePassword123!"
    hashed = hash_password(pw)
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False

def test_access_policy_role_enforcement(db_session):
    customer = db_session.query(User).filter(User.username == "customer_bob").first()
    operator = db_session.query(User).filter(User.username == "operator_alice").first()
    manager = db_session.query(User).filter(User.username == "manager_carol").first()

    # Operator and Manager can perform task assignment
    AccessPolicy.require_role(operator, [Role.OPERATOR, Role.MANAGER], db=db_session, action_name="TEST_ACTION")
    AccessPolicy.require_role(manager, [Role.OPERATOR, Role.MANAGER], db=db_session, action_name="TEST_ACTION")

    # Customer CANNOT perform task assignment (Assert 403 Forbidden)
    with pytest.raises(WarehouseSecurityException) as exc_info:
        AccessPolicy.require_role(customer, [Role.OPERATOR, Role.MANAGER], db=db_session, action_name="ASSIGN_ROBOT_TASK")
    assert exc_info.value.status_code == 403
    assert "Access denied" in exc_info.value.message

def test_customer_cannot_assign_robot(client):
    # 1. Login as customer
    login_res = client.post("/auth/login", json={"username": "customer_bob", "password": "CustomerPass123!"})
    assert login_res.status_code == 200
    token = login_res.json()["token"]

    # 2. Attempt to invoke privileged task assignment API directly
    res = client.post(
        "/operations/tasks/assign",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "test-key-001"},
        json={"task_id": "fake-task-id", "robot_id": "fake-robot-id"}
    )
    # MUST return 403 Forbidden
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN_ROLE"

def test_cross_customer_order_access_denied(client):
    # Customer Bob creates an order
    login_bob = client.post("/auth/login", json={"username": "customer_bob", "password": "CustomerPass123!"})
    token_bob = login_bob.json()["token"]
    
    order_res = client.post(
        "/orders",
        headers={"Authorization": f"Bearer {token_bob}", "Idempotency-Key": "idemp-bob-order-1"},
        json={"items": [{"sku": "SKU-001", "quantity": 1}]}
    )
    assert order_res.status_code == 200 or order_res.status_code == 201
    order_id = order_res.json()["order_id"]

    # Customer Charlie logs in
    login_charlie = client.post("/auth/login", json={"username": "customer_charlie", "password": "CustomerPass123!"})
    token_charlie = login_charlie.json()["token"]

    # Charlie attempts to inspect Bob's order UUID (IDOR Attempt)
    idor_res = client.get(f"/orders/{order_id}", headers={"Authorization": f"Bearer {token_charlie}"})
    # MUST return 404 to avoid disclosing existence of other tenant's resource
    assert idor_res.status_code == 404

def test_session_revocation(client, db_session):
    login_res = client.post("/auth/login", json={"username": "customer_bob", "password": "CustomerPass123!"})
    token = login_res.json()["token"]

    # Profile check works
    res1 = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res1.status_code == 200

    # Logout
    logout_res = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_res.status_code == 200

    # Subsequent request with revoked token must fail with 401
    res2 = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 401
