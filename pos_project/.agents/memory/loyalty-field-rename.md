---
name: Loyalty field rename
description: Customer model field was renamed loyalty_points → loyalty_records; serializers re-expose it as loyalty_points for API compat.
---

The Django `Customer` model at `backend/customers/models.py` stores loyalty points in an `IntegerField` named `loyalty_records`. This was renamed from the original `loyalty_points` to avoid collision with a related model also named `loyalty_points`.

**Why:** The old `loyalty_points` model (a related FK model) and the `loyalty_points` IntegerField had the same name, causing Django ORM accessor conflicts. Renaming the field to `loyalty_records` resolved this.

**How to apply:** Any backend code that reads/writes the loyalty accumulator field must use `loyalty_records`. The customer serializer in `customers/serializers.py` maps this to `loyalty_points` via `source='loyalty_records'` so the REST API and frontend continue to receive `loyalty_points` in JSON responses without changes.

Migration: `customers/0002_alter_customer_email_loyaltyrecord_and_more.py`
