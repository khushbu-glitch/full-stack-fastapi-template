# GST Invoice System Architecture

## 🏗️ System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT (API Consumer)                    │
│                    (Browser / Postman / cURL)                    │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTP Request
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                       │
│                      (app/main.py + routers)                     │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Routes Layer                            │
│                   (app/api/routes/orders.py)                     │
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ POST /orders/   │  │ POST /generate  │  │ GET /orders/    │ │
│  │ Create Order    │  │ Generate Invoice│  │ List Orders     │ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │
│           │                    │                     │           │
└───────────┼────────────────────┼─────────────────────┼───────────┘
            │                    │                     │
            ▼                    ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Pydantic Schemas Layer                        │
│                     (app/orders/schemas.py)                      │
│                                                                   │
│  ┌────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │ OrderCreate    │  │ GSTInvoiceRequest│  │ OrderResponse  │  │
│  │ - Validation   │  │ - GSTIN Validate │  │ - Serializer   │  │
│  └────────┬───────┘  └──────────┬───────┘  └────────┬───────┘  │
└───────────┼────────────────────┼─────────────────────┼───────────┘
            │                    │                     │
            ▼                    ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Business Logic Layer                        │
│                      (app/orders/service.py)                     │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │         generate_gst_invoice(order_id, gstin)           │    │
│  │                                                           │    │
│  │  1. Validate GSTIN format                                │    │
│  │  2. Retrieve order from repository                       │    │
│  │  3. Extract seller/customer state codes                  │    │
│  │  4. Calculate GST rates (CGST/SGST or IGST)             │    │
│  │  5. Calculate tax amounts                                │    │
│  │  6. Generate invoice number                              │    │
│  │  7. Create GSTInvoice object                             │    │
│  │  8. Return invoice                                        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌──────────────────────┐  ┌──────────────────────┐            │
│  │ extract_state_code() │  │ calculate_gst_rates()│            │
│  └──────────────────────┘  └──────────────────────┘            │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Data Access Layer                          │
│                   (app/orders/repository.py)                     │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │            OrderRepository (In-Memory)                   │    │
│  │                                                           │    │
│  │  - create(order)      : Save new order                   │    │
│  │  - get_by_id(id)      : Retrieve order                   │    │
│  │  - get_all()          : List all orders                  │    │
│  │  - delete(id)         : Remove order                     │    │
│  │                                                           │    │
│  │  Storage: Dictionary {order_id: Order}                   │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Domain Models                            │
│                      (app/orders/models.py)                      │
│                                                                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ OrderItem   │    │   Order     │    │ GSTInvoice  │         │
│  ├─────────────┤    ├─────────────┤    ├─────────────┤         │
│  │ name        │◄───│ items[]     │◄───│ order       │         │
│  │ quantity    │    │ customer    │    │ seller      │         │
│  │ price       │    │ gstin       │    │ cgst        │         │
│  │ hsn_code    │    │ address     │    │ sgst        │         │
│  │ total()     │    │ subtotal()  │    │ igst        │         │
│  └─────────────┘    └─────────────┘    │ grand_total │         │
│                                         └─────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Request Flow: Create Order

```
1. Client → POST /api/v1/mock/orders/
   {
     "customer_name": "ABC Corp",
     "customer_gstin": "29ABCDE1234F1Z5",
     "items": [...]
   }

2. API Route (orders.py)
   ├─ Receives request
   └─ Validates via OrderCreate schema

3. Pydantic Schema (schemas.py)
   ├─ Validates GSTIN format (15 chars, numeric prefix)
   ├─ Validates item quantities (> 0)
   ├─ Validates prices (> 0)
   └─ Converts to uppercase

4. Create Domain Objects (models.py)
   ├─ OrderItem objects for each item
   └─ Order object with all items

5. Repository (repository.py)
   ├─ Assigns order_id
   ├─ Stores in memory
   └─ Returns saved order

6. API Route
   ├─ Converts to OrderResponse schema
   └─ Returns JSON (201 Created)

7. Client ← Response
   {
     "order_id": 1,
     "subtotal": 51000.0,
     ...
   }
```

---

## 🔄 Request Flow: Generate Invoice

