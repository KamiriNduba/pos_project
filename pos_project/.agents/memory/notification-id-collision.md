---
name: Notification ID collision under concurrent creation
description: The notification_id field used self.id (None before save) as suffix, causing UNIQUE constraint failures when two notifications created within the same second.
---

The rule: The `Notification.save()` method generates `notification_id` as `NOT-{datetime}-{suffix}`. The original suffix was `self.id or '000'` — but `self.id` is None before first save, so concurrent creations all get `'000'` and collide.

**Why:** Fixed by using `uuid.uuid4().hex[:6].upper()` as the suffix instead, guaranteeing uniqueness.

**How to apply:** `uuid` was already imported in `notifications/models.py`. Pattern to remember: any counter/sequence-based ID generated in `save()` before the DB assigns a PK must use a UUID or random suffix, not the not-yet-assigned PK.
