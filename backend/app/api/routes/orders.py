from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.orders.repository import order_repo
from app.orders.schemas import (
    GenerateInvoiceRequest,
    InvoiceOut,
    OrderCreate,
    OrderItemOut,
    OrderOut,
)
from app.orders.service import generate_gst_invoice

router = APIRouter(prefix="/mock/orders", tags=["orders-mock"])


@router.post("/", response_model=OrderOut)
def create_order(order_in: OrderCreate) -> OrderOut:
    order = order_repo.create(order_in)
    items = [
        OrderItemOut(
            sku=i.sku,
            description=i.description,
            quantity=i.quantity,
            unit_price=i.unit_price,
            gst_rate=i.gst_rate,
            taxable_value=i.taxable_value,
        )
        for i in order.items
    ]
    return OrderOut(id=order.id, items=items)


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int) -> OrderOut:
    order = order_repo.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    items = [
        OrderItemOut(
            sku=i.sku,
            description=i.description,
            quantity=i.quantity,
            unit_price=i.unit_price,
            gst_rate=i.gst_rate,
            taxable_value=i.taxable_value,
        )
        for i in order.items
    ]
    return OrderOut(id=order.id, items=items)


@router.post("/{order_id}/generate-invoice", response_model=InvoiceOut)
def create_invoice(order_id: int, body: GenerateInvoiceRequest) -> InvoiceOut:
    try:
        return generate_gst_invoice(order_id=order_id, customer_gstin=body.customer_gstin)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
