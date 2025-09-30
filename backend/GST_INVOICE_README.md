# GST Invoice Generation Feature

This document describes the GST-compliant invoice generation system for India e-commerce platforms.

## Overview

The GST invoice feature provides:
- **Automatic GST calculation** based on seller and customer locations
- **Intra-state transactions**: CGST (9%) + SGST (9%) when seller and customer are in the same state
- **Inter-state transactions**: IGST (18%) when seller and customer are in different states
- **Mock order management** with in-memory storage
- **Comprehensive API endpoints** for testing and integration
- **Full test coverage** with pytest

## Architecture

### Module Structure

```
backend/app/
├── orders/
│   ├── __init__.py
│   ├── models.py          # Order and Invoice domain models
│   ├── schemas.py         # Pydantic validation schemas
│   ├── repository.py      # In-memory data storage
│   └── service.py         # GST calculation logic
├── api/routes/
│   └── orders.py          # REST API endpoints
├── core/
│   └── config.py          # GST settings (SELLER_GSTIN, etc.)
└── tests/
    ├── test_gst_invoice.py     # Unit tests
    └── test_gst_invoice_api.py # Integration tests
```

## Configuration

GST settings are defined in `app/core/config.py`:

```python
# GST Settings for India e-commerce
SELLER_GSTIN: str = "29ABCDE1234F1Z5"  # Karnataka GSTIN
SELLER_NAME: str = "Example E-commerce Pvt Ltd"
SELLER_ADDRESS: str = "123, Brigade Road, Bangalore, Karnataka - 560001"
SELLER_STATE_CODE: str  # Auto-computed from GSTIN (first 2 digits)
```

## API Endpoints

All endpoints are under `/api/v1/mock/orders` (available in local environment only).

### 1. Create Order

**POST** `/api/v1/mock/orders/`

Create a new order with customer and item details.

**Request Body:**
```json
{
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
```

**Response (201):**
```json
{
  "order_id": 1,
  "customer_name": "John Doe",
  "customer_gstin": "29ABCDE1234F1Z5",
  "customer_address": "123 MG Road, Bangalore, Karnataka - 560001",
  "items": [
    {
      "product_name": "Laptop",
      "quantity": 1,
      "unit_price": 50000.0,
      "hsn_code": "84713000",
      "total_amount": 50000.0
    },
    {
      "product_name": "Mouse",
      "quantity": 2,
      "unit_price": 500.0,
      "hsn_code": "84716060",
      "total_amount": 1000.0
    }
  ],
  "subtotal": 51000.0,
  "order_date": "2025-09-30T12:46:32.123456"
}
```

### 2. Generate GST Invoice

**POST** `/api/v1/mock/orders/{order_id}/generate-invoice`

Generate a GST-compliant invoice for an existing order.

**Request Body:**
```json
{
  "customer_gstin": "29XYZPQ5678G2A1"
}
```

**Response (200):**
```json
{
  "invoice_number": "INV-1-20250930124632",
  "invoice_date": "2025-09-30T12:46:32.123456",
  "seller_gstin": "29ABCDE1234F1Z5",
  "seller_name": "Example E-commerce Pvt Ltd",
  "seller_address": "123, Brigade Road, Bangalore, Karnataka - 560001",
  "seller_state_code": "29",
  "customer_name": "John Doe",
  "customer_gstin": "29XYZPQ5678G2A1",
  "customer_address": "123 MG Road, Bangalore, Karnataka - 560001",
  "customer_state_code": "29",
  "order_id": 1,
  "order_date": "2025-09-30T12:46:32.123456",
  "items": [...],
  "subtotal": 51000.0,
  "cgst_rate": 9.0,
  "cgst_amount": 4590.0,
  "sgst_rate": 9.0,
  "sgst_amount": 4590.0,
  "igst_rate": 0.0,
  "igst_amount": 0.0,
  "total_tax": 9180.0,
  "grand_total": 60180.0,
  "is_intra_state": true
}
```

### 3. Get Order

**GET** `/api/v1/mock/orders/{order_id}`

Retrieve details of a specific order.

### 4. List Orders

**GET** `/api/v1/mock/orders/`

Get all orders in the system.

## GST Calculation Logic

### State Code Extraction
State codes are extracted from GSTIN (first 2 digits):
- **29**: Karnataka
- **27**: Maharashtra  
- **06**: Delhi
- **33**: Tamil Nadu
- etc.

### Tax Calculation Rules

#### Intra-State Transaction (Same State)
When `seller_state_code == customer_state_code`:
- **CGST**: 9% (Central GST)
- **SGST**: 9% (State GST)
- **IGST**: 0%
- **Total Tax**: 18%

Example: Seller in Karnataka (29) → Customer in Karnataka (29)

#### Inter-State Transaction (Different States)
When `seller_state_code != customer_state_code`:
- **CGST**: 0%
- **SGST**: 0%
- **IGST**: 18% (Integrated GST)
- **Total Tax**: 18%

Example: Seller in Karnataka (29) → Customer in Maharashtra (27)

