"""Pydantic schemas for orders and GST invoices"""
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, field_validator


class OrderItemCreate(BaseModel):
    """Schema for creating an order item"""
    product_name: str = Field(..., min_length=1, max_length=200)
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)
    hsn_code: str = Field(default="00000000", min_length=4, max_length=8)


class OrderItemResponse(BaseModel):
    """Schema for order item response"""
    product_name: str
    quantity: int
    unit_price: float
    hsn_code: str
    total_amount: float


class OrderCreate(BaseModel):
    """Schema for creating an order"""
    customer_name: str = Field(..., min_length=1, max_length=200)
    customer_gstin: str = Field(..., min_length=15, max_length=15)
    customer_address: str = Field(..., min_length=1, max_length=500)
    items: List[OrderItemCreate] = Field(..., min_items=1)
    
    @field_validator("customer_gstin")
    @classmethod
    def validate_gstin(cls, v: str) -> str:
        """Validate GSTIN format"""
        if len(v) != 15:
            raise ValueError("GSTIN must be 15 characters long")
        # Basic format: 2 digits state code + 10 alphanumeric PAN + 1 letter + 1 digit + 1 letter/digit + 1 digit/letter
        if not v[:2].isdigit():
            raise ValueError("First 2 characters must be state code (digits)")
        return v.upper()


class OrderResponse(BaseModel):
    """Schema for order response"""
    order_id: int
    customer_name: str
    customer_gstin: str
    customer_address: str
    items: List[OrderItemResponse]
    subtotal: float
    order_date: datetime


class GSTInvoiceRequest(BaseModel):
    """Schema for GST invoice generation request"""
    customer_gstin: str = Field(..., min_length=15, max_length=15)
    
    @field_validator("customer_gstin")
    @classmethod
    def validate_gstin(cls, v: str) -> str:
        """Validate GSTIN format"""
        if len(v) != 15:
            raise ValueError("GSTIN must be 15 characters long")
        if not v[:2].isdigit():
            raise ValueError("First 2 characters must be state code (digits)")
        return v.upper()


class GSTInvoiceResponse(BaseModel):
    """Schema for GST invoice response"""
    invoice_number: str
    invoice_date: datetime
    
    # Seller details
    seller_gstin: str
    seller_name: str
    seller_address: str
    seller_state_code: str
    
    # Customer details
    customer_name: str
    customer_gstin: str
    customer_address: str
    customer_state_code: str
    
    # Order details
    order_id: int
    order_date: datetime
    items: List[OrderItemResponse]
    
    # Tax calculation
    subtotal: float
    cgst_rate: float
    cgst_amount: float
    sgst_rate: float
    sgst_amount: float
    igst_rate: float
    igst_amount: float
    total_tax: float
    grand_total: float
    
    # Transaction type
    is_intra_state: bool
    
    class Config:
        from_attributes = True
