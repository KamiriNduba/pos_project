---
name: Frontend page data ownership
description: CustomersPage, UsersPage, and ExpensesPage are self-contained; App.tsx no longer passes data or callbacks to them.
---

As of this session, three pages manage their own backend state via hooks:

- **CustomersPage** — fetches `/api/customers/` on mount; handles create/edit/deactivate internally.
- **UsersPage** — fetches `/api/users/` on mount; handles create (via registerAccount) and deactivate internally.
- **ExpensesPage** — fetches `/api/payments/expenses/` and `/api/payments/expense-categories/` on mount; handles create and delete internally.

**Why:** These pages previously received props from App.tsx (completedSales, users array) and built mock data locally. Moving state ownership into each page makes them independently testable and removes the need to thread data down through App.tsx.

**How to apply:** Do not pass `users`, `completedSales`, or `expenses` props to these three pages from App.tsx. The `openAddCustomerSignal` numeric counter prop on `CustomersPage` is still supported.
