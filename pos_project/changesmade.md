# Changes Made — Django + React POS/ERP System

## Overview
Full end-to-end wiring of the Django backend and React frontend. Fixed all backend bugs, applied migrations, and replaced every page that used mock/local data with real API calls.

---

## Backend Fixes (Session 1)

### `payments/models.py`
- Removed duplicate model class definitions and orphaned code that caused `AppRegistryNotReady` errors on startup.
- Added missing `api_base_url` property to `MpesaAccount` model.

### `customers/models.py`
- Renamed field `loyalty_points` (IntegerField) to `loyalty_records` to avoid collision with the `loyalty_points` related model.
- Made `email` field optional (`blank=True, null=True`).
- Fixed model methods (`get_account_reference`, `update_total_spent`).
- Added new `LoyaltyRecord` model to replace the old `loyalty_points` model.

### `returns/serializers.py` and `returns/views.py`
- Fixed Python syntax errors (unterminated string literals, misplaced code).
- Removed duplicate `ReturnViewSet` class definition.

### `reports/views.py`
- Fixed bad import (`from reports.report_service import ...` → correct module path).

### `payments/serializers.py`
- Fixed indentation errors in several serializer classes.

### `payments/mpesa_service.py`
- Added `api_base_url` property to `MpesaAccount` that was referenced but never defined.

### `reports/report_service.py`
- Updated `loyalty_points` field references to `loyalty_records` (x2 occurrences).

### All `loyalty_points` field references
- Updated across: `customers/admin.py`, `customers/views.py`, `customers/serializers.py`, `sales/models.py`, `returns/models.py`, `reports/report_service.py`.
- Serializers expose the field as `loyalty_points` via `source='loyalty_records'` for API backward compatibility.

### Migrations Applied (Session 1)
- `customers/0002` — Alters `email` field, creates `LoyaltyRecord` model, removes old `loyalty_points` model.
- `payments/0003` — Removes stale indexes/model from payments app, adds new fields to `PaymentAccount`, `MpesaAccount`, `MpesaTransaction`, `PaymentTransaction`.

---

## Frontend Fixes (Session 1)

### `services/api.ts`
Added new exported API functions:
- `updateCustomer(id, data)` — PATCH `/customers/{id}/`
- `deleteCustomer(id)` — DELETE `/customers/{id}/`
- `loadUsers()` — GET `/users/`
- `deactivateUser(id)` — PATCH `/users/{id}/` with `{is_active: false}`
- `loadExpenses()` — GET `/payments/expenses/`
- `loadExpenseCategories()` — GET `/payments/expense-categories/`
- `createExpense(data)` — POST `/payments/expenses/`
- `deleteExpense(id)` — DELETE `/payments/expenses/{id}/`

Added new interfaces: `BackendExpenseCategory`, `BackendExpense`, `CreateExpenseInput`.

### `components/pages/CustomersPage.tsx`
- **Complete rewrite** — removed dependency on `completedSales` prop and `buildCustomersFromSales` fallback.
- Now fetches real customers from `/api/customers/` on mount.
- Add/Edit/Deactivate customer all call real API endpoints.

### `components/pages/UsersPage.tsx`
- **Complete rewrite** — component now manages its own state (no longer receives `users` prop).
- Fetches users from `/api/users/` on mount.
- Add User form submits via `registerAccount()` with username, email, password, and role.

### `components/pages/ExpensesPage.tsx`
- **Complete rewrite** — wired to real backend at `/api/payments/expenses/`.
- Fetches expense categories, add/delete expense via API.

### `App.tsx`
- Removed `completedSales` prop from `CustomersPage`, `users` prop from `UsersPage`.
- Removed `users` state and all `setUsers` calls.

---

## Backend Fixes (Session 2 — Full End-to-End)

### `users/models.py`
- Removed obsolete `inventory_clerk` role; replaced with `storekeeper` throughout (`can_manage_products`, `can_manage_stock`, `get_permissions_list`, `UserViewSet`).

### `sales/models.py`
- Fixed tax to **inclusive 16% VAT**:
  - `tax_amount = total × rate / (100 + rate)` (was `total × rate / 100`)
  - `total` is the pre-tax price — no add-on; VAT is already inside the price.

### `products/serializers.py`
- Rewrote to remove non-existent fields (`supplier_sku`, `carton_price`, `icon`, `color`, etc.).
- Added `price`, `quantity`, `base_unit_name`, `tax_rate`, `supplier_name` response fields.
- Fixed `profit_margin`, `is_low_stock`, `stock_value` as `SerializerMethodField`.

### `products/views.py`
- Changed bulk-import URL from `bulk-import` → `import` (fixes 404 on frontend).
- Updated `export` action: adds Supplier, Cost Price, Reorder Level, Tax Rate columns; filename → `inventory.xlsx`.
- Added `download_template` action: returns populated Excel template for product import.