```
1. Client → POST /api/v1/mock/orders/1/generate-invoice
   {
     "customer_gstin": "27XYZPQ5678G2A1"
   }

2. API Route (orders.py)
   ├─ Extracts order_id from path
   └─ Validates via GSTInvoiceRequest schema

3. Service Layer (service.py)
   │
   ├─ generate_gst_invoice(1, "27XYZPQ5678G2A1")
   │
   ├─ [Step 1] Validate GSTIN
   │   ├─ Length check (15 chars)
   │   └─ Format check (numeric prefix)
   │
   ├─ [Step 2] Retrieve order
   │   └─ repository.get_by_id(1)
   │
   ├─ [Step 3] Extract state codes
   │   ├─ Seller: "29" (Karnataka)
   │   └─ Customer: "27" (Maharashtra)
   │
   ├─ [Step 4] Calculate GST rates
   │   ├─ Compare state codes: 29 ≠ 27
   │   └─ Inter-state → IGST 18%
   │
   ├─ [Step 5] Calculate amounts
   │   ├─ Subtotal: ₹51,000
   │   ├─ CGST: ₹0 (0%)
   │   ├─ SGST: ₹0 (0%)
   │   ├─ IGST: ₹9,180 (18%)
   │   ├─ Total Tax: ₹9,180
   │   └─ Grand Total: ₹60,180
   │
   ├─ [Step 6] Generate invoice number
   │   └─ "INV-1-20250930124632"
   │
   └─ [Step 7] Create GSTInvoice object

4. API Route
   ├─ Converts to GSTInvoiceResponse schema
   └─ Returns JSON (200 OK)

5. Client ← Response
   {
     "invoice_number": "INV-1-...",
     "cgst_amount": 0.0,
     "sgst_amount": 0.0,
     "igst_amount": 9180.0,
     "grand_total": 60180.0,
     "is_intra_state": false
   }
```

---

## 🧮 GST Calculation Decision Tree

```
                    ┌─────────────────────┐
                    │  Order + GSTIN      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Extract State Codes │
                    │ - Seller: GSTIN[:2] │
                    │ - Customer: GSTIN[:2]│
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Compare State Codes │
                    └──────────┬──────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
                ▼                             ▼
    ┌────────────────────┐      ┌────────────────────┐
    │ Same State         │      │ Different States   │
    │ (Intra-State)      │      │ (Inter-State)      │
    └──────┬─────────────┘      └──────┬─────────────┘
           │                           │
           ▼                           ▼
    ┌────────────────────┐      ┌────────────────────┐
    │ Apply Rates:       │      │ Apply Rate:        │
    │ - CGST: 9%         │      │ - IGST: 18%        │
    │ - SGST: 9%         │      │ - CGST: 0%         │
    │ - IGST: 0%         │      │ - SGST: 0%         │
    └──────┬─────────────┘      └──────┬─────────────┘
           │                           │
           └───────────┬───────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │ Calculate Amounts    │
            │ Amount = (Subtotal × │
            │          Rate) / 100 │
            └──────────┬───────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │ Total Tax = CGST +   │
            │            SGST +    │
            │            IGST      │
            └──────────┬───────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │ Grand Total =        │
            │ Subtotal + Tax       │
            └──────────────────────┘
```

---

## 📊 Data Flow Diagram

```
┌──────────────┐
│   Client     │
└──────┬───────┘
       │ 1. Create Order Request
       │
       ▼
┌──────────────────────┐
│  API Route Layer     │──────► Validate via Pydantic
└──────┬───────────────┘
       │ 2. Valid Order Data
       │
       ▼
┌──────────────────────┐
│  Domain Models       │──────► Create Order & Items
└──────┬───────────────┘
       │ 3. Order Object
       │
       ▼
┌──────────────────────┐
│  Repository          │──────► Store in Memory
└──────┬───────────────┘
       │ 4. Saved Order
       │
       ▼
┌──────────────────────┐
│  API Response        │──────► Serialize to JSON
└──────┬───────────────┘
       │ 5. Order Response
       │
       ▼
┌──────────────┐
│   Client     │
└──────────────┘

       │ 6. Generate Invoice Request
       │
       ▼
┌──────────────────────┐
│  Service Layer       │
│                      │
│  ┌───────────────┐   │
│  │1. Validate    │   │──────► Check GSTIN
│  └───────┬───────┘   │
│          │           │
│  ┌───────▼───────┐   │
│  │2. Get Order   │   │──────► From Repository
│  └───────┬───────┘   │
│          │           │
│  ┌───────▼───────┐   │
│  │3. Extract     │   │──────► State Codes
│  │   States      │   │
│  └───────┬───────┘   │
│          │           │
│  ┌───────▼───────┐   │
│  │4. Calculate   │   │──────► GST Rates
│  │   Rates       │   │
│  └───────┬───────┘   │
│          │           │
│  ┌───────▼───────┐   │
│  │5. Calculate   │   │──────► Tax Amounts
│  │   Amounts     │   │
│  └───────┬───────┘   │
│          │           │
│  ┌───────▼───────┐   │
│  │6. Create      │   │──────► Invoice Object
│  │   Invoice     │   │
│  └───────────────┘   │
└──────┬───────────────┘
       │ 7. GST Invoice
       │
       ▼
┌──────────────────────┐
│  API Response        │──────► Serialize to JSON
└──────┬───────────────┘
       │ 8. Invoice Response
       │
       ▼
┌──────────────┐
│   Client     │
└──────────────┘
```

---

## 🗂️ Directory Structure

