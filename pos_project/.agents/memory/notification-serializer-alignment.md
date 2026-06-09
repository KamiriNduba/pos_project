---
name: Notification serializer to frontend field alignment
description: Backend Notification model uses status/priority fields; frontend BackendNotification interface expects is_read/severity/action_url as booleans/enums.
---

The rule: `NotificationSerializer` must expose `is_read` (bool), `severity` (info/warning/error), and `action_url` (string) as computed `SerializerMethodField`s in addition to the native model fields.

**Why:** Frontend `BackendNotification` interface hardcodes these field names. The backend model instead uses `status` (pending/sent/read) and `priority` (low/medium/high/critical). The mapping: `is_read = status=='read'`; severity map: `low→info, medium→warning, high→warning, critical→error`; `action_url` built from `related_product_id` or `related_sale_id`.

**How to apply:** Also add `?is_read=false` filtering to `NotificationViewSet.get_queryset()` — map it to `status__in=['pending','sent']`.
