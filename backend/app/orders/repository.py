"""In-memory repository for orders (mock implementation)"""
from typing import Dict, Optional

from app.orders.models import Order


class OrderRepository:
    """In-memory storage for orders"""
    
    def __init__(self):
        self._orders: Dict[int, Order] = {}
        self._next_id: int = 1
    
    def create(self, order: Order) -> Order:
        """Store a new order"""
        order.order_id = self._next_id
        self._orders[self._next_id] = order
        self._next_id += 1
        return order
    
    def get_by_id(self, order_id: int) -> Optional[Order]:
        """Retrieve an order by ID"""
        return self._orders.get(order_id)
    
    def get_all(self) -> list[Order]:
        """Get all orders"""
        return list(self._orders.values())
    
    def delete(self, order_id: int) -> bool:
        """Delete an order"""
        if order_id in self._orders:
            del self._orders[order_id]
            return True
        return False


# Global singleton instance
order_repository = OrderRepository()
