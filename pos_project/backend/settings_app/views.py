"""
Simple key-value app settings endpoint.
GET  /api/settings/ — returns all settings as a flat dict
PUT  /api/settings/ — updates settings (partial, merges with existing)
"""
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


# In-memory store (resets on server restart).
# For persistence across restarts, migrate to a DB model.
_DEFAULT_SETTINGS = {
    "store_name": "My POS Store",
    "currency": "KES",
    "currency_symbol": "KSh",
    "tax_rate": 16,
    "receipt_footer": "Thank you for shopping with us!",
    "low_stock_threshold": 10,
    "loyalty_points_per_100": 1,
    "allow_negative_stock": False,
    "require_customer_for_sale": False,
    "enable_mpesa": True,
    "business_phone": "",
    "business_email": "",
    "business_address": "",
}

_settings_store: dict = dict(_DEFAULT_SETTINGS)


class AppSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'value': _settings_store})

    def put(self, request):
        updates = request.data
        if not isinstance(updates, dict):
            return Response({'success': False, 'error': 'Expected a JSON object'}, status=400)
        _settings_store.update(updates)
        return Response({'success': True, 'data': _settings_store})

    def patch(self, request):
        return self.put(request)
