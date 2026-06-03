"""Checkout calculation service.

Handles GST, delivery fee, and final bill calculations for orders.
"""

GST_RATE = 0.05  # 5% GST on food items
DELIVERY_FEE_STANDARD = 40.0  # ₹40 standard delivery
DELIVERY_FEE_FREE_THRESHOLD = 500.0  # Free delivery above ₹500


def calculate_subtotal(items_price_data: list[dict]) -> float:
    """Calculate subtotal from a list of {price, quantity} dicts."""
    return round(sum(item["price"] * item["quantity"] for item in items_price_data), 2)


def calculate_gst(subtotal: float) -> float:
    """Calculate GST amount based on subtotal."""
    return round(subtotal * GST_RATE, 2)


def calculate_delivery_fee(subtotal: float) -> float:
    """Calculate delivery fee. Free above threshold."""
    if subtotal >= DELIVERY_FEE_FREE_THRESHOLD:
        return 0.0
    return DELIVERY_FEE_STANDARD


def calculate_total(subtotal: float, gst: float, delivery_fee: float) -> float:
    """Calculate final total amount."""
    return round(subtotal + gst + delivery_fee, 2)


def calculate_checkout(items_price_data: list[dict]) -> dict:
    """Perform full checkout calculation.

    Args:
        items_price_data: List of dicts with 'price' and 'quantity' keys.

    Returns:
        Dict with subtotal, gst, delivery_fee, total_amount.
    """
    subtotal = calculate_subtotal(items_price_data)
    gst = calculate_gst(subtotal)
    delivery_fee = calculate_delivery_fee(subtotal)
    total = calculate_total(subtotal, gst, delivery_fee)

    return {
        "subtotal": subtotal,
        "gst": gst,
        "delivery_fee": delivery_fee,
        "total_amount": total,
    }