```
backend/
├── app/
│   ├── orders/                   # GST Invoice Module
│   │   ├── __init__.py
│   │   ├── models.py             # Domain Models
│   │   │   ├── class OrderItem
│   │   │   ├── class Order
│   │   │   └── class GSTInvoice
│   │   │
│   │   ├── schemas.py            # Pydantic Schemas
│   │   │   ├── OrderItemCreate
│   │   │   ├── OrderCreate
│   │   │   ├── OrderResponse
│   │   │   ├── GSTInvoiceRequest
│   │   │   └── GSTInvoiceResponse
│   │   │
│   │   ├── repository.py         # Data Access
│   │   │   └── class OrderRepository
│   │   │
│   │   └── service.py            # Business Logic
│   │       ├── generate_gst_invoice()
│   │       ├── calculate_gst_rates()
│   │       └── extract_state_code()
│   │
│   ├── api/
│   │   ├── main.py               # Router Registration
│   │   └── routes/
│   │       └── orders.py         # API Endpoints
│   │           ├── POST /orders/
│   │           ├── GET  /orders/
│   │           ├── GET  /orders/{id}
│   │           └── POST /orders/{id}/generate-invoice
│   │
│   ├── core/
│   │   └── config.py             # GST Configuration
│   │       ├── SELLER_GSTIN
│   │       ├── SELLER_NAME
│   │       ├── SELLER_ADDRESS
│   │       └── SELLER_STATE_CODE
│   │
│   └── tests/
│       ├── test_gst_invoice.py     # Unit Tests
│       └── test_gst_invoice_api.py # Integration Tests
│
├── GST_INVOICE_README.md         # Full Documentation
├── GST_FEATURE_SUMMARY.md        # Implementation Summary
├── GST_QUICK_REFERENCE.md        # Quick Reference
├── GST_ARCHITECTURE.md           # This File
└── example_gst_usage.py          # Usage Examples
```

---

## 🔐 Security & Validation Flow

```
┌─────────────┐
│ Raw Request │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────┐
│ FastAPI Input Validation         │
│ - Content-Type check             │
│ - JSON parsing                   │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ Pydantic Schema Validation       │
│ ✓ Field types                    │
│ ✓ Required fields                │
│ ✓ Min/Max lengths                │
│ ✓ Custom validators              │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ GSTIN Validation                 │
│ ✓ Length = 15                    │
│ ✓ First 2 chars numeric          │
│ ✓ Uppercase conversion           │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ Business Logic Validation        │
│ ✓ Order exists                   │
│ ✓ Valid state codes              │
│ ✓ Calculation accuracy           │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ Success Response                 │
│ OR                               │
│ HTTP Error (400/404/422)         │
└──────────────────────────────────┘
```

---

## 📈 Scaling Considerations

### Current (Development)
```
┌──────────────┐
│   FastAPI    │ ──► In-Memory Store
└──────────────┘      (Dictionary)
```

### Production Ready
```
┌──────────────┐
│   FastAPI    │
│   (Uvicorn)  │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│ PostgreSQL Database  │
│ - Orders Table       │
│ - Invoices Table     │
│ - Items Table        │
└──────────────────────┘
```

### High Availability
```
┌─────────────────────────────────┐
│   Load Balancer (NGINX)         │
└──────────┬──────────────────────┘
           │
    ┌──────┴──────┬─────────┐
    │             │         │
    ▼             ▼         ▼
┌────────┐  ┌────────┐  ┌────────┐
│FastAPI │  │FastAPI │  │FastAPI │
│Instance│  │Instance│  │Instance│
└───┬────┘  └───┬────┘  └───┬────┘
    │           │           │
    └───────────┴───────────┘
                │
                ▼
    ┌───────────────────────┐
    │ PostgreSQL Cluster    │
    │ - Master (Write)      │
    │ - Replica (Read)      │
    └───────────────────────┘
                │
                ▼
    ┌───────────────────────┐
    │ Redis Cache           │
    │ - Order lookups       │
    │ - GSTIN validation    │
    └───────────────────────┘
```

---

## 🧪 Test Architecture

```
┌─────────────────────────────────────────┐
│           Test Suite                    │
└─────────────┬───────────────────────────┘
              │
      ┌───────┴────────┐
      │                │
      ▼                ▼
┌───────────┐    ┌──────────────┐
│Unit Tests │    │ API Tests    │
└─────┬─────┘    └──────┬───────┘
      │                 │
      │                 │
      ▼                 ▼
┌─────────────────────────────────┐
│ Test Classes                    │
├─────────────────────────────────┤
│ • TestStateCodeExtraction       │
│ • TestGSTRateCalculation        │
│ • TestGSTInvoiceGeneration      │
│ • TestTaxCalculationAccuracy    │
│ • TestEdgeCases                 │
│ • TestOrderAPI                  │
│ • TestInvoiceGenerationAPI      │
│ • TestComplexScenarios          │
└─────────────────────────────────┘
```

---

## 🎯 Design Patterns Used

### 1. Repository Pattern
```
Service ──► Repository ──► Data Store
  (Business Logic)  (Data Access)  (Storage)
```

### 2. Service Layer Pattern
```
API ──► Service ──► Repository
  (HTTP)  (Logic)  (Data)
```

### 3. DTO Pattern (Pydantic Schemas)
```
Request ──► Schema ──► Model ──► Schema ──► Response
          (Validate)  (Process) (Serialize)
```

---

**Last Updated:** 2025-09-30  
**Version:** 1.0.0
