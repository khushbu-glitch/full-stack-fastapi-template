from pydantic import BaseModel

class OrderCreate(BaseModel):
    amount: float
    customer_gstin: str | None = None

class Order(OrderCreate):
    id: int

    class Config:
        orm_mode = True

class Invoice(BaseModel):
    order_id: int
    customer_gstin: str
    seller_gstin: str
    subtotal: float
    cgst: float
    sgst: float
    igst: float
    total: float
