# TODO

## Completed
- None

## Next
- [ ] Add `RegisterView`/endpoint for `/api/accounts/register/` by wiring it to existing `users` API (or adding a dedicated accounts endpoint).
- [ ] Update `backend/erp_sales/urls.py` to include `path('api/accounts/', ...)` mapping to the proper register endpoint.
- [ ] Audit `payments/urls.py` for callback URL routing and align with `MpesaService` base_url usage.
- [ ] Fix `MpesaService.__init__` base_url to use environment (sandbox vs production) as requested.
- [ ] Restart server and run `python test_mpesa_stkpush.py admin Nbcmiri528. 254701111038 1 TEST001` and confirm success.
- [ ] List all working endpoints.

