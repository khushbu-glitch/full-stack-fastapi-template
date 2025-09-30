# GST Invoice - Quick Reference Card

## 🚀 API Endpoints

### Base URL (Local)
```
http://localhost:8000/api/v1/mock/orders
```

### 1. Create Order
```http
POST /api/v1/mock/orders/
Content-Type: application/json

{
  "customer_name": "string",
  "customer_gstin": "string (15 chars)",
  "customer_address": "string",
  "items": [
    {
      "product_name": "string",
      "quantity": integer (>0),
      "unit_price": float (>0),
      "hsn_code": "string (4-8 chars, default: 00000000)"
    }
  ]
}

Response: 201 Created
{
  "order_id": integer,
  "customer_name": "string",
  "customer_gstin": "string",
  "customer_address": "string",
  "items": [...],
  "subtotal": float,
  "order_date": "datetime"
}
```

### 2. Generate Invoice
```http
POST /api/v1/mock/orders/{order_id}/generate-invoice
Content-Type: application/json

{
  "customer_gstin": "string (15 chars)"
}

Response: 200 OK
{
  "invoice_number": "string",
  "invoice_date": "datetime",
  "seller_gstin": "string",
  "seller_name": "string",
  "seller_address": "string",
  "seller_state_code": "string",
  "customer_name": "string",
  "customer_gstin": "string",
  "customer_address": "string",
  "customer_state_code": "string",
  "order_id": integer,
  "order_date": "datetime",
  "items": [...],
  "subtotal": float,
  "cgst_rate": float,
  "cgst_amount": float,
  "sgst_rate": float,
  "sgst_amount": float,
  "igst_rate": float,
  "igst_amount": float,
  "total_tax": float,
  "grand_total": float,
  "is_intra_state": boolean
}
```

### 3. Get Order
```http
GET /api/v1/mock/orders/{order_id}

Response: 200 OK (same as create response)
```

### 4. List Orders
```http
GET /api/v1/mock/orders/

Response: 200 OK
[
  { order object },
  { order object },
  ...
]
```

---

## 📐 GST Calculation Rules

### Intra-State (Same State)
```
seller_state_code == customer_state_code

CGST = 9%
SGST = 9%
IGST = 0%
Total = 18%
```

### Inter-State (Different States)
```
seller_state_code != customer_state_code

CGST = 0%
SGST = 0%
IGST = 18%
Total = 18%
```

### Formula
```python
subtotal = sum(item.quantity * item.unit_price for item in items)
cgst_amount = round((subtotal * cgst_rate) / 100, 2)
sgst_amount = round((subtotal * sgst_rate) / 100, 2)
igst_amount = round((subtotal * igst_rate) / 100, 2)
total_tax = cgst_amount + sgst_amount + igst_amount
grand_total = round(subtotal + total_tax, 2)
```

---

## 🔤 GSTIN Format

```
[State][PAN      ][E][C][S]
 29    ABCDE1234F 1  Z  5

State (2): Numeric state code (01-36)
PAN (10):  10-character PAN
E (1):     Entity code
C (1):     Check digit
S (1):     Suffix
```

### Common State Codes
| Code | State        | Code | State        |
|------|--------------|------|--------------|
| 01   | J&K          | 19   | West Bengal  |
| 06   | Haryana      | 27   | Maharashtra  |
| 07   | Delhi        | 29   | Karnataka    |
| 09   | UP           | 32   | Kerala       |
| 10   | Bihar        | 33   | Tamil Nadu   |

---

## 💻 Code Examples

### Python (Direct Service Call)
```python
from app.orders.service import generate_gst_invoice

# Generate invoice
invoice = generate_gst_invoice(
    order_id=1,
    customer_gstin="29XYZPQ5678G2A1"
)

print(f"Total: ₹{invoice.grand_total}")
print(f"CGST: ₹{invoice.cgst_amount}")
print(f"SGST: ₹{invoice.sgst_amount}")
print(f"IGST: ₹{invoice.igst_amount}")
```

### Python (HTTP Client)
```python
import requests

# Create order
response = requests.post(
    "http://localhost:8000/api/v1/mock/orders/",
    json={
        "customer_name": "ABC Corp",
        "customer_gstin": "29ABCDE1234F1Z5",
        "customer_address": "Bangalore",
        "items": [
            {
                "product_name": "Laptop",
                "quantity": 1,
                "unit_price": 50000.0,
                "hsn_code": "84713000"
            }
        ]
    }
)
order_id = response.json()["order_id"]

# Generate invoice
invoice_response = requests.post(
    f"http://localhost:8000/api/v1/mock/orders/{order_id}/generate-invoice",
    json={"customer_gstin": "27XYZPQ5678G2A1"}
)
invoice = invoice_response.json()
print(f"Invoice: {invoice['invoice_number']}")
print(f"Total: ₹{invoice['grand_total']}")
```

