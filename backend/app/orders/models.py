from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from sqlmodel import Field, SQLModel


class OrderItem(SQLModel):
    sku: str = Field(min_length=1, max_length=64)
    description: Optional[str] = Field(default=None, max_length=255)
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(gt=Decimal("0"))
    gst_rate: Decimal = Field(ge=Decimal("0"))  # e.g., 5, 12, 18

    @property
    def taxable_value(self) -> Decimal:
        return (self.unit_price * Decimal(self.quantity)).quantize(Decimal("0.01"))


class Order(SQLModel):
    id: int
    items: List[OrderItem] = Field(default_factory=list)
