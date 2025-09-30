"""
Pytest tests for GST invoice generation

Tests cover:
1. Intra-state transactions (CGST + SGST)
2. Inter-state transactions (IGST)
3. Invalid GSTIN handling
4. Order not found scenarios
5. Tax calculation accuracy
"""
import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.orders.models import Order, OrderItem
from app.orders.repository import order_repository
from app.orders.service import (
    calculate_gst_rates,
    extract_state_code,
    generate_gst_invoice,
)


@pytest.fixture(autouse=True)
def reset_repository():
    """Reset the order repository before each test"""
    order_repository._orders.clear()
    order_repository._next_id = 1
    yield


def create_sample_order(customer_gstin: str = "29ABCDE1234F1Z5") -> Order:
    """Helper to create a sample order"""
    items = [
        OrderItem(
            product_name="Laptop",
            quantity=1,
            unit_price=50000.0,
            hsn_code="84713000"
        ),
        OrderItem(
            product_name="Mouse",
            quantity=2,
            unit_price=500.0,
            hsn_code="84716060"
        ),
    ]
    
    order = Order(
        order_id=0,
        customer_name="John Doe",
        customer_gstin=customer_gstin,
        customer_address="123 MG Road, Bangalore, Karnataka - 560001",
        items=items,
    )
    
    return order_repository.create(order)


class TestStateCodeExtraction:
    """Test state code extraction from GSTIN"""
    
    def test_extract_state_code_valid(self):
        """Test extracting state code from valid GSTIN"""
        assert extract_state_code("29ABCDE1234F1Z5") == "29"
        assert extract_state_code("27XYZPQ5678G2A1") == "27"
        assert extract_state_code("06MNOPQ9876H3B2") == "06"
    
    def test_extract_state_code_invalid(self):
        """Test extracting state code from invalid GSTIN"""
        with pytest.raises(ValueError):
            extract_state_code("1")


class TestGSTRateCalculation:
    """Test GST rate calculation logic"""
    
    def test_intra_state_rates(self):
        """Test GST rates for intra-state transaction (same state)"""
        cgst, sgst, igst = calculate_gst_rates("29", "29")
        assert cgst == 9.0
        assert sgst == 9.0
        assert igst == 0.0
    
    def test_inter_state_rates(self):
        """Test GST rates for inter-state transaction (different states)"""
        cgst, sgst, igst = calculate_gst_rates("29", "27")
        assert cgst == 0.0
        assert sgst == 0.0
        assert igst == 18.0
    
    def test_total_tax_same(self):
        """Verify total tax is same for intra and inter-state"""
        cgst1, sgst1, igst1 = calculate_gst_rates("29", "29")
        cgst2, sgst2, igst2 = calculate_gst_rates("29", "27")
        assert cgst1 + sgst1 == igst2


