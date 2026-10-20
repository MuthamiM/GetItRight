import re
from typing import Optional


def normalize_email(value: Optional[str]) -> str:
    return (value or "").strip().casefold()


def normalize_phone(value: Optional[str]) -> Optional[str]:
    """Return a punctuation-free phone identity, canonicalizing Kenyan local numbers."""
    digits = "".join(re.findall(r"[0-9]", value or ""))
    if digits.startswith("00"):
        digits = digits[2:]
    if len(digits) == 10 and digits.startswith("0"):
        digits = "254" + digits[1:]
    elif len(digits) == 9 and digits.startswith(("1", "7")):
        digits = "254" + digits
    if not 7 <= len(digits) <= 15:
        return None
    return digits or None
