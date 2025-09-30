from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.orders.repository import order_repo

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clear_repo() -> None:
    order_repo.clear()


def _dec(v: Any) -> Decimal:
    return Decimal(str(v))


def _create_sample_order() -> int:
    payload = {
        "items": [
            {
                "sku": "SKU-1",
                "description": "Item 1",
                "quantity": 2,
                "unit_price": "100.00",
                "gst_rate": "18.00",
            },
            {
                "sku": "SKU-2",
                "description": "Item 2",
                "quantity": 1,
                "unit_price": "50.00",
                "gst_rate": "5.00",
            },
        ]
    }
    r = client.post("/api/v1/mock/orders/", json=payload)
    assert r.status_code == 200, r.text
    order = r.json()
    assert "id" in order
    return int(order["id"])


def test_generate_invoice_intra_state() -> None:
    order_id = _create_sample_order()
    # Seller state from settings is 29; use a customer GSTIN with state code 29
    body = {"customer_gstin": "29ABCDE1234F1Z5"}
    r = client.post(f"/api/v1/mock/orders/{order_id}/generate-invoice", json=body)
    assert r.status_code == 200, r.text
    data = r.json()

    assert data["supply_type"] == "intra"
    assert data["seller_state_code"] == "29"
    assert data["customer_state_code"] == "29"

    # Totals
    assert _dec(data["total_taxable_value"]) == Decimal("250.00")
    assert _dec(data["total_cgst"]) == Decimal("19.25")
    assert _dec(data["total_sgst"]) == Decimal("19.25")
    assert _dec(data["total_igst"]) == Decimal("0.00")
    assert _dec(data["grand_total"]) == Decimal("288.50")

    # Line item checks
    items = data["items"]
    assert len(items) == 2
    line1 = items[0]
    assert _dec(line1["taxable_value"]) == Decimal("200.00")
    assert _dec(line1["cgst_amount"]) == Decimal("18.00")
    assert _dec(line1["sgst_amount"]) == Decimal("18.00")
    assert _dec(line1["igst_amount"]) == Decimal("0.00")

    line2 = items[1]
    assert _dec(line2["taxable_value"]) == Decimal("50.00")
    assert _dec(line2["cgst_amount"]) == Decimal("1.25")
    assert _dec(line2["sgst_amount"]) == Decimal("1.25")
    assert _dec(line2["igst_amount"]) == Decimal("0.00")


def test_generate_invoice_inter_state() -> None:
    order_id = _create_sample_order()
    # Different state code, e.g., 27 (Maharashtra)
    body = {"customer_gstin": "27ABCDE1234F1Z5"}
    r = client.post(f"/api/v1/mock/orders/{order_id}/generate-invoice", json=body)
    assert r.status_code == 200, r.text
    data = r.json()

    assert data["supply_type"] == "inter"
    assert data["seller_state_code"] == "29"
    assert data["customer_state_code"] == "27"

    assert _dec(data["total_taxable_value"]) == Decimal("250.00")
    assert _dec(data["total_cgst"]) == Decimal("0.00")
    assert _dec(data["total_sgst"]) == Decimal("0.00")
    assert _dec(data["total_igst"]) == Decimal("38.50")
    assert _dec(data["grand_total"]) == Decimal("288.50")

    items = data["items"]
    assert len(items) == 2
    line1 = items[0]
    assert _dec(line1["igst_amount"]) == Decimal("36.00")
    line2 = items[1]
    assert _dec(line2["igst_amount"]) == Decimal("2.50")


@pytest.mark.parametrize(
    "bad_gstin",
    ["", "1", "99ABCDE1234F1Z5", "AAABCDE1234F1Z5"],
)
def test_generate_invoice_invalid_gstin_returns_400(bad_gstin: str) -> None:
    order_id = _create_sample_order()
    r = client.post(
        f"/api/v1/mock/orders/{order_id}/generate-invoice",
        json={"customer_gstin": bad_gstin},
    )
    assert r.status_code == 400
    data = r.json()
    assert "detail" in data