class TestGSTInvoiceGeneration:
    """Test GST invoice generation"""
    
    def test_generate_invoice_intra_state(self):
        """Test invoice generation for intra-state transaction"""
        # Create order with Karnataka GSTIN
        order = create_sample_order("29XYZPQ5678G2A1")
        
        # Generate invoice (seller is also in Karnataka - 29)
        invoice = generate_gst_invoice(order.order_id, "29XYZPQ5678G2A1")
        
        # Verify invoice details
        assert invoice.invoice_number.startswith(f"INV-{order.order_id}")
        assert invoice.order.order_id == order.order_id
        assert invoice.seller_gstin == settings.SELLER_GSTIN
        
        # Verify amounts
        expected_subtotal = 51000.0  # 50000 + 1000
        assert invoice.subtotal == expected_subtotal
        
        # Verify CGST + SGST (intra-state)
        assert invoice.cgst_rate == 9.0
        assert invoice.sgst_rate == 9.0
        assert invoice.igst_rate == 0.0
        
        assert invoice.cgst_amount == 4590.0  # 9% of 51000
        assert invoice.sgst_amount == 4590.0  # 9% of 51000
        assert invoice.igst_amount == 0.0
        
        assert invoice.total_tax == 9180.0  # CGST + SGST
        assert invoice.grand_total == 60180.0  # 51000 + 9180
    
    def test_generate_invoice_inter_state(self):
        """Test invoice generation for inter-state transaction"""
        # Create order with Maharashtra GSTIN
        order = create_sample_order("27ABCDE1234F1Z5")
        
        # Generate invoice (seller in Karnataka - 29, customer in Maharashtra - 27)
        invoice = generate_gst_invoice(order.order_id, "27ABCDE1234F1Z5")
        
        # Verify invoice details
        assert invoice.invoice_number.startswith(f"INV-{order.order_id}")
        assert invoice.order.order_id == order.order_id
        
        # Verify amounts
        expected_subtotal = 51000.0
        assert invoice.subtotal == expected_subtotal
        
        # Verify IGST (inter-state)
        assert invoice.cgst_rate == 0.0
        assert invoice.sgst_rate == 0.0
        assert invoice.igst_rate == 18.0
        
        assert invoice.cgst_amount == 0.0
        assert invoice.sgst_amount == 0.0
        assert invoice.igst_amount == 9180.0  # 18% of 51000
        
        assert invoice.total_tax == 9180.0  # IGST
        assert invoice.grand_total == 60180.0  # 51000 + 9180
    
    def test_generate_invoice_different_customer_gstin(self):
        """Test invoice generation with different customer GSTIN than order"""
        # Create order with one GSTIN
        order = create_sample_order("29ABCDE1234F1Z5")
        
        # Generate invoice with different GSTIN
        invoice = generate_gst_invoice(order.order_id, "27XYZPQ5678G2A1")
        
        # Verify GSTIN is updated
        assert invoice.order.customer_gstin == "27XYZPQ5678G2A1"
        
        # Should be inter-state (29 -> 27)
        assert invoice.igst_rate == 18.0
        assert invoice.cgst_rate == 0.0
        assert invoice.sgst_rate == 0.0
    
    def test_generate_invoice_order_not_found(self):
        """Test invoice generation for non-existent order"""
        with pytest.raises(HTTPException) as exc_info:
            generate_gst_invoice(999, "29ABCDE1234F1Z5")
        
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail).lower()
    
    def test_generate_invoice_invalid_gstin_length(self):
        """Test invoice generation with invalid GSTIN length"""
        order = create_sample_order("29ABCDE1234F1Z5")
        
        with pytest.raises(HTTPException) as exc_info:
            generate_gst_invoice(order.order_id, "29ABCDE")
        
        assert exc_info.value.status_code == 400
        assert "15 characters" in str(exc_info.value.detail)
    
    def test_generate_invoice_invalid_gstin_format(self):
        """Test invoice generation with invalid GSTIN format"""
        order = create_sample_order("29ABCDE1234F1Z5")
        
        with pytest.raises(HTTPException) as exc_info:
            generate_gst_invoice(order.order_id, "ABABCDE1234F1Z5")
        
        assert exc_info.value.status_code == 400
        assert "state code" in str(exc_info.value.detail).lower()


