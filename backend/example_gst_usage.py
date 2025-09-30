"""
Example script demonstrating GST invoice generation

This script shows how to use the GST invoice feature programmatically.
Run this from the backend directory: python example_gst_usage.py
"""
from datetime import datetime

from app.orders.models import Order, OrderItem
from app.orders.repository import order_repository
from app.orders.service import generate_gst_invoice


def print_separator():
    print("\n" + "="*80 + "\n")


def print_invoice(invoice):
    """Pretty print an invoice"""
    print(f"INVOICE: {invoice.invoice_number}")
    print(f"Date: {invoice.invoice_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print_separator()
    
    print("SELLER DETAILS:")
    print(f"  GSTIN: {invoice.seller_gstin}")
    print(f"  Name: {invoice.seller_name}")
    print(f"  Address: {invoice.seller_address}")
    print(f"  State Code: {invoice.seller_gstin[:2]}")
    print_separator()
    
    print("CUSTOMER DETAILS:")
    print(f"  GSTIN: {invoice.order.customer_gstin}")
    print(f"  Name: {invoice.order.customer_name}")
    print(f"  Address: {invoice.order.customer_address}")
    print(f"  State Code: {invoice.order.customer_gstin[:2]}")
    print_separator()
    
    print("ITEMS:")
    for item in invoice.order.items:
        print(f"  • {item.product_name}")
        print(f"    HSN: {item.hsn_code}")
        print(f"    Qty: {item.quantity} × ₹{item.unit_price:,.2f} = ₹{item.total_amount:,.2f}")
    print_separator()
    
    print("TAX CALCULATION:")
    print(f"  Subtotal:        ₹{invoice.subtotal:,.2f}")
    print()
    
    if invoice.cgst_amount > 0:
        print(f"  CGST ({invoice.cgst_rate}%):     ₹{invoice.cgst_amount:,.2f}")
        print(f"  SGST ({invoice.sgst_rate}%):     ₹{invoice.sgst_amount:,.2f}")
        print(f"  [Intra-State Transaction]")
    else:
        print(f"  IGST ({invoice.igst_rate}%):    ₹{invoice.igst_amount:,.2f}")
        print(f"  [Inter-State Transaction]")
    
    print()
    print(f"  Total Tax:       ₹{invoice.total_tax:,.2f}")
    print(f"  GRAND TOTAL:     ₹{invoice.grand_total:,.2f}")
    print_separator()


def example_intra_state():
    """Example: Intra-state transaction (Karnataka to Karnataka)"""
    print("EXAMPLE 1: INTRA-STATE TRANSACTION")
    print("Seller: Karnataka (29) → Customer: Karnataka (29)")
    print_separator()
    
    # Create order
    items = [
        OrderItem(
            product_name="Dell Laptop",
            quantity=1,
            unit_price=55000.0,
            hsn_code="84713000"
        ),
        OrderItem(
            product_name="Wireless Mouse",
            quantity=2,
            unit_price=800.0,
            hsn_code="84716060"
        ),
        OrderItem(
            product_name="USB Cable",
            quantity=3,
            unit_price=200.0,
            hsn_code="85444900"
        ),
    ]
    
    order = Order(
        order_id=0,
        customer_name="Bangalore Tech Solutions Pvt Ltd",
        customer_gstin="29BGLTS1234F1Z5",  # Karnataka
        customer_address="#45, Residency Road, Bangalore, Karnataka - 560025",
        items=items,
    )
    
    saved_order = order_repository.create(order)
    print(f"✓ Order created: #{saved_order.order_id}")
    
    # Generate invoice
    invoice = generate_gst_invoice(saved_order.order_id, "29BGLTS1234F1Z5")
    print(f"✓ Invoice generated: {invoice.invoice_number}")
    print_separator()
    
    print_invoice(invoice)


def example_inter_state():
    """Example: Inter-state transaction (Karnataka to Maharashtra)"""
    print("\nEXAMPLE 2: INTER-STATE TRANSACTION")
    print("Seller: Karnataka (29) → Customer: Maharashtra (27)")
    print_separator()
    
    # Create order
    items = [
        OrderItem(
            product_name="HP Printer",
            quantity=1,
            unit_price=15000.0,
            hsn_code="84433100"
        ),
        OrderItem(
            product_name="Printer Paper (500 sheets)",
            quantity=10,
            unit_price=250.0,
            hsn_code="48025610"
        ),
    ]
    
    order = Order(
        order_id=0,
        customer_name="Mumbai Office Supplies Ltd",
        customer_gstin="27MBOFS1234G2A1",  # Maharashtra
        customer_address="12th Floor, Nariman Point, Mumbai, Maharashtra - 400021",
        items=items,
    )
    
    saved_order = order_repository.create(order)
    print(f"✓ Order created: #{saved_order.order_id}")
    
    # Generate invoice
    invoice = generate_gst_invoice(saved_order.order_id, "27MBOFS1234G2A1")
    print(f"✓ Invoice generated: {invoice.invoice_number}")
    print_separator()
    
    print_invoice(invoice)


def example_tax_comparison():
    """Example: Compare tax for same order with different customer locations"""
    print("\nEXAMPLE 3: TAX COMPARISON - SAME ORDER, DIFFERENT STATES")
    print_separator()
    
    # Create single order
    items = [
        OrderItem(
            product_name="MacBook Pro",
            quantity=1,
            unit_price=120000.0,
            hsn_code="84713000"
        ),
    ]
    
    order = Order(
        order_id=0,
        customer_name="Tech Corp",
        customer_gstin="29DUMMY1234F1Z5",
        customer_address="Sample Address",
        items=items,
    )
    
    saved_order = order_repository.create(order)
    print(f"Order: ₹1,20,000 MacBook Pro")
    print_separator()
    
    # Scenario 1: Karnataka customer (Intra-state)
    invoice1 = generate_gst_invoice(saved_order.order_id, "29KRNTK1234F1Z5")
    print("SCENARIO A: Karnataka Customer (Intra-State)")
    print(f"  State Code: 29 (Same as seller)")
    print(f"  CGST (9%): ₹{invoice1.cgst_amount:,.2f}")
    print(f"  SGST (9%): ₹{invoice1.sgst_amount:,.2f}")
    print(f"  IGST (0%): ₹{invoice1.igst_amount:,.2f}")
    print(f"  Total:     ₹{invoice1.grand_total:,.2f}")
    print()
    
    # Scenario 2: Delhi customer (Inter-state)
    invoice2 = generate_gst_invoice(saved_order.order_id, "07DELHI1234G2A1")
    print("SCENARIO B: Delhi Customer (Inter-State)")
    print(f"  State Code: 07 (Different from seller)")
    print(f"  CGST (0%): ₹{invoice2.cgst_amount:,.2f}")
    print(f"  SGST (0%): ₹{invoice2.sgst_amount:,.2f}")
    print(f"  IGST (18%): ₹{invoice2.igst_amount:,.2f}")
    print(f"  Total:     ₹{invoice2.grand_total:,.2f}")
    print()
    
    print("OBSERVATION:")
    print(f"  Both scenarios result in same total tax (18% = 9%+9%)")
    print(f"  Only the tax structure differs based on state")
    print_separator()


def main():
    """Run all examples"""
    print("\n" + "🇮🇳 GST INVOICE GENERATION EXAMPLES 🇮🇳".center(80))
    print_separator()
    
    # Reset repository
    order_repository._orders.clear()
    order_repository._next_id = 1
    
    # Run examples
    example_intra_state()
    example_inter_state()
    example_tax_comparison()
    
    print("\n✓ All examples completed successfully!")
    print(f"\nTotal orders created: {len(order_repository.get_all())}")
    print_separator()


if __name__ == "__main__":
    main()
