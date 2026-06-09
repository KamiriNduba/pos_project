import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone


PRODUCTS_DATA = [
    ("Unga Jogoo 2kg", "Grains & Flour", "JOG-001", 180, 140, 500, 8),
    ("Unga Hostess 2kg", "Grains & Flour", "HOS-002", 175, 135, 400, 10),
    ("Rice Pishori 5kg", "Grains & Flour", "PIS-003", 950, 750, 200, 20),
    ("Sunflower Oil 2L", "Cooking Oil", "SUN-004", 520, 400, 300, 15),
    ("Rina Oil 1L", "Cooking Oil", "RIN-005", 270, 210, 250, 12),
    ("Golden Fry 3L", "Cooking Oil", "GOL-006", 750, 580, 180, 10),
    ("Sugar Mumias 2kg", "Sugar & Salt", "MUM-007", 320, 240, 400, 25),
    ("Salt Kensalt 1kg", "Sugar & Salt", "KEN-008", 60, 45, 600, 30),
    ("Maziwa Fresh 500ml", "Dairy", "MAZ-009", 65, 50, 500, 20),
    ("Brookside Milk 500ml", "Dairy", "BRK-010", 70, 55, 480, 20),
    ("Blue Band 250g", "Spreads", "BBD-011", 145, 110, 300, 15),
    ("Nutella 200g", "Spreads", "NUT-012", 850, 650, 80, 5),
    ("Exe Biscuits 200g", "Snacks", "EXE-013", 55, 40, 400, 30),
    ("Nice Biscuits 400g", "Snacks", "NIC-014", 110, 85, 350, 25),
    ("Pringles Original 149g", "Snacks", "PRG-015", 450, 340, 100, 8),
    ("Coca-Cola 500ml", "Beverages", "COK-016", 80, 60, 700, 50),
    ("Pepsi 500ml", "Beverages", "PEP-017", 75, 58, 500, 40),
    ("Dettol Soap 175g", "Personal Care", "DET-018", 120, 90, 400, 20),
    ("Lux Soap 175g", "Personal Care", "LUX-019", 110, 85, 350, 20),
    ("Colgate Toothpaste 75ml", "Personal Care", "COL-020", 180, 140, 300, 15),
    ("Omo Detergent 1kg", "Cleaning", "OMO-021", 380, 290, 250, 15),
    ("Ariel Detergent 1kg", "Cleaning", "ARI-022", 420, 320, 200, 12),
    ("Jik Bleach 1L", "Cleaning", "JIK-023", 150, 115, 300, 20),
    ("Pampers Size 3 x40", "Baby Care", "PAM-024", 1250, 960, 120, 8),
    ("Huggies Size 3 x44", "Baby Care", "HUG-025", 1300, 1000, 100, 6),
    ("Indomie Chicken 70g", "Instant Food", "IND-026", 35, 25, 800, 60),
    ("Knorr Chicken Cubes 8s", "Spices", "KNR-027", 85, 65, 500, 30),
    ("Royco Mchuzi Mix 75g", "Spices", "ROY-028", 75, 58, 600, 35),
    ("Keringet Water 500ml", "Beverages", "KER-029", 50, 38, 1000, 80),
    ("Refresh Juice 300ml", "Beverages", "REF-030", 70, 52, 600, 50),
]

SUPPLIERS_DATA = [
    ("Naivas Wholesale Ltd", "John Kariuki", "+254 700 100 001", "naivas.wholesale@email.com"),
    ("Bidco Africa Ltd", "Alice Wanjiru", "+254 700 100 002", "bidco.africa@email.com"),
    ("Unga Group Ltd", "Peter Mwangi", "+254 700 100 003", "unga.group@email.com"),
    ("East African Breweries", "Mary Njeri", "+254 700 100 004", "eabl@email.com"),
    ("Procter & Gamble Kenya", "James Otieno", "+254 700 100 005", "pg.kenya@email.com"),
]

CUSTOMERS_DATA = [
    ("Grace Wanjiru", "+254 712 001 001", "grace.wanjiru@email.com", "Nairobi"),
    ("James Mwangi", "+254 712 001 002", "james.mwangi@email.com", "Westlands"),
    ("Fatuma Hassan", "+254 712 001 003", "fatuma.hassan@email.com", "Mombasa"),
    ("Kevin Odhiambo", "+254 712 001 004", "kevin.odh@email.com", "Kisumu"),
    ("Agnes Kamau", "+254 712 001 005", "agnes.kamau@email.com", "Nakuru"),
    ("Brian Kipchoge", "+254 712 001 006", "brian.kip@email.com", "Eldoret"),
    ("Diana Mutuku", "+254 712 001 007", "diana.mut@email.com", "Machakos"),
    ("Samuel Njoroge", "+254 712 001 008", "samuel.njr@email.com", "Nairobi"),
    ("Wambui Gichuru", "+254 712 001 009", "wambui.gi@email.com", "Thika"),
    ("Patrick Otieno", "+254 712 001 010", "patrick.ot@email.com", "Kisumu"),
]