class TestTaxCalculationAccuracy:
    """Test tax calculation accuracy for various scenarios"""
    
    def test_rounding_precision(self):
        """Test that tax calculations are rounded correctly"""
        items = [
            OrderItem(
                product_name="Item with odd price",
                quantity=1,
                unit_price=1234.56,
                hsn_code="12345678"
            ),
        ]
        
        order = Order(
            order_id=0,
            customer_name="Test Customer",
            customer_gstin="29ABCDE1234F1Z5",
            customer_address="Test Address",
            items=items,
        )
        order = order_repository.create(order)
        
        invoice = generate_gst_invoice(order.order_id, "29ABCDE1234F1Z5")
        
        # Verify amounts are rounded to 2 decimal places
        assert invoice.subtotal == 1234.56
        assert invoice.cgst_amount == 111.11  # 9% of 1234.56 = 111.1104 -> 111.11
        assert invoice.sgst_amount == 111.11
        assert invoice.grand_total == 1456.78  # 1234.56 + 222.22 = 1456.78
    
    def test_multiple_items_tax_calculation(self):
        """Test tax calculation with multiple items"""
        items = [
            OrderItem(product_name="Item 1", quantity=2, unit_price=1000.0, hsn_code="11111111"),
            OrderItem(product_name="Item 2", quantity=3, unit_price=500.0, hsn_code="22222222"),
            OrderItem(product_name="Item 3", quantity=1, unit_price=2500.0, hsn_code="33333333"),
        ]
        
        order = Order(
            order_id=0,
            customer_name="Test Customer",
            customer_gstin="06ABCDE1234F1Z5",  # Delhi
            customer_address="Test Address",
            items=items,
        )
        order = order_repository.create(order)
        
        # Generate invoice for inter-state (29 -> 06)
        invoice = generate_gst_invoice(order.order_id, "06ABCDE1234F1Z5")
        
        # Verify subtotal: (2*1000) + (3*500) + (1*2500) = 6000
        assert invoice.subtotal == 6000.0
        
        # Verify IGST: 18% of 6000 = 1080
        assert invoice.igst_amount == 1080.0
        assert invoice.grand_total == 7080.0
    
    def test_zero_state_tax_in_inter_state(self):
        """Ensure CGST and SGST are zero in inter-state transactions"""
        order = create_sample_order("27ABCDE1234F1Z5")
        invoice = generate_gst_invoice(order.order_id, "27ABCDE1234F1Z5")
        
        # Change to inter-state
        invoice = generate_gst_invoice(order.order_id, "06ABCDE1234F1Z5")
        
        assert invoice.cgst_amount == 0.0
        assert invoice.sgst_amount == 0.0
        assert invoice.igst_amount > 0.0
    
    def test_zero_igst_in_intra_state(self):
        """Ensure IGST is zero in intra-state transactions"""
        order = create_sample_order("29ABCDE1234F1Z5")
        invoice = generate_gst_invoice(order.order_id, "29ABCDE1234F1Z5")
        
        assert invoice.igst_amount == 0.0
        assert invoice.cgst_amount > 0.0
        assert invoice.sgst_amount > 0.0


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_single_item_order(self):
        """Test invoice generation with single item"""
        items = [
            OrderItem(product_name="Single Item", quantity=1, unit_price=100.0, hsn_code="12345678"),
        ]
        
        order = Order(
            order_id=0,
            customer_name="Test Customer",
            customer_gstin="29ABCDE1234F1Z5",
            customer_address="Test Address",
            items=items,
        )
        order = order_repository.create(order)
        
        invoice = generate_gst_invoice(order.order_id, "29ABCDE1234F1Z5")
        
        assert invoice.subtotal == 100.0
        assert invoice.grand_total == 118.0  # 100 + 18% tax
    
    def test_gstin_case_insensitive(self):
        """Test that GSTIN is handled case-insensitively"""
        order = create_sample_order("29ABCDE1234F1Z5")
        
        # Use lowercase GSTIN
        invoice = generate_gst_invoice(order.order_id, "29abcde1234f1z5")
        
        # Should be converted to uppercase
        assert invoice.order.customer_gstin == "29ABCDE1234F1Z5"
    
    def test_all_state_codes(self):
        """Test various state codes"""
        state_codes = ["01", "06", "09", "19", "27", "29", "33", "36"]
        
        for state_code in state_codes:
            customer_gstin = f"{state_code}ABCDE1234F1Z5"
            order = create_sample_order(customer_gstin)
            
            invoice = generate_gst_invoice(order.order_id, customer_gstin)
            
            extracted_code = extract_state_code(invoice.order.customer_gstin)
            assert extracted_code == state_code
