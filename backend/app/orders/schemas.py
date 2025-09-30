from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field as PydField


class OrderItemCreate(BaseModel):
    sku: str = PydField(min_length=1, max_length=64)
    description: Optional[str] = PydField(default=None, max_length=255)
    quantity: int = PydField(gt=0)
    unit_price: Decimal = PydField(gt=Decimal("0"))
    gst_rate: Decimal = PydField(ge=Decimal("0"))


class OrderCreate(BaseModel):
    items: List[OrderItemCreate]


class OrderItemOut(BaseModel):
    sku: str
    description: Optional[str]
    quantity: int
    unit_price: Decimal
    gst_rate: Decimal
    taxable_value: Decimal


class OrderOut(BaseModel):
    id: int
    items: List[OrderItemOut]


class InvoiceItemOut(BaseModel):
    sku: str
    description: Optional[str]
    quantity: int
    unit_price: Decimal
    gst_rate: Decimal
    taxable_value: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    total_with_tax: Decimal


class InvoiceOut(BaseModel):
    order_id: int
    seller_gstin: str
    seller_state_code: str
    customer_gstin: str
    customer_state_code: str
    supply_type: str  # "intra" or "inter"
    items: List[InvoiceItemOut]
    total_taxable_value: Decimal
    total_cgst: Decimal
    total_sgst: Decimal
    total_igst: Decimal
    grand_total: Decimal


class GenerateInvoiceRequest(BaseModel):
    customer_gstin: str