### cURL
```bash
# Create order
ORDER_ID=$(curl -s -X POST "http://localhost:8000/api/v1/mock/orders/" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test",
    "customer_gstin": "29ABCDE1234F1Z5",
    "customer_address": "Address",
    "items": [{"product_name": "Item", "quantity": 1, "unit_price": 1000.0}]
  }' | jq -r '.order_id')

# Generate invoice (intra-state)
curl -X POST "http://localhost:8000/api/v1/mock/orders/$ORDER_ID/generate-invoice" \
  -H "Content-Type: application/json" \
  -d '{"customer_gstin": "29XYZPQ5678G2A1"}' | jq

# Generate invoice (inter-state)
curl -X POST "http://localhost:8000/api/v1/mock/orders/$ORDER_ID/generate-invoice" \
  -H "Content-Type: application/json" \
  -d '{"customer_gstin": "27XYZPQ5678G2A1"}' | jq
```

---

## 🧪 Testing Commands

### Run All GST Tests
```bash
# In Docker container
docker compose exec backend bash scripts/tests-start.sh app/tests/test_gst_invoice*.py -v

# With uv locally
cd backend
uv run pytest app/tests/test_gst_invoice*.py -v
```

### Run Specific Test Classes
```bash
# Unit tests only
pytest app/tests/test_gst_invoice.py::TestGSTInvoiceGeneration -v

# API tests only
pytest app/tests/test_gst_invoice_api.py::TestInvoiceGenerationAPI -v
```

### Run Example Script
```bash
cd backend
python example_gst_usage.py
```

---

## ⚠️ Error Codes

| Code | Error | Solution |
|------|-------|----------|
| 400 | Invalid GSTIN format | Ensure 15 chars, numeric state code |
| 404 | Order not found | Check order_id exists |
| 422 | Validation error | Check request body format |

---

## 📦 Module Structure

```
app/
├── orders/
│   ├── models.py       # Order, OrderItem, GSTInvoice
│   ├── schemas.py      # OrderCreate, GSTInvoiceResponse
│   ├── repository.py   # OrderRepository (in-memory)
│   └── service.py      # generate_gst_invoice()
├── api/routes/
│   └── orders.py       # API endpoints
└── core/
    └── config.py       # SELLER_GSTIN settings
```

---

## 🎯 Key Functions

### `generate_gst_invoice(order_id, customer_gstin)`
**Purpose:** Generate GST-compliant invoice  
**Location:** `app/orders/service.py`  
**Returns:** `GSTInvoice` object  
**Raises:** HTTPException (400, 404)

### `calculate_gst_rates(seller_state, customer_state)`
**Purpose:** Determine CGST/SGST/IGST rates  
**Location:** `app/orders/service.py`  
**Returns:** `(cgst_rate, sgst_rate, igst_rate)`

### `extract_state_code(gstin)`
**Purpose:** Extract state code from GSTIN  
**Location:** `app/orders/service.py`  
**Returns:** 2-digit state code string

---

## 📊 Configuration

### Current Settings (config.py)
```python
SELLER_GSTIN = "29ABCDE1234F1Z5"  # Karnataka
SELLER_NAME = "Example E-commerce Pvt Ltd"
SELLER_ADDRESS = "123, Brigade Road, Bangalore, Karnataka - 560001"
SELLER_STATE_CODE = "29"  # Auto-computed
```

### Modify Seller Details
Edit `backend/app/core/config.py` or set environment variables:
```bash
export SELLER_GSTIN="27XYZPQ5678G2A1"
export SELLER_NAME="Your Company Name"
export SELLER_ADDRESS="Your Address"
```

---

## 🔍 Debugging Tips

### Check Order Exists
```python
from app.orders.repository import order_repository
order = order_repository.get_by_id(1)
print(order)
```

### Validate GSTIN Manually
```python
from app.orders.service import extract_state_code
state = extract_state_code("29ABCDE1234F1Z5")
print(f"State code: {state}")
```

### View All Orders
```bash
curl http://localhost:8000/api/v1/mock/orders/ | jq
```

---

## 📚 Documentation Links

- **Full Documentation**: `GST_INVOICE_README.md`
- **Implementation Summary**: `GST_FEATURE_SUMMARY.md`
- **API Docs (when running)**: http://localhost:8000/docs
- **Example Code**: `example_gst_usage.py`

---

## ✅ Checklist

Before using in production:
- [ ] Replace in-memory storage with database
- [ ] Add authentication/authorization
- [ ] Implement product-specific GST rates
- [ ] Add invoice PDF generation
- [ ] Configure proper invoice numbering
- [ ] Add audit logging
- [ ] Implement backup strategy
- [ ] Test with real GSTINs
- [ ] Verify compliance with GST Act
- [ ] Add monitoring and alerts

---

**Version:** 1.0.0  
**Last Updated:** 2025-09-30
