from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import List

from app.core.config import settings
from .models import OrderItem
from .repository import order_repo
from .schemas import InvoiceItemOut, InvoiceOut
from .state_codes import is_valid_state_code

Q2 = Decimal("0.01")


def _quantize(v: Decimal) -> Decimal:
    return v.quantize(Q2, rounding=ROUND_HALF_UP)


def _get_state_code_from_gstin(gstin: str) -> str:
    if not gstin or len(gstin) < 2:
        raise ValueError("Invalid GSTIN")
    code = gstin[:2]
    if not is_valid_state_code(code):
        raise ValueError("Invalid GSTIN state code")
    return code


def _compute_item_taxes(item: OrderItem, supply_type: str) -> tuple[Decimal, Decimal, Decimal]:
    # Returns (cgst_amount, sgst_amount, igst_amount)
    taxable = item.taxable_value
    rate = (item.gst_rate or Decimal("0")) / Decimal("100")
    tax_total = taxable * rate
    if supply_type == "intra":
        half = _quantize(tax_total / Decimal("2"))
        return (half, half, Decimal("0.00"))
    else:
        return (Decimal("0.00"), Decimal("0.00"), _quantize(tax_total))


def generate_gst_invoice(order_id: int, customer_gstin: str) -> InvoiceOut:
    order = order_repo.get(order_id)
    if not order:
        raise ValueError("Order not found")

    try:
        customer_state_code = _get_state_code_from_gstin(customer_gstin)
    except ValueError as e:
        raise ValueError(str(e))

    seller_gstin = settings.SELLER_GSTIN
    seller_state_code = settings.SELLER_STATE_CODE

    supply_type = (
        "intra" if customer_state_code == seller_state_code else "inter"
    )

    items_out: List[InvoiceItemOut] = []
    total_taxable_value = Decimal("0.00")
    total_cgst = Decimal("0.00")
    total_sgst = Decimal("0.00")
    total_igst = Decimal("0.00")

    for it in order.items:
        taxable = _quantize(it.taxable_value)
        cgst, sgst, igst = _compute_item_taxes(it, supply_type)
        line_total = _quantize(taxable + cgst + sgst + igst)

        items_out.append(
            InvoiceItemOut(
                sku=it.sku,
                description=it.description,
                quantity=it.quantity,
                unit_price=_quantize(it.unit_price),
                gst_rate=_quantize(it.gst_rate),
                taxable_value=taxable,
                cgst_amount=cgst,
                sgst_amount=sgst,
                igst_amount=igst,
                total_with_tax=line_total,
            )
        )

        total_taxable_value += taxable
        total_cgst += cgst
        total_sgst += sgst
        total_igst += igst

    total_taxable_value = _quantize(total_taxable_value)
    total_cgst = _quantize(total_cgst)
    total_sgst = _quantize(total_sgst)
    total_igst = _quantize(total_igst)

    grand_total = _quantize(
        total_taxable_value + total_cgst + total_sgst + total_igst
    )

    return InvoiceOut(
        order_id=order_id,
        seller_gstin=seller_gstin,
        seller_state_code=seller_state_code,
        customer_gstin=customer_gstin,
        customer_state_code=customer_state_code,
        supply_type=supply_type,
        items=items_out,
        total_taxable_value=total_taxable_value,
        total_cgst=total_cgst,
        total_sgst=total_sgst,
        total_igst=total_igst,
        grand_total=grand_total,
    )
