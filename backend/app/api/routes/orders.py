"""API routes for orders and GST invoice generation"""
from typing import List

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.orders.models import Order, OrderItem
from app.orders.repository import order_repository
from app.orders.schemas import (
    GSTInvoiceRequest,
    GSTInvoiceResponse,
    OrderCreate,
    OrderItemResponse,
    OrderResponse,
)
from app.orders.service import extract_state_code, generate_gst_invoice

router = APIRouter()


@router.post("/", response_model=OrderResponse, status_code=201)
def create_order(order_data: OrderCreate) -> OrderResponse:
    """
    Create a new order
    
    This is a mock endpoint for testing GST invoice generation.
    """
    # Create order items
    items = [
        OrderItem(
            product_name=item.product_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            hsn_code=item.hsn_code,
        )
        for item in order_data.items
    ]
    
    # Create order
    order = Order(
        order_id=0,  # Will be assigned by repository
        customer_name=order_data.customer_name,
        customer_gstin=order_data.customer_gstin,
        customer_address=order_data.customer_address,
        items=items,
    )
    
    # Save order
    saved_order = order_repository.create(order)
    
    # Convert to response
    return OrderResponse(
        order_id=saved_order.order_id,
        customer_name=saved_order.customer_name,
        customer_gstin=saved_order.customer_gstin,
        customer_address=saved_order.customer_address,
        items=[
            OrderItemResponse(
                product_name=item.product_name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                hsn_code=item.hsn_code,
                total_amount=item.total_amount,
            )
            for item in saved_order.items
        ],
        subtotal=saved_order.subtotal,
        order_date=saved_order.order_date,
    )


@router.get("/", response_model=List[OrderResponse])
def list_orders() -> List[OrderResponse]:
    """
    List all orders
    
    This is a mock endpoint for testing.
    """
    orders = order_repository.get_all()
    
    return [
        OrderResponse(
            order_id=order.order_id,
            customer_name=order.customer_name,
            customer_gstin=order.customer_gstin,
            customer_address=order.customer_address,
            items=[
                OrderItemResponse(
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    hsn_code=item.hsn_code,
                    total_amount=item.total_amount,
                )
                for item in order.items
            ],
            subtotal=order.subtotal,
            order_date=order.order_date,
        )
        for order in orders
    ]


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int) -> OrderResponse:
    """
    Get a specific order by ID
    """
    order = order_repository.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    
    return OrderResponse(
        order_id=order.order_id,
        customer_name=order.customer_name,
        customer_gstin=order.customer_gstin,
        customer_address=order.customer_address,
        items=[
            OrderItemResponse(
                product_name=item.product_name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                hsn_code=item.hsn_code,
                total_amount=item.total_amount,
            )
            for item in order.items
        ],
        subtotal=order.subtotal,
        order_date=order.order_date,
    )


@router.post("/{order_id}/generate-invoice", response_model=GSTInvoiceResponse)
def generate_invoice(order_id: int, request: GSTInvoiceRequest) -> GSTInvoiceResponse:
    """
    Generate a GST-compliant invoice for an order
    
    The invoice calculates:
    - **CGST + SGST** for intra-state transactions (same state code)
    - **IGST** for inter-state transactions (different state codes)
    
    State codes are extracted from the GSTIN (first 2 digits).
    """
    # Generate invoice
    invoice = generate_gst_invoice(order_id, request.customer_gstin)
    
    # Extract state codes
    seller_state_code = extract_state_code(invoice.seller_gstin)
    customer_state_code = extract_state_code(invoice.order.customer_gstin)
    
    # Build response
    return GSTInvoiceResponse(
        invoice_number=invoice.invoice_number,
        invoice_date=invoice.invoice_date,
        # Seller details
        seller_gstin=invoice.seller_gstin,
        seller_name=invoice.seller_name,
        seller_address=invoice.seller_address,
        seller_state_code=seller_state_code,
        # Customer details
        customer_name=invoice.order.customer_name,
        customer_gstin=invoice.order.customer_gstin,
        customer_address=invoice.order.customer_address,
        customer_state_code=customer_state_code,
        # Order details
        order_id=invoice.order.order_id,
        order_date=invoice.order.order_date,
        items=[
            OrderItemResponse(
                product_name=item.product_name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                hsn_code=item.hsn_code,
                total_amount=item.total_amount,
            )
            for item in invoice.order.items
        ],
        # Tax calculation
        subtotal=invoice.subtotal,
        cgst_rate=invoice.cgst_rate,
        cgst_amount=invoice.cgst_amount,
        sgst_rate=invoice.sgst_rate,
        sgst_amount=invoice.sgst_amount,
        igst_rate=invoice.igst_rate,
        igst_amount=invoice.igst_amount,
        total_tax=invoice.total_tax,
        grand_total=invoice.grand_total,
        # Transaction type
        is_intra_state=(seller_state_code == customer_state_code),
    )
