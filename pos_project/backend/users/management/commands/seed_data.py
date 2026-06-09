from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random
from datetime import timedelta


class Command(BaseCommand):
    help = 'Seed the database with realistic demo data (products, customers, sales, etc.)'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')
        self._create_categories()
        self._create_suppliers()
        self._create_products()
        self._create_customers()
        self._create_sales()
        self.stdout.write(self.style.SUCCESS('\nSeed data created successfully!'))

    def _create_categories(self):
        from products.models import Category
        cats = [
            ('Beverages', 'beverages'),
            ('Bakery', 'bakery'),
            ('Dairy & Eggs', 'dairy-eggs'),
            ('Fresh Produce', 'fresh-produce'),
            ('Snacks & Confectionery', 'snacks'),
            ('Household Supplies', 'household'),
            ('Personal Care', 'personal-care'),
            ('Frozen Foods', 'frozen-foods'),
            ('Cereals & Grains', 'cereals-grains'),
            ('Meat & Seafood', 'meat-seafood'),
        ]
        for name, slug in cats:
            Category.objects.get_or_create(name=name, defaults={'slug': slug})
        self.stdout.write(f'  {len(cats)} categories ready')

    def _create_suppliers(self):
        from products.models import Supplier
        suppliers = [
            {'name': 'Bidco Africa Ltd', 'phone': '0722123456', 'email': 'orders@bidco.co.ke', 'contact_person': 'James Mwangi'},
            {'name': 'Unga Group PLC', 'phone': '0733234567', 'email': 'supply@unga.co.ke', 'contact_person': 'Mary Kamau'},
            {'name': 'Nairobi Fresh Farms', 'phone': '0711345678', 'email': 'fresh@nairobifarms.co.ke', 'contact_person': 'Peter Otieno'},
            {'name': 'East Africa Breweries', 'phone': '0721456789', 'email': 'trade@eabl.co.ke', 'contact_person': 'Grace Njeri'},
            {'name': 'Highlands Bakery', 'phone': '0712567890', 'email': 'orders@highlands.co.ke', 'contact_person': 'Samuel Kariuki'},
        ]
        created = 0
        for s in suppliers:
            if not Supplier.objects.filter(name=s['name']).exists():
                Supplier.objects.create(**s)
                created += 1
        self.stdout.write(f'  {created} new suppliers created')

    def _create_products(self):
        from products.models import Product, Category, Supplier

        cat = {c.slug: c for c in Category.objects.all()}
        sup = {s.name: s for s in Supplier.objects.all()}

        def get_cat(slug): return cat.get(slug)
        def get_sup(name): return sup.get(name)

        products_data = [
            # Beverages
            {'name': 'Coca-Cola 500ml', 'sku': 'BEV-001', 'category': 'beverages', 'supplier': 'East Africa Breweries', 'cost': 35, 'retail': 50, 'wholesale': 44, 'stock': 240, 'reorder': 50, 'unit': 'bottle'},
            {'name': 'Fanta Orange 500ml', 'sku': 'BEV-002', 'category': 'beverages', 'supplier': 'East Africa Breweries', 'cost': 35, 'retail': 50, 'wholesale': 44, 'stock': 180, 'reorder': 50, 'unit': 'bottle'},
            {'name': 'Sprite 500ml', 'sku': 'BEV-003', 'category': 'beverages', 'supplier': 'East Africa Breweries', 'cost': 35, 'retail': 50, 'wholesale': 44, 'stock': 160, 'reorder': 40, 'unit': 'bottle'},
            {'name': 'Dasani Water 500ml', 'sku': 'BEV-004', 'category': 'beverages', 'supplier': 'East Africa Breweries', 'cost': 20, 'retail': 35, 'wholesale': 30, 'stock': 300, 'reorder': 60, 'unit': 'bottle'},
            {'name': 'Delmonte Juice 1L', 'sku': 'BEV-005', 'category': 'beverages', 'supplier': 'Bidco Africa Ltd', 'cost': 120, 'retail': 175, 'wholesale': 155, 'stock': 80, 'reorder': 20, 'unit': 'litre'},
            {'name': 'Stoney Tangawizi 500ml', 'sku': 'BEV-006', 'category': 'beverages', 'supplier': 'East Africa Breweries', 'cost': 35, 'retail': 50, 'wholesale': 44, 'stock': 144, 'reorder': 36, 'unit': 'bottle'},
            # Bakery
            {'name': 'Supa Loaf Bread 400g', 'sku': 'BAK-001', 'category': 'bakery', 'supplier': 'Highlands Bakery', 'cost': 45, 'retail': 60, 'wholesale': 55, 'stock': 60, 'reorder': 20, 'unit': 'loaf'},
            {'name': 'Mandazi Dozen', 'sku': 'BAK-002', 'category': 'bakery', 'supplier': 'Highlands Bakery', 'cost': 70, 'retail': 100, 'wholesale': 90, 'stock': 40, 'reorder': 10, 'unit': 'dozen'},
            {'name': 'Chapati 5-Pack', 'sku': 'BAK-003', 'category': 'bakery', 'supplier': 'Highlands Bakery', 'cost': 80, 'retail': 120, 'wholesale': 105, 'stock': 30, 'reorder': 10, 'unit': 'pack'},
            # Dairy
            {'name': 'KCC Milk 500ml', 'sku': 'DAI-001', 'category': 'dairy-eggs', 'supplier': 'Nairobi Fresh Farms', 'cost': 45, 'retail': 65, 'wholesale': 58, 'stock': 100, 'reorder': 30, 'unit': 'pkt'},
            {'name': 'Brookside Yoghurt 200ml', 'sku': 'DAI-002', 'category': 'dairy-eggs', 'supplier': 'Nairobi Fresh Farms', 'cost': 55, 'retail': 80, 'wholesale': 70, 'stock': 60, 'reorder': 20, 'unit': 'cup'},
            {'name': 'Eggs (Tray of 30)', 'sku': 'DAI-003', 'category': 'dairy-eggs', 'supplier': 'Nairobi Fresh Farms', 'cost': 320, 'retail': 420, 'wholesale': 380, 'stock': 25, 'reorder': 8, 'unit': 'tray'},
            {'name': 'Butter 250g', 'sku': 'DAI-004', 'category': 'dairy-eggs', 'supplier': 'Bidco Africa Ltd', 'cost': 160, 'retail': 220, 'wholesale': 195, 'stock': 40, 'reorder': 10, 'unit': 'pkt'},
            # Fresh Produce
            {'name': 'Tomatoes 1kg', 'sku': 'PRO-001', 'category': 'fresh-produce', 'supplier': 'Nairobi Fresh Farms', 'cost': 60, 'retail': 90, 'wholesale': 80, 'stock': 35, 'reorder': 10, 'unit': 'kg'},
            {'name': 'Onions 1kg', 'sku': 'PRO-002', 'category': 'fresh-produce', 'supplier': 'Nairobi Fresh Farms', 'cost': 40, 'retail': 65, 'wholesale': 55, 'stock': 40, 'reorder': 10, 'unit': 'kg'},
            {'name': 'Potatoes 2kg', 'sku': 'PRO-003', 'category': 'fresh-produce', 'supplier': 'Nairobi Fresh Farms', 'cost': 80, 'retail': 120, 'wholesale': 105, 'stock': 50, 'reorder': 15, 'unit': 'bag'},
            # Snacks
            {'name': 'Pringles Original 165g', 'sku': 'SNK-001', 'category': 'snacks', 'supplier': 'Bidco Africa Ltd', 'cost': 250, 'retail': 350, 'wholesale': 310, 'stock': 48, 'reorder': 12, 'unit': 'can'},
            {'name': 'Cadbury Dairy Milk 80g', 'sku': 'SNK-002', 'category': 'snacks', 'supplier': 'Bidco Africa Ltd', 'cost': 85, 'retail': 130, 'wholesale': 115, 'stock': 60, 'reorder': 15, 'unit': 'bar'},
            {'name': 'Lays Chips 50g', 'sku': 'SNK-003', 'category': 'snacks', 'supplier': 'Bidco Africa Ltd', 'cost': 35, 'retail': 55, 'wholesale': 48, 'stock': 120, 'reorder': 30, 'unit': 'pkt'},
            {'name': 'Weetabix 430g', 'sku': 'SNK-004', 'category': 'cereals-grains', 'supplier': 'Unga Group PLC', 'cost': 180, 'retail': 260, 'wholesale': 230, 'stock': 35, 'reorder': 10, 'unit': 'box'},
            # Household
            {'name': 'Ariel Detergent 500g', 'sku': 'HHD-001', 'category': 'household', 'supplier': 'Bidco Africa Ltd', 'cost': 140, 'retail': 200, 'wholesale': 175, 'stock': 50, 'reorder': 15, 'unit': 'pkt'},
            {'name': 'Domestos Bleach 750ml', 'sku': 'HHD-002', 'category': 'household', 'supplier': 'Bidco Africa Ltd', 'cost': 90, 'retail': 135, 'wholesale': 120, 'stock': 40, 'reorder': 10, 'unit': 'btl'},
            {'name': 'Toilet Paper 10-Roll', 'sku': 'HHD-003', 'category': 'household', 'supplier': 'Bidco Africa Ltd', 'cost': 190, 'retail': 270, 'wholesale': 240, 'stock': 60, 'reorder': 15, 'unit': 'pack'},
            {'name': 'Bar Soap 175g', 'sku': 'HHD-004', 'category': 'household', 'supplier': 'Bidco Africa Ltd', 'cost': 45, 'retail': 70, 'wholesale': 62, 'stock': 80, 'reorder': 20, 'unit': 'bar'},
            # Personal Care
            {'name': 'Colgate Toothpaste 100ml', 'sku': 'PER-001', 'category': 'personal-care', 'supplier': 'Bidco Africa Ltd', 'cost': 90, 'retail': 130, 'wholesale': 115, 'stock': 55, 'reorder': 15, 'unit': 'tube'},
            {'name': 'Dove Shampoo 200ml', 'sku': 'PER-002', 'category': 'personal-care', 'supplier': 'Bidco Africa Ltd', 'cost': 210, 'retail': 300, 'wholesale': 265, 'stock': 40, 'reorder': 10, 'unit': 'btl'},
            # Cereals
            {'name': 'Unga Twiga 2kg', 'sku': 'CER-001', 'category': 'cereals-grains', 'supplier': 'Unga Group PLC', 'cost': 130, 'retail': 185, 'wholesale': 165, 'stock': 45, 'reorder': 12, 'unit': 'bag'},
            {'name': 'Jogoo Maize Flour 2kg', 'sku': 'CER-002', 'category': 'cereals-grains', 'supplier': 'Unga Group PLC', 'cost': 120, 'retail': 170, 'wholesale': 150, 'stock': 55, 'reorder': 15, 'unit': 'bag'},
            {'name': 'Kabras Sugar 2kg', 'sku': 'CER-003', 'category': 'cereals-grains', 'supplier': 'Unga Group PLC', 'cost': 170, 'retail': 240, 'wholesale': 210, 'stock': 70, 'reorder': 20, 'unit': 'bag'},
            {'name': 'Golden Sunflower Oil 2L', 'sku': 'CER-004', 'category': 'cereals-grains', 'supplier': 'Bidco Africa Ltd', 'cost': 420, 'retail': 580, 'wholesale': 520, 'stock': 30, 'reorder': 8, 'unit': 'btl'},
        ]

        created = 0
        for pd in products_data:
            if not Product.objects.filter(sku=pd['sku']).exists():
                Product.objects.create(
                    sku=pd['sku'],
                    name=pd['name'],
                    barcode=pd['sku'],
                    category=get_cat(pd['category']),
                    supplier=get_sup(pd['supplier']),
                    cost_price=Decimal(str(pd['cost'])),
                    retail_price=Decimal(str(pd['retail'])),
                    wholesale_price=Decimal(str(pd['wholesale'])),
                    stock_quantity=Decimal(str(pd['stock'])),
                    reorder_level=Decimal(str(pd['reorder'])),
                    unit=pd['unit'],
                    tax_rate=Decimal('16'),
                    is_active=True,
                )
                created += 1
        self.stdout.write(f'  {created} new products created ({Product.objects.count()} total)')

    def _create_customers(self):
        from customers.models import Customer
        customers_data = [
            {'name': 'John Mwangi', 'phone': '0712345001', 'email': 'john.mwangi@gmail.com'},
            {'name': 'Grace Kamau', 'phone': '0722345002', 'email': 'grace.kamau@yahoo.com'},
            {'name': 'Peter Otieno', 'phone': '0733345003', 'email': 'peter.otieno@outlook.com'},
            {'name': 'Sarah Njeri', 'phone': '0711345004', 'email': 'sarah.njeri@gmail.com'},
            {'name': 'David Kariuki', 'phone': '0721345005', 'email': 'david.kariuki@gmail.com'},
            {'name': 'Mary Wambui', 'phone': '0741345006', 'email': 'mary.wambui@gmail.com'},
            {'name': 'James Kimani', 'phone': '0751345007', 'email': 'james.kimani@gmail.com'},
            {'name': 'Ann Mutua', 'phone': '0761345008', 'email': 'ann.mutua@gmail.com'},
            {'name': 'Robert Omondi', 'phone': '0771345009', 'email': 'robert.omondi@gmail.com'},
            {'name': 'Lucy Wanjiku', 'phone': '0781345010', 'email': 'lucy.wanjiku@gmail.com'},
        ]
        created = 0
        for cd in customers_data:
            if not Customer.objects.filter(phone=cd['phone']).exists():
                Customer.objects.create(**cd, is_active=True)
                created += 1
        self.stdout.write(f'  {created} new customers created')

    def _create_sales(self):
        from sales.models import Sale, SaleItem, Payment
        from products.models import Product
        from customers.models import Customer
        from users.models import User

        products = list(Product.objects.filter(is_active=True))
        customers = list(Customer.objects.all())
        cashier = User.objects.filter(role='cashier').first() or User.objects.first()

        if not cashier:
            self.stdout.write('  No users found — skipping sales seed. Run create_demo_users first.')
            return

        if not products:
            self.stdout.write('  No products found — skipping sales seed.')
            return

        sale_count = 0
        today = timezone.now().date()

        for days_ago in range(30, 0, -1):
            sale_date = today - timedelta(days=days_ago)
            num_sales = random.randint(3, 10)

            for _ in range(num_sales):
                hour = random.randint(8, 20)
                minute = random.randint(0, 59)
                sale_datetime = timezone.make_aware(
                    timezone.datetime(sale_date.year, sale_date.month, sale_date.day, hour, minute)
                )
                customer = random.choice(customers) if random.random() > 0.3 else None

                sale = Sale.objects.create(
                    cashier=cashier,
                    customer=customer,
                    status='completed',
                    payment_status='paid',
                    tax_rate=Decimal('16'),
                    discount_percentage=Decimal('0'),
                )
                sale.sale_date = sale_datetime
                Sale.objects.filter(pk=sale.pk).update(sale_date=sale_datetime)

                num_items = random.randint(1, 5)
                sale_products = random.sample(products, min(num_items, len(products)))

                for product in sale_products:
                    qty = Decimal(str(random.randint(1, 4)))
                    unit_price = product.retail_price
                    item_subtotal = unit_price * qty
                    item_total = item_subtotal
                    SaleItem.objects.create(
                        sale=sale,
                        product=product,
                        product_name=product.name,
                        product_sku=product.sku,
                        quantity=qty,
                        unit_price=unit_price,
                        subtotal=item_subtotal,
                        discount_amount=Decimal('0'),
                        discount_percentage=Decimal('0'),
                        total=item_total,
                    )

                sale.calculate_totals()

                Payment.objects.create(
                    sale=sale,
                    payment_method='cash',
                    amount=sale.total,
                    recorded_by=cashier,
                )

                sale_count += 1

        self.stdout.write(f'  {sale_count} sales created across 30 days')