### Formula
```
Subtotal = Sum of (quantity × unit_price) for all items
CGST Amount = (Subtotal × CGST Rate) / 100
SGST Amount = (Subtotal × SGST Rate) / 100
IGST Amount = (Subtotal × IGST Rate) / 100
Total Tax = CGST Amount + SGST Amount + IGST Amount
Grand Total = Subtotal + Total Tax
```

All amounts are rounded to 2 decimal places.

## GSTIN Validation

GSTIN (Goods and Services Tax Identification Number) must:
- Be exactly **15 characters** long
- Start with **2-digit state code** (must be numeric)
- Follow format: `[State Code (2)][PAN (10)][Entity Code (1)][Check Digit (1)][Letter/Digit (1)]`

Example valid GSTIN: `29ABCDE1234F1Z5`

## Testing

### Run Unit Tests
```bash
# Inside Docker container
docker compose exec backend bash scripts/tests-start.sh app/tests/test_gst_invoice.py -v

# Or with uv locally
uv run pytest app/tests/test_gst_invoice.py -v
```

### Run Integration Tests
```bash
docker compose exec backend bash scripts/tests-start.sh app/tests/test_gst_invoice_api.py -v
```

### Run All GST Tests
```bash
docker compose exec backend bash scripts/tests-start.sh app/tests/test_gst_invoice*.py -v
```

## Test Coverage

The test suite includes:

### Unit Tests (`test_gst_invoice.py`)
1. **State Code Extraction**: Valid/invalid GSTIN formats
2. **GST Rate Calculation**: Intra-state vs inter-state
3. **Invoice Generation**: 
   - Intra-state with CGST+SGST
   - Inter-state with IGST
   - Invalid order IDs
   - Invalid GSTIN formats
4. **Tax Calculation Accuracy**: Rounding, multiple items
5. **Edge Cases**: Single items, case sensitivity, various state codes

### Integration Tests (`test_gst_invoice_api.py`)
1. **Order API**: Create, retrieve, list orders
2. **Invoice Generation API**: 
   - Full request/response flow
   - Error handling
   - Complex scenarios with multiple items
3. **Response Structure Validation**

## Usage Examples

### Example 1: Intra-State Transaction (Karnataka → Karnataka)

```python
# 1. Create order
order_response = client.post("/api/v1/mock/orders/", json={
    "customer_name": "Acme Corp",
    "customer_gstin": "29ABCDE1234F1Z5",
    "customer_address": "Bangalore, Karnataka",
    "items": [{"product_name": "Laptop", "quantity": 1, "unit_price": 50000.0}]
})
order_id = order_response.json()["order_id"]

# 2. Generate invoice
invoice_response = client.post(
    f"/api/v1/mock/orders/{order_id}/generate-invoice",
    json={"customer_gstin": "29XYZPQ5678G2A1"}  # Same state (29)
)

# Result: CGST=4500, SGST=4500, IGST=0, Total Tax=9000, Grand Total=59000
```

### Example 2: Inter-State Transaction (Karnataka → Maharashtra)

```python
# 1. Create order (same as above)

# 2. Generate invoice with different state
invoice_response = client.post(
    f"/api/v1/mock/orders/{order_id}/generate-invoice",
    json={"customer_gstin": "27XYZPQ5678G2A1"}  # Different state (27)
)

# Result: CGST=0, SGST=0, IGST=9000, Total Tax=9000, Grand Total=59000
```

## Indian State Codes Reference

| Code | State/UT |
|------|----------|
| 01 | Jammu and Kashmir |
| 02 | Himachal Pradesh |
| 03 | Punjab |
| 04 | Chandigarh |
| 05 | Uttarakhand |
| 06 | Haryana / Delhi |
| 07 | Delhi |
| 08 | Rajasthan |
| 09 | Uttar Pradesh |
| 10 | Bihar |
| 19 | West Bengal |
| 27 | Maharashtra |
| 29 | Karnataka |
| 32 | Kerala |
| 33 | Tamil Nadu |
| 36 | Telangana |

## Limitations & Future Enhancements

### Current Limitations
- **In-memory storage**: Orders are lost on server restart
- **Fixed GST rate**: All products use 18% GST rate
- **Mock implementation**: Not connected to real database

### Potential Enhancements
1. **Database persistence**: Store orders in PostgreSQL
2. **Product-specific rates**: Support 5%, 12%, 18%, 28% GST rates based on HSN codes
3. **Cess calculation**: Add cess for specific products
4. **TDS/TCS**: Add tax deduction/collection at source
5. **PDF generation**: Create printable invoice PDFs
6. **GST filing integration**: Export data for GSTR-1 filing
7. **E-way bill**: Generate e-way bills for logistics
8. **Invoice numbering**: Implement sequential invoice numbering with fiscal year

## Security Considerations

- **GSTIN validation**: Always validate GSTIN format before processing
- **Input sanitization**: All inputs are validated via Pydantic schemas
- **API access**: Currently limited to local environment only
- **Production readiness**: Add authentication/authorization before production use

## Support

For issues or questions about the GST invoice feature:
1. Check test files for usage examples
2. Review API documentation at `/docs` when server is running
3. Examine service logic in `app/orders/service.py`

---

**Note**: This is a mock implementation for development and testing. For production use, ensure compliance with latest GST regulations and integrate with certified accounting systems.
