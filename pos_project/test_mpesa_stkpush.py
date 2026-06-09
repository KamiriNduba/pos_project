import os
import sys
import json

import django
from django.conf import settings



def bootstrap_django():
    # Ensure repo root is on sys.path so `backend.*` imports resolve.
    repo_root = os.path.dirname(os.path.abspath(__file__))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.erp_sales.settings')
    django.setup()


def make_request(payload):
    """This script expects Mpesa to be reachable via your Django API.

    It sends an authenticated request to:
      POST /api/payments/mpesa-payments/stk-push/

    NOTE: Your Mpesa endpoints are DRF ViewSet actions.
    """
    import requests
    base_url = os.environ.get('DJANGO_BASE_URL', 'http://127.0.0.1:8000')
    access_token = os.environ.get('DJANGO_ACCESS_TOKEN')

    if not access_token:
        print('Missing env var DJANGO_ACCESS_TOKEN. Create a JWT first using /api/token/.', file=sys.stderr)
        sys.exit(2)

    url = f"{base_url}/api/payments/mpesa-payments/stk-push/"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    r = requests.post(url, headers=headers, json=payload, timeout=60)
    try:
        data = r.json()
    except Exception:
        data = r.text

    return r.status_code, data


def main(argv):
    # Expected args (as provided by user):
    # admin <phone> <amount> <reference>
    if len(argv) != 5:
        print('Usage: python test_mpesa_stkpush.py <username> <phone> <amount> <reference>', file=sys.stderr)
        return 1

    username = argv[1]
    phone = argv[2]
    amount = argv[3]
    reference = argv[4]

    bootstrap_django()

    # Create payload matching MpesaStkPushSerializer
    payload = {
        'phone_number': phone,
        'amount': amount,
        'account_reference': reference,
        'transaction_desc': f"STK Push for {username}",
    }

    status_code, data = make_request(payload)

    print(json.dumps({'status_code': status_code, 'response': data}, indent=2, default=str))
    if 200 <= status_code < 300:
        return 0
    return 3


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))

