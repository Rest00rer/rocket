import asyncio
import uuid

from httpx import AsyncClient


def key() -> str:
    return str(uuid.uuid4())


async def inventory_item(client: AsyncClient, sku: str, warehouse: str) -> dict:
    response = await client.get("/api/inventory")
    assert response.status_code == 200
    return next(
        item
        for item in response.json()["items"]
        if item["product"]["sku"] == sku and item["warehouse"]["name"] == warehouse
    )


async def test_seed_contains_required_balances(client: AsyncClient) -> None:
    inventory = (await client.get("/api/inventory")).json()
    values = {
        (item["product"]["sku"], item["warehouse"]["name"]): item["on_hand"]
        for item in inventory["items"]
    }
    assert values == {
        ("SKU-101", "Север"): 10,
        ("SKU-101", "Юг"): 6,
        ("SKU-102", "Север"): 5,
        ("SKU-102", "Юг"): 0,
        ("SKU-103", "Север"): 0,
        ("SKU-103", "Юг"): 4,
    }


async def test_receipt_is_idempotent(client: AsyncClient, catalog: dict) -> None:
    payload = {
        "product_id": catalog["products"]["SKU-102"]["id"],
        "warehouse_id": catalog["warehouses"]["Юг"]["id"],
        "quantity": 3,
    }
    idempotency_key = key()
    first = await client.post(
        "/api/receipts", json=payload, headers={"Idempotency-Key": idempotency_key}
    )
    second = await client.post(
        "/api/receipts", json=payload, headers={"Idempotency-Key": idempotency_key}
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json() == second.json()
    assert (await inventory_item(client, "SKU-102", "Юг"))["on_hand"] == 3


async def test_fbs_reserve_cancel_and_ship(client: AsyncClient, catalog: dict) -> None:
    payload = {
        "product_id": catalog["products"]["SKU-101"]["id"],
        "warehouse_id": catalog["warehouses"]["Север"]["id"],
        "quantity": 3,
    }
    reserved = await client.post(
        "/api/fbs/reservations", json=payload, headers={"Idempotency-Key": key()}
    )
    assert reserved.status_code == 201
    item = await inventory_item(client, "SKU-101", "Север")
    assert (item["on_hand"], item["reserved_fbs"], item["available"]) == (10, 3, 7)

    cancelled = await client.post(
        f"/api/fbs/reservations/{reserved.json()['entity_id']}/cancel",
        headers={"Idempotency-Key": key()},
    )
    assert cancelled.status_code == 200
    assert (await inventory_item(client, "SKU-101", "Север"))["reserved_fbs"] == 0

    second = await client.post(
        "/api/fbs/reservations", json=payload, headers={"Idempotency-Key": key()}
    )
    shipped = await client.post(
        f"/api/fbs/reservations/{second.json()['entity_id']}/ship",
        headers={"Idempotency-Key": key()},
    )
    assert shipped.status_code == 200
    item = await inventory_item(client, "SKU-101", "Север")
    assert (item["on_hand"], item["reserved_fbs"], item["available"]) == (7, 0, 7)
    summary = (await client.get("/api/inventory")).json()
    assert summary["in_transit"]["fbs_to_customer"] == 3


async def test_fbo_dispatch_and_receive(client: AsyncClient, catalog: dict) -> None:
    payload = {
        "product_id": catalog["products"]["SKU-101"]["id"],
        "warehouse_id": catalog["warehouses"]["Юг"]["id"],
        "quantity": 2,
    }
    dispatched = await client.post(
        "/api/fbo/shipments", json=payload, headers={"Idempotency-Key": key()}
    )
    assert dispatched.status_code == 201
    assert (await inventory_item(client, "SKU-101", "Юг"))["on_hand"] == 4
    assert (await client.get("/api/inventory")).json()["in_transit"]["fbo"] == 2

    shipment_id = dispatched.json()["entity_id"]
    receive_key = key()
    first = await client.post(
        f"/api/fbo/shipments/{shipment_id}/receive",
        headers={"Idempotency-Key": receive_key},
    )
    second = await client.post(
        f"/api/fbo/shipments/{shipment_id}/receive",
        headers={"Idempotency-Key": receive_key},
    )
    assert first.json() == second.json()
    assert (await client.get("/api/inventory")).json()["in_transit"]["fbo"] == 0


async def test_transfer_dispatch_and_receive(client: AsyncClient, catalog: dict) -> None:
    payload = {
        "product_id": catalog["products"]["SKU-102"]["id"],
        "source_warehouse_id": catalog["warehouses"]["Север"]["id"],
        "destination_warehouse_id": catalog["warehouses"]["Юг"]["id"],
        "quantity": 4,
    }
    transfer = await client.post("/api/transfers", json=payload)
    assert transfer.status_code == 201
    transfer_id = transfer.json()["id"]
    assert (
        await client.post(
            f"/api/transfers/{transfer_id}/dispatch",
            headers={"Idempotency-Key": key()},
        )
    ).status_code == 200
    assert (await inventory_item(client, "SKU-102", "Север"))["on_hand"] == 1
    assert (await client.get("/api/inventory")).json()["in_transit"]["between_warehouses"] == 4

    assert (
        await client.post(
            f"/api/transfers/{transfer_id}/receive",
            headers={"Idempotency-Key": key()},
        )
    ).status_code == 200
    assert (await inventory_item(client, "SKU-102", "Юг"))["on_hand"] == 4


async def test_only_draft_transfer_can_be_deleted_without_changing_stock(
    client: AsyncClient, catalog: dict
) -> None:
    payload = {
        "product_id": catalog["products"]["SKU-102"]["id"],
        "source_warehouse_id": catalog["warehouses"]["Север"]["id"],
        "destination_warehouse_id": catalog["warehouses"]["Юг"]["id"],
        "quantity": 4,
    }
    transfer = await client.post("/api/transfers", json=payload)
    transfer_id = transfer.json()["id"]

    deleted = await client.delete(
        f"/api/transfers/{transfer_id}", headers={"Idempotency-Key": key()}
    )

    assert deleted.status_code == 200
    assert deleted.json()["status"] == "deleted"
    assert (await inventory_item(client, "SKU-102", "Север"))["on_hand"] == 5
    assert not (await client.get("/api/transfers")).json()
    history = (await client.get("/api/operations", params={"sku": "SKU-102"})).json()["items"]
    assert {item["operation_type"] for item in history[:2]} == {
        "transfer_created",
        "transfer_deleted",
    }


async def test_sent_transfer_cannot_be_deleted(client: AsyncClient, catalog: dict) -> None:
    transfer = await client.post(
        "/api/transfers",
        json={
            "product_id": catalog["products"]["SKU-102"]["id"],
            "source_warehouse_id": catalog["warehouses"]["Север"]["id"],
            "destination_warehouse_id": catalog["warehouses"]["Юг"]["id"],
            "quantity": 1,
        },
    )
    transfer_id = transfer.json()["id"]
    await client.post(
        f"/api/transfers/{transfer_id}/dispatch",
        headers={"Idempotency-Key": key()},
    )

    response = await client.delete(
        f"/api/transfers/{transfer_id}", headers={"Idempotency-Key": key()}
    )

    assert response.status_code == 409
    assert response.json()["code"] == "invalid_transfer_state"


async def test_shortage_on_selected_warehouse_does_not_use_other_stock(
    client: AsyncClient, catalog: dict
) -> None:
    payload = {
        "product_id": catalog["products"]["SKU-103"]["id"],
        "warehouse_id": catalog["warehouses"]["Север"]["id"],
        "quantity": 3,
    }
    response = await client.post(
        "/api/fbo/shipments", json=payload, headers={"Idempotency-Key": key()}
    )
    assert response.status_code == 409
    assert response.json()["code"] == "insufficient_stock"
    assert response.json()["details"]["available_here"] == 0
    assert response.json()["details"]["available_total"] == 4
    assert (await inventory_item(client, "SKU-103", "Юг"))["on_hand"] == 4


async def test_archiving_warehouse_preserves_stock_and_blocks_receipt(
    client: AsyncClient, catalog: dict
) -> None:
    north_id = catalog["warehouses"]["Север"]["id"]
    response = await client.delete(f"/api/warehouses/{north_id}")
    assert response.status_code == 200
    assert response.json()["archived"] is True
    item = await inventory_item(client, "SKU-101", "Север")
    assert item["on_hand"] == 10
    assert item["warehouse"]["archived"] is True

    receipt = await client.post(
        "/api/receipts",
        json={
            "product_id": catalog["products"]["SKU-101"]["id"],
            "warehouse_id": north_id,
            "quantity": 1,
        },
        headers={"Idempotency-Key": key()},
    )
    assert receipt.status_code == 409
    assert receipt.json()["code"] == "warehouse_archived"


async def test_idempotency_key_cannot_be_reused_for_another_payload(
    client: AsyncClient, catalog: dict
) -> None:
    idempotency_key = key()
    base = {
        "product_id": catalog["products"]["SKU-101"]["id"],
        "warehouse_id": catalog["warehouses"]["Север"]["id"],
    }
    assert (
        await client.post(
            "/api/receipts",
            json={**base, "quantity": 1},
            headers={"Idempotency-Key": idempotency_key},
        )
    ).status_code == 201
    conflict = await client.post(
        "/api/receipts",
        json={**base, "quantity": 2},
        headers={"Idempotency-Key": idempotency_key},
    )
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "idempotency_conflict"


async def test_operation_history_contains_business_events(
    client: AsyncClient, catalog: dict
) -> None:
    await client.post(
        "/api/receipts",
        json={
            "product_id": catalog["products"]["SKU-101"]["id"],
            "warehouse_id": catalog["warehouses"]["Север"]["id"],
            "quantity": 2,
        },
        headers={"Idempotency-Key": key()},
    )
    history = (await client.get("/api/operations?sku=SKU-101")).json()["items"]
    assert history[0]["operation_type"] == "receipt"
    assert history[0]["quantity"] == 2
    assert history[0]["destination_warehouse_name"] == "Север"


async def test_operation_history_accepts_multiple_operation_types(
    client: AsyncClient, catalog: dict
) -> None:
    payload = {
        "product_id": catalog["products"]["SKU-102"]["id"],
        "source_warehouse_id": catalog["warehouses"]["Север"]["id"],
        "destination_warehouse_id": catalog["warehouses"]["Юг"]["id"],
        "quantity": 1,
    }
    transfer = await client.post("/api/transfers", json=payload)
    transfer_id = transfer.json()["id"]
    await client.post(
        f"/api/transfers/{transfer_id}/dispatch",
        headers={"Idempotency-Key": key()},
    )
    await client.post(
        f"/api/transfers/{transfer_id}/receive",
        headers={"Idempotency-Key": key()},
    )

    response = await client.get(
        "/api/operations",
        params=[
            ("operation_type", "transfer_created"),
            ("operation_type", "transfer_received"),
        ],
    )

    assert response.status_code == 200
    operation_types = {item["operation_type"] for item in response.json()["items"]}
    assert operation_types == {"transfer_created", "transfer_received"}


async def test_concurrent_reservations_never_overbook_stock(
    client: AsyncClient, catalog: dict
) -> None:
    payload = {
        "product_id": catalog["products"]["SKU-102"]["id"],
        "warehouse_id": catalog["warehouses"]["Север"]["id"],
        "quantity": 4,
    }

    first, second = await asyncio.gather(
        client.post(
            "/api/fbs/reservations",
            json=payload,
            headers={"Idempotency-Key": key()},
        ),
        client.post(
            "/api/fbs/reservations",
            json=payload,
            headers={"Idempotency-Key": key()},
        ),
    )

    assert sorted((first.status_code, second.status_code)) == [201, 409]
    item = await inventory_item(client, "SKU-102", "Север")
    assert item["on_hand"] == 5
    assert item["reserved_fbs"] == 4
    assert item["available"] == 1


async def test_concurrent_retries_with_same_idempotency_key_replay_one_result(
    client: AsyncClient, catalog: dict
) -> None:
    payload = {
        "product_id": catalog["products"]["SKU-101"]["id"],
        "warehouse_id": catalog["warehouses"]["Север"]["id"],
        "quantity": 3,
    }
    idempotency_key = key()

    first, second = await asyncio.gather(
        client.post(
            "/api/fbs/reservations",
            json=payload,
            headers={"Idempotency-Key": idempotency_key},
        ),
        client.post(
            "/api/fbs/reservations",
            json=payload,
            headers={"Idempotency-Key": idempotency_key},
        ),
    )

    assert first.status_code == second.status_code == 201
    assert first.json() == second.json()
    item = await inventory_item(client, "SKU-101", "Север")
    assert item["reserved_fbs"] == 3
