import pytest
from unittest.mock import patch
from app.orders.service import generate_gst_invoice
from app.orders.repository import order_repository

@pytest.fixture(autouse=True)
def clear_orders():
    order_repository.orders = {}
    order_repository.next_id = 1

@patch('app.core.config.settings.SELLER_GSTIN', "27ABCDE1234F1Z5") # Maharashtra
def test_generate_intra_state_invoice():
    order = order_repository.create_order(amount=100.0, customer_gstin="27BCDEF2345F2Z6")
    invoice = generate_gst_invoice(order.id, "27BCDEF2345F2Z6")
    assert invoice.subtotal == 100.0
    assert invoice.cgst == 9.0
    assert invoice.sgst == 9.0
    assert invoice.igst == 0.0
    assert invoice.total == 118.0

@patch('app.core.config.settings.SELLER_GSTIN', "27ABCDE1234F1Z5") # Maharashtra
def test_generate_inter_state_invoice():
    order = order_repository.create_order(amount=100.0, customer_gstin="29BCDEF2345F2Z6") # Karnataka
    invoice = generate_gst_invoice(order.id, "29BCDEF2345F2Z6")
    assert invoice.subtotal == 100.0
    assert invoice.cgst == 0.0
    assert invoice.sgst == 0.0
    assert invoice.igst == 18.0
    assert invoice.total == 118.0

def test_generate_invoice_for_nonexistent_order():
    with pytest.raises(ValueError, match="Order not found"):
        generate_gst_invoice(999, "27BCDEF2345F2Z6")
