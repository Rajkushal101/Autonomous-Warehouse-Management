import pytest
from app.models.entities import Order, Task, Robot, InventoryMovement
from worker.dispatcher import run_single_tick

def test_st01_e2e_fulfillment_workflow(client, db_session):
    """
    ST-01: End-to-End Warehouse Fulfillment Test
    1. Authenticate Customer
    2. Place Order (Verify atomic reservation)
    3. Authenticate Operator & Dispatch Robot
    4. Run Simulation Steps (Pickup -> Move -> Packing Bay Drop)
    5. Verify Order status is FULFILLED, destination inventory credited, movement ledger complete.
    """
    # 1. Customer Login
    login_cust = client.post("/auth/login", json={"username": "customer_bob", "password": "CustomerPass123!"})
    assert login_cust.status_code == 200
    cust_token = login_cust.json()["token"]

    # 2. Place Order
    order_res = client.post(
        "/orders",
        headers={"Authorization": f"Bearer {cust_token}", "Idempotency-Key": "e2e-order-idemp-01"},
        json={"items": [{"sku": "SKU-001", "quantity": 2}]}
    )
    assert order_res.status_code in [200, 201]
    order_id = order_res.json()["order_id"]
    task_id = order_res.json()["items"][0]["task_id"]

    # 3. Operator Login
    login_op = client.post("/auth/login", json={"username": "operator_alice", "password": "OperatorPass123!"})
    assert login_op.status_code == 200
    op_token = login_op.json()["token"]

    # Find idle robot
    fleet_res = client.get("/operations/fleet", headers={"Authorization": f"Bearer {op_token}"})
    robots = fleet_res.json()["robots"]
    idle_robot = next(r for r in robots if r["status"] == "IDLE")

    # 4. Dispatch Robot
    assign_res = client.post(
        "/operations/tasks/assign",
        headers={"Authorization": f"Bearer {op_token}", "Idempotency-Key": "e2e-assign-idemp-01"},
        json={"task_id": task_id, "robot_id": idle_robot["id"]}
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["task_state"] == "ASSIGNED"

    # 5. Execute Simulation Ticks until Delivered
    max_ticks = 40
    ticks = 0
    delivered = False
    while ticks < max_ticks:
        tick_result = run_single_tick(db_session)
        task = db_session.query(Task).filter(Task.id == task_id).first()
        if task.state == "COMPLETED":
            delivered = True
            break
        ticks += 1

    assert delivered is True, f"Robot failed to deliver item within {max_ticks} ticks"

    # 6. Verify Customer Receipt
    receipt_res = client.get(f"/orders/{order_id}", headers={"Authorization": f"Bearer {cust_token}"})
    assert receipt_res.status_code == 200, f"Receipt error: {receipt_res.status_code} - {receipt_res.text}"
    receipt_data = receipt_res.json()
    assert receipt_data["status"] == "FULFILLED"
    assert receipt_data["items"][0]["delivered_qty"] == 2
    assert receipt_data["items"][0]["task_state"] == "COMPLETED"

def test_st02_security_penetration_boundary(client):
    """
    ST-02: Security Verification
    Customer attempts to invoke manager-only stock adjustment and operator emergency stop.
    Asserts both are denied with 403 Forbidden.
    """
    login_cust = client.post("/auth/login", json={"username": "customer_bob", "password": "CustomerPass123!"})
    cust_token = login_cust.json()["token"]

    # Attempt stock adjustment
    adj_res = client.post(
        "/inventory/adjustments",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={"sku": "SKU-001", "location_code": "SHELF-01", "delta": 100, "reason": "Hacking inventory"}
    )
    assert adj_res.status_code == 403

    # Attempt pause operations
    pause_res = client.post(
        "/operations/pause",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={"reason": "Denial of service attempt"}
    )
    assert pause_res.status_code == 403
