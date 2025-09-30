"""GST invoice generation service"""
from datetime import datetime

from fastapi import HTTPException

from app.core.config import settings
from app.orders.models import GSTInvoice, Order
from app.orders.repository import order_repository


def extract_state_code(gstin: str) -> str:
    """Extract state code from GSTIN (first 2 digits)"""
    if len(gstin) < 2:
        raise ValueError("Invalid GSTIN format")
    return gstin[:2]


def calculate_gst_rates(seller_state_code: str, customer_state_code: str) -> tuple[float, float, float]:
    """
    Calculate GST rates based on state codes
    
    Returns:
        tuple: (cgst_rate, sgst_rate, igst_rate)
    """
    # Standard GST rate is 18% (can be customized per product category)
    gst_rate = 18.0
    
    if seller_state_code == customer_state_code:
        # Intra-state transaction: CGST + SGST
        cgst_rate = gst_rate / 2  # 9%
        sgst_rate = gst_rate / 2  # 9%
        igst_rate = 0.0
    else:
        # Inter-state transaction: IGST
        cgst_rate = 0.0
        sgst_rate = 0.0
        igst_rate = gst_rate  # 18%
    
    return cgst_rate, sgst_rate, igst_rate


def generate_gst_invoice(order_id: int, customer_gstin: str) -> GSTInvoice:
    """
    Generate a GST-compliant invoice for an order
    
    Args:
        order_id: The order ID
        customer_gstin: Customer's GSTIN
        
    Returns:
        GSTInvoice: Generated invoice with tax calculations
        
    Raises:
        HTTPException: If order not found or GSTIN is invalid
    """
    # Validate GSTIN format
    if len(customer_gstin) != 15:
        raise HTTPException(status_code=400, detail="GSTIN must be 15 characters long")
    
    if not customer_gstin[:2].isdigit():
        raise HTTPException(
            status_code=400, 
            detail="Invalid GSTIN format: first 2 characters must be state code"
        )
    
    # Retrieve order
    order = order_repository.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    
    # Update customer GSTIN if different from order
    order.customer_gstin = customer_gstin.upper()
    
    # Extract state codes
    seller_state_code = settings.SELLER_STATE_CODE
    customer_state_code = extract_state_code(customer_gstin)
    
    # Calculate GST rates
    cgst_rate, sgst_rate, igst_rate = calculate_gst_rates(
        seller_state_code, customer_state_code
    )
    
    # Calculate amounts
    subtotal = order.subtotal
    cgst_amount = round((subtotal * cgst_rate) / 100, 2)
    sgst_amount = round((subtotal * sgst_rate) / 100, 2)
    igst_amount = round((subtotal * igst_rate) / 100, 2)
    total_tax = cgst_amount + sgst_amount + igst_amount
    grand_total = round(subtotal + total_tax, 2)
    
    # Generate invoice number
    invoice_date = datetime.utcnow()
    invoice_number = f"INV-{order_id}-{invoice_date.strftime('%Y%m%d%H%M%S')}"
    
    # Create invoice
    invoice = GSTInvoice(
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        order=order,
        seller_gstin=settings.SELLER_GSTIN,
        seller_name=settings.SELLER_NAME,
        seller_address=settings.SELLER_ADDRESS,
        subtotal=subtotal,
        cgst_rate=cgst_rate,
        cgst_amount=cgst_amount,
        sgst_rate=sgst_rate,
        sgst_amount=sgst_amount,
        igst_rate=igst_rate,
        igst_amount=igst_amount,
        total_tax=total_tax,
        grand_total=grand_total
    )
    
    return invoice