### `products/urls.py`
- Removed duplicate manual `download-template` path (now handled by router via ViewSet action).

### `returns/urls.py`, `notifications/urls.py`, `reports/urls.py`
- Removed double `api/` prefix in URL patterns that caused 404 errors.

### `reports/views.py` *(full rewrite)*
- All endpoints now query real database records:
  - `dashboard` — today/week/month sales, transaction counts, low-stock count, totals.
  - `sales_summary` — revenue, tax, discount, cost aggregates with time-series breakdown.
  - `top_products` — ranked by revenue with quantity and margin.
  - `inventory_status` — stock levels, reorder alerts, stock value.
  - `customer_summary` — spend totals, visit counts, loyalty points.
  - `payment_methods` — breakdown by payment method.

### `users/management/commands/create_demo_users.py` *(new)*
Creates all 7 demo accounts:

| Username | Role | Password |
|---|---|---|
| `superadmin` | super_admin | `Superadmin1234!` |
| `admin_user` | admin | `Demo1234!` |
| `manager_user` | manager | `Demo1234!` |
| `storekeeper_user` | storekeeper | `Demo1234!` |
| `cashier_user` | cashier | `Demo1234!` |
| `accountant_user` | accountant | `Demo1234!` |
| `viewer_user` | viewer | `Demo1234!` |

### `users/management/commands/seed_data.py` *(new)*
Seeds the database with realistic Kenyan supermarket data:
- **10 categories**: Beverages, Bakery, Dairy & Eggs, Fresh Produce, Snacks, Household, Personal Care, Frozen Foods, Cereals & Grains, Meat & Seafood
- **5 suppliers**: Bidco Africa, Unga Group, Nairobi Fresh Farms, East Africa Breweries, Highlands Bakery
- **30 products** with real KSh prices, 16% VAT inclusive (Coca-Cola, Jogoo Flour, Ariel, Colgate, etc.)
- **10 customers** with Kenyan names and phone numbers
- **219 sales** spread across 30 days (3–10 per day, random product mix)

---

## Frontend Fixes (Session 2)

### `services/api.ts`
- Added `tax_rate` and `supplier_name` to `BackendProduct` interface.
- Fixed `mapProductFromApi`: tax now mapped from `product.tax_rate` (default 16); supplier name included.
- Added new exported API functions:
  - `getSuppliers()` / `createSupplier()` / `updateSupplier()` — supplier CRUD
  - `getPurchaseOrders()` / `createPurchaseOrder()` — purchase order CRUD
  - `getReportsDashboard()` — dashboard KPIs
  - `getReportsSalesSummary(days)` — time-series sales
  - `getReportsTopProducts(days, limit)` — top products by revenue
  - `exportInventory()` — downloads inventory as Excel

### `components/pages/POSPageEnhanced.tsx`
- Added `supplierName?: string` to `POSProduct` interface.
- Added `orderNotes` state and **Order Notes** textarea to the cart panel.
- Fixed VAT display: `tax component = price × qty × rate / (100 + rate)`; total is subtotal only (no add-on).
- Changed label from `Tax:` → `VAT (incl.):`.
- Notes cleared after every completed payment.

### `components/pages/ProductsPageEnhanced.tsx`
- Added `supplier?: string` to `Product` interface.
- `mapLiveProduct` maps `product.supplierName` → `product.supplier`.
- Added **Supplier** column to products table.

### `components/pages/SuppliersPage.tsx`
- Added `useEffect` + `getSuppliers` API call on mount.
- Shows real supplier records from backend; falls back to locally-derived list if API is unavailable.

### `components/pages/PurchasesPage.tsx`
- Added `useEffect` + `getPurchaseOrders` API call on mount.
- Uses real purchase order data from backend; falls back to prop-derived data if unavailable.

---

## How to Re-run Setup (after a DB reset)

```bash
# Must use Python 3.12 — packages are installed for 3.12, not the system Python 3.13
cd backend
/home/runner/workspace/.pythonlibs/bin/python3.12 manage.py migrate
/home/runner/workspace/.pythonlibs/bin/python3.12 manage.py create_demo_users
/home/runner/workspace/.pythonlibs/bin/python3.12 manage.py seed_data
```

---

## API Compatibility Notes
- Customer serializer exposes `loyalty_points` (mapped from `loyalty_records`) — frontend continues to work.
- All endpoints use standard DRF ModelViewSet patterns with JWT Bearer token auth.
- Tax is **inclusive**: `KSh 50` for Coca-Cola means `KSh 6.90` is VAT, `KSh 43.10` is net. No tax added on checkout.
