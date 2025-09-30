"""
Integration tests for GST invoice API endpoints

Tests the full API flow:
1. Create order
2. Generate invoice
3. Verify response structure and calculations
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.orders.repository import order_repository

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_repository():
    """Reset the order repository before each test"""
    order_repository._orders.clear()
    order_repository._next_id = 1
    yield


class TestOrderAPI:
    """Test order creation and retrieval endpoints"""
    
    def test_create_order_success(self):
        """Test successful order creation"""
        order_data = {
            "customer_name": "John Doe",
            "customer_gstin": "29ABCDE1234F1Z5",
            "customer_address": "123 MG Road, Bangalore, Karnataka - 560001",
            "items": [
                {
                    "product_name": "Laptop",
                    "quantity": 1,
                    "unit_price": 50000.0,
                    "hsn_code": "84713000"
                },
                {
                    "product_name": "Mouse",
                    "quantity": 2,
                    "unit_price": 500.0,
                    "hsn_code": "84716060"
                }
            ]
        }
        
        response = client.post("/api/v1/mock/orders/", json=order_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["order_id"] == 1
        assert data["customer_name"] == "John Doe"
        assert data["customer_gstin"] == "29ABCDE1234F1Z5"
        assert len(data["items"]) == 2
        assert data["subtotal"] == 51000.0
    
    def test_create_order_invalid_gstin_length(self):
        """Test order creation with invalid GSTIN length"""
        order_data = {
            "customer_name": "John Doe",
            "customer_gstin": "29ABCDE",  # Too short
            "customer_address": "123 MG Road",
            "items": [
                {
                    "product_name": "Item",
                    "quantity": 1,
                    "unit_price": 100.0
                }
            ]
        }
        
        response = client.post("/api/v1/mock/orders/", json=order_data)
        
        assert response.status_code == 422
    
    def test_create_order_invalid_gstin_format(self):
        """Test order creation with invalid GSTIN format"""
        order_data = {
            "customer_name": "John Doe",
            "customer_gstin": "ABABCDE1234F1Z5",  # Invalid state code
            "customer_address": "123 MG Road",
            "items": [
                {
                    "product_name": "Item",
                    "quantity": 1,
                    "unit_price": 100.0
                }
            ]
        }
        
        response = client.post("/api/v1/mock/orders/", json=order_data)
        
        assert response.status_code == 422
    
    def test_get_order_success(self):
        """Test retrieving a specific order"""
        # Create order first
        order_data = {
            "customer_name": "Jane Smith",
            "customer_gstin": "27XYZPQ5678G2A1",
            "customer_address": "456 Park Street, Mumbai",
            "items": [
                {
                    "product_name": "Keyboard",
                    "quantity": 1,
                    "unit_price": 2000.0
                }
            ]
        }
        
        create_response = client.post("/api/v1/mock/orders/", json=order_data)
        order_id = create_response.json()["order_id"]
        
        # Retrieve order
        response = client.get(f"/api/v1/mock/orders/{order_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["order_id"] == order_id
        assert data["customer_name"] == "Jane Smith"
        assert data["subtotal"] == 2000.0
    
    def test_get_order_not_found(self):
        """Test retrieving non-existent order"""
        response = client.get("/api/v1/mock/orders/999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_list_orders(self):
        """Test listing all orders"""
        # Create multiple orders
        for i in range(3):
            order_data = {
                "customer_name": f"Customer {i}",
                "customer_gstin": "29ABCDE1234F1Z5",
                "customer_address": f"Address {i}",
                "items": [
                    {
                        "product_name": f"Product {i}",
                        "quantity": 1,
                        "unit_price": 1000.0
                    }
                ]
            }
            client.post("/api/v1/mock/orders/", json=order_data)
        
        # List all orders
        response = client.get("/api/v1/mock/orders/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 3
        assert all(order["order_id"] in [1, 2, 3] for order in data)


class TestInvoiceGenerationAPI:
    """Test invoice generation endpoints"""
    
    def test_generate_invoice_intra_state(self):
        """Test generating invoice for intra-state transaction"""
        # Create order with Karnataka GSTIN
        order_data = {
            "customer_name": "Intra State Customer",
            "customer_gstin": "29ABCDE1234F1Z5",
            "customer_address": "Bangalore, Karnataka",
            "items": [
                {
                    "product_name": "Product A",
                    "quantity": 2,
                    "unit_price": 5000.0,
                    "hsn_code": "12345678"
                }
            ]
        }
        
        create_response = client.post("/api/v1/mock/orders/", json=order_data)
        order_id = create_response.json()["order_id"]
        
        # Generate invoice with same state GSTIN
        invoice_request = {
            "customer_gstin": "29XYZPQ5678G2A1"  # Karnataka
        }
        
        response = client.post(
            f"/api/v1/mock/orders/{order_id}/generate-invoice",
            json=invoice_request
        )
        
        assert response.status_code == 200
        invoice = response.json()
        
        # Verify intra-state transaction
        assert invoice["is_intra_state"] is True
        assert invoice["seller_state_code"] == "29"
        assert invoice["customer_state_code"] == "29"
        
        # Verify CGST + SGST
        assert invoice["cgst_rate"] == 9.0
        assert invoice["sgst_rate"] == 9.0
        assert invoice["igst_rate"] == 0.0
        
        assert invoice["cgst_amount"] == 900.0  # 9% of 10000
        assert invoice["sgst_amount"] == 900.0  # 9% of 10000
        assert invoice["igst_amount"] == 0.0
        
        assert invoice["subtotal"] == 10000.0
        assert invoice["total_tax"] == 1800.0
        assert invoice["grand_total"] == 11800.0
    
    def test_generate_invoice_inter_state(self):
        """Test generating invoice for inter-state transaction"""
        # Create order
        order_data = {
            "customer_name": "Inter State Customer",
            "customer_gstin": "29ABCDE1234F1Z5",
            "customer_address": "Bangalore, Karnataka",
            "items": [
                {
                    "product_name": "Product B",
                    "quantity": 1,
                    "unit_price": 10000.0,
                    "hsn_code": "87654321"
                }
            ]
        }
        
        create_response = client.post("/api/v1/mock/orders/", json=order_data)
        order_id = create_response.json()["order_id"]
        
        # Generate invoice with different state GSTIN
        invoice_request = {
            "customer_gstin": "27XYZPQ5678G2A1"  # Maharashtra
        }
        
        response = client.post(
            f"/api/v1/mock/orders/{order_id}/generate-invoice",
            json=invoice_request
        )
        
        assert response.status_code == 200
        invoice = response.json()
        
        # Verify inter-state transaction
        assert invoice["is_intra_state"] is False
        assert invoice["seller_state_code"] == "29"
        assert invoice["customer_state_code"] == "27"
        
        # Verify IGST
        assert invoice["cgst_rate"] == 0.0
        assert invoice["sgst_rate"] == 0.0
        assert invoice["igst_rate"] == 18.0
        
        assert invoice["cgst_amount"] == 0.0
        assert invoice["sgst_amount"] == 0.0
        assert invoice["igst_amount"] == 1800.0  # 18% of 10000
        
        assert invoice["subtotal"] == 10000.0
        assert invoice["total_tax"] == 1800.0
        assert invoice["grand_total"] == 11800.0
    
    def test_generate_invoice_order_not_found(self):
        """Test generating invoice for non-existent order"""
        invoice_request = {
            "customer_gstin": "29ABCDE1234F1Z5"
        }
        
        response = client.post(
            "/api/v1/mock/orders/999/generate-invoice",
            json=invoice_request
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_generate_invoice_invalid_gstin(self):
        """Test generating invoice with invalid GSTIN"""
        # Create order
        order_data = {
            "customer_name": "Test Customer",
            "customer_gstin": "29ABCDE1234F1Z5",
            "customer_address": "Test Address",
            "items": [
                {
                    "product_name": "Product",
                    "quantity": 1,
                    "unit_price": 1000.0
                }
            ]
        }
        
        create_response = client.post("/api/v1/mock/orders/", json=order_data)
        order_id = create_response.json()["order_id"]
        
        # Try to generate invoice with invalid GSTIN
        invoice_request = {
            "customer_gstin": "INVALID"
        }
        
        response = client.post(
            f"/api/v1/mock/orders/{order_id}/generate-invoice",
            json=invoice_request
        )
        
        assert response.status_code == 422
    
    def test_generate_multiple_invoices_same_order(self):
        """Test generating multiple invoices for same order with different GSTINs"""
        # Create order
        order_data = {
            "customer_name": "Multi Invoice Customer",
            "customer_gstin": "29ABCDE1234F1Z5",
            "customer_address": "Test Address",
            "items": [
                {
                    "product_name": "Product",
                    "quantity": 1,
                    "unit_price": 5000.0
                }
            ]
        }
        
        create_response = client.post("/api/v1/mock/orders/", json=order_data)
        order_id = create_response.json()["order_id"]
        
        # Generate first invoice (intra-state)
        invoice_request_1 = {"customer_gstin": "29XYZPQ5678G2A1"}
        response_1 = client.post(
            f"/api/v1/mock/orders/{order_id}/generate-invoice",
            json=invoice_request_1
        )
        
        assert response_1.status_code == 200
        invoice_1 = response_1.json()
        assert invoice_1["is_intra_state"] is True
        
        # Generate second invoice (inter-state)
        invoice_request_2 = {"customer_gstin": "27XYZPQ5678G2A1"}
        response_2 = client.post(
            f"/api/v1/mock/orders/{order_id}/generate-invoice",
            json=invoice_request_2
        )
        
        assert response_2.status_code == 200
        invoice_2 = response_2.json()
        assert invoice_2["is_intra_state"] is False
        
        # Both should have same subtotal but different tax structure
        assert invoice_1["subtotal"] == invoice_2["subtotal"]
        assert invoice_1["total_tax"] == invoice_2["total_tax"]
        assert invoice_1["grand_total"] == invoice_2["grand_total"]


class TestComplexScenarios:
    """Test complex scenarios with multiple items and calculations"""
    
    def test_invoice_with_multiple_items(self):
        """Test invoice generation with multiple items"""
        order_data = {
            "customer_name": "Complex Order Customer",
            "customer_gstin": "29ABCDE1234F1Z5",
            "customer_address": "Test Address",
            "items": [
                {
                    "product_name": "Item 1",
                    "quantity": 2,
                    "unit_price": 1500.0,
                    "hsn_code": "11111111"
                },
                {
                    "product_name": "Item 2",
                    "quantity": 3,
                    "unit_price": 800.0,
                    "hsn_code": "22222222"
                },
                {
                    "product_name": "Item 3",
                    "quantity": 1,
                    "unit_price": 5000.0,
                    "hsn_code": "33333333"
                }
            ]
        }
        
        create_response = client.post("/api/v1/mock/orders/", json=order_data)
        order_id = create_response.json()["order_id"]
        
        # Generate invoice
        invoice_request = {"customer_gstin": "06ABCDE1234F1Z5"}  # Delhi
        response = client.post(
            f"/api/v1/mock/orders/{order_id}/generate-invoice",
            json=invoice_request
        )
        
        assert response.status_code == 200
        invoice = response.json()
        
        # Verify calculations
        # Subtotal: (2*1500) + (3*800) + (1*5000) = 10400
        assert invoice["subtotal"] == 10400.0
        
        # Inter-state IGST: 18% of 10400 = 1872
        assert invoice["igst_amount"] == 1872.0
        assert invoice["total_tax"] == 1872.0
        assert invoice["grand_total"] == 12272.0
        
        # Verify all items are included
        assert len(invoice["items"]) == 3
    
    def test_invoice_response_structure(self):
        """Test that invoice response has all required fields"""
        # Create order
        order_data = {
            "customer_name": "Structure Test",
            "customer_gstin": "29ABCDE1234F1Z5",
            "customer_address": "Test Address",
            "items": [
                {
                    "product_name": "Product",
                    "quantity": 1,
                    "unit_price": 1000.0
                }
            ]
        }
        
        create_response = client.post("/api/v1/mock/orders/", json=order_data)
        order_id = create_response.json()["order_id"]
        
        # Generate invoice
        invoice_request = {"customer_gstin": "29XYZPQ5678G2A1"}
        response = client.post(
            f"/api/v1/mock/orders/{order_id}/generate-invoice",
            json=invoice_request
        )
        
        assert response.status_code == 200
        invoice = response.json()
        
        # Verify all required fields are present
        required_fields = [
            "invoice_number", "invoice_date",
            "seller_gstin", "seller_name", "seller_address", "seller_state_code",
            "customer_name", "customer_gstin", "customer_address", "customer_state_code",
            "order_id", "order_date", "items",
            "subtotal", "cgst_rate", "cgst_amount", "sgst_rate", "sgst_amount",
            "igst_rate", "igst_amount", "total_tax", "grand_total",
            "is_intra_state"
        ]
        
        for field in required_fields:
            assert field in invoice, f"Missing field: {field}"
