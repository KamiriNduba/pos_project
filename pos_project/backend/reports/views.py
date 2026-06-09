from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, F, Avg, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import SavedReport
from .serializers import SavedReportSerializer


class ReportViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard_stats(self, request):
        from sales.models import Sale
        from products.models import Product
        from customers.models import Customer

        today = timezone.now().date()
        today_start = timezone.make_aware(
            timezone.datetime.combine(today, timezone.datetime.min.time())
        )
        week_start = timezone.make_aware(
            timezone.datetime.combine(today - timedelta(days=7), timezone.datetime.min.time())
        )
        month_start = timezone.make_aware(
            timezone.datetime.combine(today.replace(day=1), timezone.datetime.min.time())
        )

        def sales_agg(qs):
            agg = qs.filter(status='completed').aggregate(
                total=Sum('total'), count=Count('id')
            )
            return float(agg['total'] or 0), agg['count'] or 0

        today_total, today_count = sales_agg(Sale.objects.filter(sale_date__gte=today_start))
        week_total, week_count = sales_agg(Sale.objects.filter(sale_date__gte=week_start))
        month_total, month_count = sales_agg(Sale.objects.filter(sale_date__gte=month_start))

        low_stock = Product.objects.filter(
            is_active=True, stock_quantity__lte=F('reorder_level')
        ).exclude(reorder_level=0).count()

        total_products = Product.objects.filter(is_active=True).count()
        total_customers = Customer.objects.filter(is_active=True).count()

        return Response({
            'today_sales': today_total,
            'today_transactions': today_count,
            'week_sales': week_total,
            'week_transactions': week_count,
            'month_sales': month_total,
            'month_transactions': month_count,
            'low_stock_count': low_stock,
            'total_products': total_products,
            'total_customers': total_customers,
        })

    @action(detail=False, methods=['get'], url_path='sales-summary')
    def sales_summary(self, request):
        from sales.models import Sale, SaleItem

        days = int(request.query_params.get('days', 30))
        start = timezone.make_aware(
            timezone.datetime.combine(
                timezone.now().date() - timedelta(days=days),
                timezone.datetime.min.time()
            )
        )

        sales = Sale.objects.filter(status='completed', sale_date__gte=start)

        agg = sales.aggregate(
            total_revenue=Sum('total'),
            total_tax=Sum('tax_amount'),
            total_discount=Sum('discount_amount'),
            count=Count('id'),
        )

        daily = (
            sales.extra(select={'day': "date(sale_date)"})
            .values('day')
            .annotate(total=Sum('total'), count=Count('id'))
            .order_by('day')
        )

        return Response({
            'period_days': days,
            'total_revenue': float(agg['total_revenue'] or 0),
            'total_tax': float(agg['total_tax'] or 0),
            'total_discount': float(agg['total_discount'] or 0),
            'transaction_count': agg['count'] or 0,
            'daily_breakdown': [
                {'date': str(d['day']), 'total': float(d['total'] or 0), 'count': d['count']}
                for d in daily
            ],
        })

    @action(detail=False, methods=['get'], url_path='top-products')
    def top_products(self, request):
        from sales.models import SaleItem

        days = int(request.query_params.get('days', 30))
        limit = int(request.query_params.get('limit', 10))
        start = timezone.make_aware(
            timezone.datetime.combine(
                timezone.now().date() - timedelta(days=days),
                timezone.datetime.min.time()
            )
        )

        top = (
            SaleItem.objects.filter(sale__status='completed', sale__sale_date__gte=start)
            .values('product__id', 'product__name', 'product__sku')
            .annotate(
                qty_sold=Sum('quantity'),
                revenue=Sum('total'),
            )
            .order_by('-revenue')[:limit]
        )

        return Response([
            {
                'product_id': t['product__id'],
                'product_name': t['product__name'],
                'sku': t['product__sku'],
                'qty_sold': float(t['qty_sold'] or 0),
                'revenue': float(t['revenue'] or 0),
            }
            for t in top
        ])

    @action(detail=False, methods=['get'], url_path='inventory-status')
    def inventory_status(self, request):
        from products.models import Product

        products = Product.objects.filter(is_active=True).select_related('category', 'supplier')
        total_value = sum(float(p.stock_quantity * p.cost_price) for p in products)
        low_stock = [p for p in products if p.reorder_level > 0 and p.stock_quantity <= p.reorder_level]

        return Response({
            'total_products': len(products),
            'total_stock_value': total_value,
            'low_stock_count': len(low_stock),
            'low_stock_items': [
                {
                    'id': p.id,
                    'name': p.name,
                    'sku': p.sku,
                    'stock': float(p.stock_quantity),
                    'reorder_level': float(p.reorder_level),
                    'supplier': p.supplier.name if p.supplier else None,
                }
                for p in low_stock[:20]
            ],
        })

    @action(detail=False, methods=['get'], url_path='customer-summary')
    def customer_summary(self, request):
        from sales.models import Sale
        from customers.models import Customer

        days = int(request.query_params.get('days', 30))
        start = timezone.make_aware(
            timezone.datetime.combine(
                timezone.now().date() - timedelta(days=days),
                timezone.datetime.min.time()
            )
        )

        top_customers = (
            Sale.objects.filter(status='completed', sale_date__gte=start, customer__isnull=False)
            .values('customer__id', 'customer__name', 'customer__phone')
            .annotate(spend=Sum('total'), visits=Count('id'))
            .order_by('-spend')[:10]
        )

        total_customers = Customer.objects.filter(is_active=True).count()
        new_customers = Customer.objects.filter(
            is_active=True, created_at__gte=start
        ).count()

        return Response({
            'total_customers': total_customers,
            'new_customers_period': new_customers,
            'top_customers': [
                {
                    'id': c['customer__id'],
                    'name': c['customer__name'],
                    'phone': c['customer__phone'],
                    'total_spend': float(c['spend'] or 0),
                    'visit_count': c['visits'],
                }
                for c in top_customers
            ],
        })

    @action(detail=False, methods=['get'], url_path='payment-methods')
    def payment_methods(self, request):
        from sales.models import Payment

        days = int(request.query_params.get('days', 30))
        start = timezone.make_aware(
            timezone.datetime.combine(
                timezone.now().date() - timedelta(days=days),
                timezone.datetime.min.time()
            )
        )

        breakdown = (
            Payment.objects.filter(payment_date__gte=start)
            .values('payment_method')
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('-total')
        )

        return Response([
            {
                'method': b['payment_method'],
                'total': float(b['total'] or 0),
                'count': b['count'],
            }
            for b in breakdown
        ])

    @action(detail=False, methods=['post'], url_path='generate')
    def generate_report(self, request):
        report_type = request.data.get('report_type', 'sales')
        return Response({'message': f'Report {report_type} queued', 'status': 'ok'})


class SavedReportViewSet(viewsets.ModelViewSet):
    queryset = SavedReport.objects.all()
    serializer_class = SavedReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['report_type', 'is_public']
    search_fields = ['name', 'description']
    ordering = ['-created_at']

    def get_queryset(self):
        return SavedReport.objects.filter(
            Q(created_by=self.request.user) | Q(is_public=True)
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
