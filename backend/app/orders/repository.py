from __future__ import annotations

from decimal import Decimal
from itertools import count
from threading import RLock
from typing import Dict, List, Optional

from .models import Order, OrderItem
from .schemas import OrderCreate, OrderItemCreate


class InMemoryOrderRepository:
    def __init__(self) -> None:
        self._orders: Dict[int, Order] = {}
        self._seq = count(1)
        self._lock = RLock()

    def create(self, order_in: OrderCreate) -> Order:
        with self._lock:
            order_id = next(self._seq)
            items: List[OrderItem] = [
                OrderItem(
                    sku=i.sku,
                    description=i.description,
                    quantity=i.quantity,
                    unit_price=Decimal(i.unit_price),
                    gst_rate=Decimal(i.gst_rate),
                )
                for i in order_in.items
            ]
            order = Order(id=order_id, items=items)
            self._orders[order_id] = order
            return order

    def get(self, order_id: int) -> Optional[Order]:
        return self._orders.get(order_id)

    def clear(self) -> None:
        with self._lock:
            self._orders.clear()
            # reset sequence
            self._seq = count(1)


order_repo = InMemoryOrderRepository()
