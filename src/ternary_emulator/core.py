"""
Balanced Ternary Arithmetic Unit

Implements balanced ternary representation using trits {-1, 0, 1}.
All arithmetic operates directly on trit representations.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Trit constants
NEG = -1
ZERO = 0
POS = 1

TRIT_TO_CHAR = {NEG: "T", ZERO: "0", POS: "1"}
CHAR_TO_TRIT = {"T": NEG, "-": NEG, "0": ZERO, "1": POS}


def int_to_balanced_ternary(value: int, width: int | None = None) -> tuple[int, ...]:
    """Convert an integer to a tuple of trits (MSB first)."""
    if value == 0:
        digits = [ZERO]
    else:
        digits: list[int] = []
        n = value
        while n != 0:
            n, remainder = divmod(n, 3)
            if remainder == 2:
                remainder = NEG
                n += 1
            digits.append(remainder)
        digits.reverse()

    if width is not None:
        while len(digits) < width:
            digits.insert(0, ZERO)
        if len(digits) > width:
            digits = digits[-width:]

    return tuple(digits)


def balanced_ternary_to_int(digits) -> int:
    """Convert trits (MSB first) to an integer."""
    value = 0
    for digit in digits:
        value = value * 3 + digit
    return value


def str_to_trits(text: str) -> list[int]:
    """Parse a balanced ternary string like '1T0T' into a list of trits."""
    text = text.strip().upper()
    if not text:
        raise ValueError("empty balanced ternary string")
    result = []
    for ch in text:
        if ch == "-":
            ch = "T"
        if ch not in CHAR_TO_TRIT:
            raise ValueError(f"invalid trit character: {ch!r}")
        result.append(CHAR_TO_TRIT[ch])
    return result


def trits_to_str(digits) -> str:
    """Convert trits to a string like '1T0T'."""
    return "".join(TRIT_TO_CHAR[d] for d in digits)


def normalize_trits(digits) -> list[int]:
    """Remove leading zeros, keeping at least one trit."""
    result = list(digits)
    while len(result) > 1 and result[0] == ZERO:
        result.pop(0)
    return result


# ── Ternary ALU operations ──────────────────────────────────────────

def ternary_add(a, b, width: int | None = None) -> list[int]:
    """Add two balanced ternary numbers."""
    a = list(a)
    b = list(b)
    max_len = max(len(a), len(b))
    if width:
        max_len = max(max_len, width)
    while len(a) < max_len:
        a.insert(0, ZERO)
    while len(b) < max_len:
        b.insert(0, ZERO)

    result = [ZERO] * max_len
    carry = ZERO

    for i in range(max_len - 1, -1, -1):
        total = a[i] + b[i] + carry
        if total > 1:
            result[i] = total - 3
            carry = POS
        elif total < -1:
            result[i] = total + 3
            carry = NEG
        else:
            result[i] = total
            carry = ZERO

    if carry != ZERO:
        result.insert(0, carry)

    if width:
        while len(result) < width:
            result.insert(0, ZERO)
        if len(result) > width:
            result = result[-width:]

    return normalize_trits(result)


def ternary_negate(a) -> list[int]:
    """Negate a balanced ternary number."""
    return [-t for t in a]


def ternary_sub(a, b, width: int | None = None) -> list[int]:
    """Subtract b from a in balanced ternary."""
    return ternary_add(a, ternary_negate(b), width)


def ternary_multiply(a, b, width: int | None = None) -> list[int]:
    """Multiply two balanced ternary numbers."""
    va = balanced_ternary_to_int(a)
    vb = balanced_ternary_to_int(b)
    result = int_to_balanced_ternary(va * vb, width)
    return list(result)


def ternary_div(a, b, width: int | None = None) -> tuple[list[int], list[int]]:
    """Divide a by b, returning (quotient, remainder)."""
    va = balanced_ternary_to_int(a)
    vb = balanced_ternary_to_int(b)
    if vb == 0:
        raise ZeroDivisionError("ternary division by zero")
    q = int(va / vb)
    r = va - q * vb
    return list(int_to_balanced_ternary(q, width)), list(int_to_balanced_ternary(r, width))


# ── Three-valued logic (single trit operations) ─────────────────────

def _validate_trit(a: int) -> int:
    if a not in (NEG, ZERO, POS):
        raise ValueError(f"invalid trit: {a}")
    return a


def tnot(a: int) -> int:
    """Three-valued NOT: negation of a single trit."""
    return -_validate_trit(a)


def tand(a: int, b: int) -> int:
    """Three-valued AND: minimum of two trits."""
    return min(_validate_trit(a), _validate_trit(b))


def tor(a: int, b: int) -> int:
    """Three-valued OR: maximum of two trits."""
    return max(_validate_trit(a), _validate_trit(b))


def txor(a: int, b: int) -> int:
    """Three-valued XOR of two trits."""
    a = _validate_trit(a)
    b = _validate_trit(b)
    if a == ZERO or b == ZERO:
        return ZERO
    return POS if a != b else NEG


# Aliases matching older API
ternary_not = tnot
ternary_and = tand
ternary_or = tor
ternary_xor = txor


def ternary_eq(a: int, b: int) -> int:
    """Three-valued equality: POS if equal, NEG if not."""
    a = _validate_trit(a)
    b = _validate_trit(b)
    return POS if a == b else NEG


# ── Quantization ────────────────────────────────────────────────────

def quantize(value: float, threshold: float = 0.3333333333) -> int:
    """Quantize a float to a ternary value."""
    if value > threshold:
        return POS
    elif value < -threshold:
        return NEG
    return ZERO


def quantize_array(values: list[float], threshold: float = 0.3333333333) -> list[int]:
    """Quantize a list of floats to ternary values."""
    return [quantize(v, threshold) for v in values]


# ── Ternary number class ────────────────────────────────────────────

@dataclass(frozen=True)
class TernaryNumber:
    """Immutable balanced ternary number."""
    trits: tuple[int, ...]

    def __post_init__(self) -> None:
        if not self.trits:
            raise ValueError("trits must not be empty")
        for t in self.trits:
            if t not in (NEG, ZERO, POS):
                raise ValueError(f"invalid trit: {t}")

    @classmethod
    def from_int(cls, value: int, width: int | None = None) -> TernaryNumber:
        return cls(int_to_balanced_ternary(value, width))

    @classmethod
    def from_string(cls, text: str) -> TernaryNumber:
        return cls(tuple(str_to_trits(text)))

    @classmethod
    def from_str(cls, text: str) -> TernaryNumber:
        return cls(tuple(str_to_trits(text)))

    def to_int(self) -> int:
        return balanced_ternary_to_int(self.trits)

    def __str__(self) -> str:
        return trits_to_str(self.trits)

    def __repr__(self) -> str:
        return f"TernaryNumber({str(self)})"

    def __add__(self, other: TernaryNumber) -> TernaryNumber:
        return TernaryNumber(tuple(ternary_add(self.trits, other.trits)))

    def __sub__(self, other: TernaryNumber) -> TernaryNumber:
        return TernaryNumber(tuple(ternary_sub(self.trits, other.trits)))

    def __mul__(self, other: TernaryNumber) -> TernaryNumber:
        return TernaryNumber(tuple(ternary_multiply(self.trits, other.trits)))

    def __neg__(self) -> TernaryNumber:
        return TernaryNumber(tuple(ternary_negate(self.trits)))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TernaryNumber):
            return NotImplemented
        return self.to_int() == other.to_int()

    def __int__(self) -> int:
        return self.to_int()

    def __len__(self) -> int:
        return len(self.trits)

    @property
    def width(self) -> int:
        return len(self.trits)
