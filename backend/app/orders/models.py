"""Order models for GST invoice generation"""
from datetime import datetime
from typing import List


class OrderItem:
    """Represents a single item in an order"""
    
    def __init__(
        self,
        product_name: str,
        quantity: int,
        unit_price: float,
        hsn_code: str = "00000000"
    ):
        self.product_name = product_name
        self.quantity = quantity
        self.unit_price = unit_price
        self.hsn_code = hsn_code
        
    @property
    def total_amount(self) -> float:
        """Calculate total amount for this item"""
        return self.quantity * self.unit_price


class Order:
    """Represents a customer order"""
    
    def __init__(
        self,
        order_id: int,
        customer_name: str,
        customer_gstin: str,
        customer_address: str,
        items: List[OrderItem],
        order_date: datetime | None = None
    ):
        self.order_id = order_id
        self.customer_name = customer_name
        self.customer_gstin = customer_gstin
        self.customer_address = customer_address
        self.items = items
        self.order_date = order_date or datetime.utcnow()
        
    @property
    def subtotal(self) -> float:
        """Calculate order subtotal (before tax)"""
        return sum(item.total_amount for item in self.items)


class GSTInvoice:
    """Represents a GST-compliant invoice"""
    
    def __init__(
        self,
        invoice_number: str,
        invoice_date: datetime,
        order: Order,
        seller_gstin: str,
        seller_name: str,
        seller_address: str,
        subtotal: float,
        cgst_rate: float,
        cgst_amount: float,
        sgst_rate: float,
        sgst_amount: float,
        igst_rate: float,
        igst_amount: float,
        total_tax: float,
        grand_total: float
    ):
        self.invoice_number = invoice_number
        self.invoice_date = invoice_date
        self.order = order
        self.seller_gstin = seller_gstin
        self.seller_name = seller_name
        self.seller_address = seller_address
        self.subtotal = subtotal
        self.cgst_rate = cgst_rate
        self.cgst_amount = cgst_amount
        self.sgst_rate = sgst_rate
        self.sgst_amount = sgst_amount
        self.igst_rate = igst_rate
        self.igst_amount = igst_amount
        self.total_tax = total_tax
        self.grand_total = grand_total
