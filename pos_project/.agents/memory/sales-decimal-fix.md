---
name: Sales model Decimal arithmetic
description: Dividing DecimalField values by Python int literal 100 produces float; causes TypeError when multiplied with another Decimal.
---

The rule: In any Django model method that multiplies Decimal fields, always divide by `Decimal('100')`, never by the int `100`.

**Why:** `Decimal('8') / 100` returns `0.08` (float in Python 3's truediv), and then `Decimal * float` raises `TypeError: unsupported operand type(s) for *: 'decimal.Decimal' and 'float'`.

**How to apply:** Affected locations in `sales/models.py`: `Sale.calculate_totals()` (discount_percentage and tax_rate), `SaleItem.save()` (discount_percentage). Any new model method doing percentage calculations on Decimal fields must use `Decimal('100')`.
