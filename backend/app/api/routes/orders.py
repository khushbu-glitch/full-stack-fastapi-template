from fastapi import APIRouter, HTTPException
from app.orders.schemas import OrderCreate, Order, Invoice
from app.orders.repository import order_repository
from app.orders.service import generate_gst_invoice as generate_gst_invoice_service

router = APIRouter()

@router.post("/mock/orders/", response_model=Order)
def create_order(order: OrderCreate):
    return order_repository.create_order(amount=order.amount, customer_gstin=order.customer_gstin)

@router.post("/mock/orders/{order_id}/generate-invoice", response_model=Invoice)
def generate_invoice(order_id: int, customer_gstin: str):
    try:
        return generate_gst_invoice_service(order_id=order_id, customer_gstin=customer_gstin)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
