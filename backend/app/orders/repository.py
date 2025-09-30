from typing import Dict, List
from .models import Order

class InMemoryOrderRepository:
    def __init__(self):
        self.orders: Dict[int, Order] = {}
        self.next_id = 1

    def create_order(self, amount: float, customer_gstin: str | None) -> Order:
        order = Order(id=self.next_id, amount=amount, customer_gstin=customer_gstin)
        self.orders[self.next_id] = order
        self.next_id += 1
        return order

    def get_order(self, order_id: int) -> Order | None:
        return self.orders.get(order_id)

order_repository = InMemoryOrderRepository()