USERS_DATA = [
    ("cashier_user",   "Demo1234!",      "cashier",        "cashier_user@pos.local"),
    ("manager_user",   "Demo1234!",      "manager",        "manager_user@pos.local"),
    ("admin_user",     "Demo1234!",      "admin",          "admin_user@pos.local"),
    ("superadmin",     "Superadmin1234!", "super_admin",   "superadmin@pos.local"),
    ("storekeeper_user","Demo1234!",     "storekeeper",    "storekeeper_user@pos.local"),
    ("accountant_user","Demo1234!",      "accountant",     "accountant_user@pos.local"),
    ("viewer_user",    "Demo1234!",      "viewer",         "viewer_user@pos.local"),
]


class Command(BaseCommand):
    help = "Seed demo users, products, customers, suppliers, and 30 days of sales"

    def handle(self, *args, **options):
        self._create_users()
        suppliers = self._create_suppliers()
        products = self._create_products(suppliers)
        customers = self._create_customers()
        self._create_sales(products, customers)
        self.stdout.write(self.style.SUCCESS("✓ Demo data seeded successfully"))

    def _create_users(self):
        from users.models import User
        created = 0
        for username, password, role, email in USERS_DATA:
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username, password=password,
                    role=role, email=email, is_active=True,
                    is_staff=(role in ('super_admin', 'admin')),
                )
                created += 1
        self.stdout.write(f"  Users: {created} created (already existed: {7 - created})")

    def _create_suppliers(self):
        from products.models import Supplier
        suppliers = []
        for name, contact, phone, email in SUPPLIERS_DATA:
            s, _ = Supplier.objects.get_or_create(
                name=name,
                defaults={"contact_person": contact, "phone": phone, "email": email}
            )
            suppliers.append(s)
        self.stdout.write(f"  Suppliers: {len(suppliers)}")
        return suppliers

    def _create_products(self, suppliers):
        from products.models import Product, Category
        products = []
        supplier_cycle = suppliers * 10
        for i, (name, cat_name, sku, retail, cost, stock, reorder) in enumerate(PRODUCTS_DATA):
            cat, _ = Category.objects.get_or_create(name=cat_name)
            supplier = supplier_cycle[i % len(suppliers)]
            p, _ = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    "name": name,
                    "category": cat,
                    "supplier": supplier,
                    "retail_price": Decimal(str(retail)),
                    "cost_price": Decimal(str(cost)),
                    "stock_quantity": Decimal(str(stock)),
                    "reorder_level": Decimal(str(reorder)),
                    "tax_rate": 16,
                    "is_active": True,
                    "unit": "pcs",
                    "barcode": f"BC{sku.replace('-', '')}",
                }
            )
            products.append(p)
        self.stdout.write(f"  Products: {len(products)}")
        return products

    def _create_customers(self):
        from customers.models import Customer
        customers = []
        for name, phone, email, city in CUSTOMERS_DATA:
            c, _ = Customer.objects.get_or_create(
                phone=phone,
                defaults={
                    "name": name,
                    "email": email,
                    "city": city,
                    "is_active": True,
                }
            )
            customers.append(c)
        self.stdout.write(f"  Customers: {len(customers)}")
        return customers

    def _create_sales(self, products, customers):
        from sales.models import Sale, SaleItem
        from users.models import User

        cashiers = list(User.objects.filter(role__in=['cashier', 'manager', 'admin'], is_active=True))
        if not cashiers:
            cashiers = list(User.objects.filter(is_active=True)[:2])

        payment_methods = ['cash', 'mpesa', 'card', 'cash', 'mpesa']
        sale_count = 0
        today = timezone.now().date()

        for day_offset in range(29, -1, -1):
            target_date = today - timedelta(days=day_offset)
            sales_today = random.randint(5, 10)

            for _ in range(sales_today):
                num_items = random.randint(1, 4)
                chosen_products = random.sample(products, min(num_items, len(products)))
                cashier = random.choice(cashiers)
                customer = random.choice(customers) if random.random() > 0.3 else None
                payment_method = random.choice(payment_methods)

                sale = Sale(
                    cashier=cashier,
                    customer=customer,
                    status='completed',
                    payment_status='paid',
                    discount_percentage=Decimal('0'),
                    tax_rate=Decimal('0'),
                )
                sale.save()

                sale_total = Decimal('0')
                for product in chosen_products:
                    qty = Decimal(str(random.randint(1, 3)))
                    price = product.retail_price
                    line_subtotal = price * qty

                    item = SaleItem(
                        sale=sale,
                        product=product,
                        product_name=product.name,
                        product_sku=product.sku,
                        unit_price=price,
                        quantity=qty,
                        subtotal=line_subtotal,
                        discount_percentage=Decimal('0'),
                        discount_amount=Decimal('0'),
                    )
                    item.save()
                    sale_total += line_subtotal

                sale.subtotal = sale_total
                sale.total = sale_total
                sale.amount_paid = sale_total
                sale.change_due = Decimal('0')
                sale.status = 'completed'
                sale.payment_status = 'paid'
                sale.save(update_fields=['subtotal', 'total', 'amount_paid', 'change_due', 'status', 'payment_status'])

                from sales.models import Payment
                Payment.objects.create(
                    sale=sale,
                    payment_method=payment_method,
                    amount=sale_total,
                    recorded_by=cashier,
                )

                Sale.objects.filter(pk=sale.pk).update(
                    sale_date=timezone.make_aware(
                        timezone.datetime.combine(target_date, timezone.datetime.min.time())
                        + timedelta(hours=random.randint(8, 20), minutes=random.randint(0, 59))
                    )
                )
                sale_count += 1

        self.stdout.write(f"  Sales: {sale_count} across 30 days")
