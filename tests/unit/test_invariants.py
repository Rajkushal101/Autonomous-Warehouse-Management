import pytest
from app.services.movement_service import MovementService
from app.services.order_service import OrderService
from app.models.entities import User, InventoryBalance, Product
from app.domain.models import WarehouseSecurityException

def test_grid_bfs_pathfinding():
    obstacles = {(3, 3), (3, 4), (7, 7)}
    start = (0, 0)
    goal = (5, 5)
    
    path = MovementService.bfs_shortest_path(
        start=start,
        goal=goal,
        grid_width=10,
        grid_height=10,
        obstacles=obstacles
    )
    assert path is not None
    assert path[0] == start
    assert path[-1] == goal
    # Assert path does not touch obstacles
    for step in path:
        assert step not in obstacles

def test_negative_quantity_order_rejected(client):
    login = client.post("/auth/login", json={"username": "customer_bob", "password": "CustomerPass123!"})
    token = login.json()["token"]

    # Negative quantity
    res = client.post(
        "/orders",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "key-neg-1"},
        json={"items": [{"sku": "SKU-001", "quantity": -5}]}
    )
    assert res.status_code == 422

    # Zero quantity
    res2 = client.post(
        "/orders",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "key-zero-1"},
        json={"items": [{"sku": "SKU-001", "quantity": 0}]}
    )
    assert res2.status_code == 422

def test_inventory_invariants_preserved(db_session):
    balances = db_session.query(InventoryBalance).all()
    for b in balances:
        assert b.on_hand >= 0
        assert b.reserved >= 0
        assert b.reserved <= b.on_hand
