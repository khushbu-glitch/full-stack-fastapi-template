from .repository import order_repository
from .schemas import Invoice
from app.core.config import settings

# State codes for GSTIN
GSTIN_STATE_CODES = {
    "35": "Andaman and Nicobar Islands",
    "37": "Andhra Pradesh",
    "12": "Arunachal Pradesh",
    "18": "Assam",
    "10": "Bihar",
    "04": "Chandigarh",
    "22": "Chhattisgarh",
    "26": "Dadra and Nagar Haveli and Daman and Diu",
    "07": "Delhi",
    "30": "Goa",
    "24": "Gujarat",
    "06": "Haryana",
    "02": "Himachal Pradesh",
    "01": "Jammu and Kashmir",
    "20": "Jharkhand",
    "29": "Karnataka",
    "32": "Kerala",
    "38": "Ladakh",
    "31": "Lakshadweep",
    "23": "Madhya Pradesh",
    "27": "Maharashtra",
    "14": "Manipur",
    "17": "Meghalaya",
    "15": "Mizoram",
    "13": "Nagaland",
    "21": "Odisha",
    "34": "Puducherry",
    "03": "Punjab",
    "08": "Rajasthan",
    "11": "Sikkim",
    "33": "Tamil Nadu",
    "36": "Telangana",
    "16": "Tripura",
    "09": "Uttar Pradesh",
    "05": "Uttarakhand",
    "19": "West Bengal"
}

def get_state_code_from_gstin(gstin: str) -> str:
    return gstin[:2]

def generate_gst_invoice(order_id: int, customer_gstin: str) -> Invoice:
    order = order_repository.get_order(order_id)
    if not order:
        raise ValueError("Order not found")

    seller_state_code = get_state_code_from_gstin(settings.SELLER_GSTIN)
    customer_state_code = get_state_code_from_gstin(customer_gstin)

    subtotal = order.amount
    cgst = 0.0
    sgst = 0.0
    igst = 0.0

    if seller_state_code == customer_state_code:
        # Intra-state transaction
        cgst = round(subtotal * 0.09, 2)
        sgst = round(subtotal * 0.09, 2)
    else:
        # Inter-state transaction
        igst = round(subtotal * 0.18, 2)

    total = subtotal + cgst + sgst + igst

    return Invoice(
        order_id=order.id,
        customer_gstin=customer_gstin,
        seller_gstin=settings.SELLER_GSTIN,
        subtotal=subtotal,
        cgst=cgst,
        sgst=sgst,
        igst=igst,
        total=total,
    )
