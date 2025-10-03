import re
import base58
import hashlib
from decimal import Decimal, ROUND_DOWN


AMOUNT_QUANT = Decimal("0.01")


def parse_decimal(value_str: str) -> Decimal:
    normalized = value_str.replace(",", ".").strip()
    return Decimal(normalized)


def format_money(amount: Decimal) -> str:
    quantized = amount.quantize(AMOUNT_QUANT, rounding=ROUND_DOWN)
    return f"{quantized.normalize()} USDT"


def is_valid_tron_address(address: str) -> bool:
    if not address or not address.startswith("T"):
        return False
    try:
        decoded = base58.b58decode(address)
    except Exception:
        return False
    if len(decoded) != 25:
        return False
    payload = decoded[:-4]
    checksum = decoded[-4:]
    double_hash = hashlib.sha256(hashlib.sha256(payload).digest()).digest()
    return checksum == double_hash[:4]


def sanitize_label(label: str) -> str:
    # Allow letters, numbers, spaces, dashes and underscores
    label = label.strip()
    return re.sub(r"[^\w\-\s]", "", label)[:64]

