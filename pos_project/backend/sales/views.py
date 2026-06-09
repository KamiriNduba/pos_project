from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime
from decimal import Decimal
from django.db import transaction
from django.http import HttpResponse

from .models import Sale, SaleItem, Payment, Receipt
from .serializers import (
    SaleSerializer,
    PaymentSerializer,
    ReceiptSerializer,
    SaleItemSerializer,
    SalePaymentSerializer,
    LoyaltyRedemptionSerializer,
)

from products.models import Product
from customers.models import Customer

# If you have a notifications util, keep it optional
try:
    from notifications.utils import send_notification
except Exception:  # pragma: no cover
    def send_notification(*args, **kwargs):
        return None


def Home(request):
    return HttpResponse("Sales ERP Backend Running")


class SaleViewSet(viewsets.ModelViewSet):
    """ViewSet for Sale operations."""

    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'payment_status', 'cashier', 'customer']
    search_fields = ['sale_id', 'customer__name', 'customer__phone', 'customer__email']
    ordering_fields = ['sale_date', 'total', 'sale_id']
    ordering = ['-sale_date']

    def get_queryset(self):
        user = self.request.user

        if getattr(user, 'role', None) in ['super_admin', 'admin', 'manager']:
            return Sale.objects.all()
        if getattr(user, 'role', None) == 'cashier':
            return Sale.objects.filter(cashier=user)

        return Sale.objects.none()

    def create(self, request, *args, **kwargs):
        """
        Override create to support the frontend POS format:
          {customer_name, grand_total, amount_paid, payment_method,
           payment_reference, items:[{product_id, quantity, price_type}]}
        as well as the standard DRF format with cart_items.
        """
        data = request.data

        # Detect frontend POS format (has 'items' key, no 'cart_items')
        if 'items' in data and 'cart_items' not in data:
            return self._create_from_pos_format(request, data)

        # Standard format: pass through to serializer
        serializer = self.get_serializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        sale = serializer.save()
        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def _create_from_pos_format(self, request, data):
        """Handle the frontend POS checkout format."""
        items = data.get('items', [])
        if not items:
            return Response({'error': 'Cart cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)

        cashier = request.user
        payment_method = data.get('payment_method', 'cash')
        payment_reference = data.get('payment_reference', '')
        amount_paid = Decimal(str(data.get('amount_paid', data.get('amount', 0))))

        # Resolve customer
        customer = None
        customer_name = data.get('customer_name', '')
        if customer_name and customer_name.lower() not in ('walk-in customer', 'walkin', ''):
            customer = Customer.objects.filter(name__iexact=customer_name).first()

        sale = Sale.objects.create(cashier=cashier, customer=customer)

        for item_data in items:
            product_id = item_data.get('product_id')
            quantity = Decimal(str(item_data.get('quantity', 1)))
            price_type = item_data.get('price_type', 'retail')

            try:
                product = Product.objects.get(id=product_id, is_active=True)
            except Product.DoesNotExist:
                return Response(
                    {'error': f'Product {product_id} not found'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if product.stock_quantity < quantity:
                return Response(
                    {'error': f'Insufficient stock for {product.name}. Available: {product.stock_quantity}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if price_type == 'wholesale':
                unit_price = product.wholesale_price or product.retail_price
            elif price_type == 'cost':
                unit_price = product.cost_price
            else:
                unit_price = product.retail_price

            SaleItem.objects.create(
                sale=sale,
                product=product,
                product_name=product.name,
                product_sku=product.sku,
                product_barcode=product.barcode,
                unit_price=unit_price,
                quantity=quantity,
                discount_percentage=Decimal('0'),
            )

            product.stock_quantity -= quantity
            product.save(update_fields=['stock_quantity'])

        sale.calculate_totals()
        sale.amount_paid = amount_paid
        if amount_paid >= sale.total:
            sale.payment_status = 'paid'
        sale.status = 'completed'
        sale.save(update_fields=['status', 'payment_status', 'amount_paid'])
        sale.add_loyalty_points()

        # Record the payment
        Payment.objects.create(
            sale=sale,
            payment_method=payment_method,
            amount=min(amount_paid, sale.total),
            reference_number=payment_reference,
            recorded_by=cashier,
        )

        Receipt.objects.create(sale=sale)
        sale.refresh_from_db()

        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='checkout')
    def checkout(self, request):
        """Complete POS checkout process."""
        serializer = SaleSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            sale = serializer.save()
            receipt_text = None
            if hasattr(sale, 'receipt'):
                receipt_text = sale.receipt.receipt_text
            return Response(
                {
                    'message': 'Sale completed successfully',
                    'sale': SaleSerializer(sale).data,
                    'receipt': receipt_text,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='add-payment')
    def add_payment(self, request, pk=None):
        """Add a payment to an existing sale."""
        sale = self.get_object()

        if sale.status != 'completed':
            return Response(
                {"error": f"Cannot add payment to sale with status: {sale.status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SalePaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        remaining_balance = sale.total - sale.amount_paid

        if data['amount'] > remaining_balance:
            return Response(
                {"error": f"Payment amount exceeds remaining balance. Remaining: {remaining_balance}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment = Payment.objects.create(
            sale=sale,
            payment_method=data['payment_method'],
            amount=data['amount'],
            mpesa_receipt_number=data.get('mpesa_receipt_number', ''),
            mpesa_phone_number=data.get('mpesa_phone_number', ''),
            card_last_four=data.get('card_last_four', ''),
            card_transaction_id=data.get('card_transaction_id', ''),
            reference_number=data.get('reference_number', ''),
            notes=data.get('notes', ''),
            recorded_by=request.user,
        )

        send_notification(request.user, f"Payment added: Sale #{sale.sale_id}")

        return Response(
            {
                'message': 'Payment added successfully',
                'payment': PaymentSerializer(payment).data,
                'sale': SaleSerializer(sale).data,
            }
        )

    @action(detail=True, methods=['post'], url_path='redeem-loyalty')
    def redeem_loyalty(self, request, pk=None):
        """Redeem customer loyalty points on this sale."""
        sale = self.get_object()

        if not sale.customer:
            return Response(
                {"error": "No customer associated with this sale"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = LoyaltyRedemptionSerializer(data=request.data, context={'sale': sale})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        points_to_redeem = serializer.validated_data['points_to_redeem']
        discount = Decimal(points_to_redeem)

        if discount > sale.total:
            discount = sale.total

        sale.loyalty_points_redeemed = points_to_redeem
        sale.loyalty_discount = discount
        sale.total = sale.total - discount
        sale.save(update_fields=['loyalty_points_redeemed', 'loyalty_discount', 'total'])

        sale.customer.redeem_loyalty_points(points_to_redeem)

        return Response(
            {
                'message': f'Redeemed {points_to_redeem} points for KES {discount} discount',
                'new_total': sale.total,
                'points_remaining': sale.customer.loyalty_records,
            }
        )

    @action(detail=True, methods=['post'], url_path='void')
    def void_sale(self, request, pk=None):
        """Void/cancel a sale. Requires manager permission."""
        sale = self.get_object()

        if getattr(request.user, 'role', None) not in ['super_admin', 'admin', 'manager']:
            return Response(
                {"error": "Only managers can void sales"},
                status=status.HTTP_403_FORBIDDEN,
            )

        reason = request.data.get('reason', '')
        if not reason:
            return Response(
                {"error": "Reason for voiding is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if sale.status == 'voided':
            return Response(
                {"error": "Sale is already voided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        success = sale.void_sale(request.user, reason)

        if success:
            return Response({'message': 'Sale voided successfully', 'sale_id': sale.sale_id})

        return Response({"error": "Failed to void sale"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='receipt')
    def get_receipt(self, request, pk=None):
        """Get receipt for a sale."""
        sale = self.get_object()

        if not hasattr(sale, 'receipt'):
            Receipt.objects.create(sale=sale)
            sale.refresh_from_db()

        return Response(
            {
                'sale_id': sale.sale_id,
                'receipt_text': sale.receipt.receipt_text,
                'receipt_number': sale.receipt.receipt_number,
            }
        )

    @action(detail=False, methods=['get'], url_path='today')
    def today_sales(self, request):
        today = timezone.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())

        sales_today = Sale.objects.filter(sale_date__range=(today_start, today_end), status='completed')
        total_sales = sales_today.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
        transaction_count = sales_today.count()

        return Response(
            {
                'date': today.isoformat(),
                'total_sales': total_sales,
                'transaction_count': transaction_count,
                'average_transaction': (total_sales / transaction_count) if transaction_count > 0 else 0,
            }
        )

    @action(detail=False, methods=['get'], url_path='sales-report')
    def sales_report(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date or not end_date:
            return Response(
                {"error": "start_date and end_date are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            end = datetime.combine(end, datetime.max.time())
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sales = Sale.objects.filter(sale_date__range=(start, end), status='completed')
        total_revenue = sales.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
        transaction_count = sales.count()

        return Response(
            {
                'period': {'start_date': start_date, 'end_date': end_date},
                'total_revenue': total_revenue,
                'transaction_count': transaction_count,
                'average_transaction': (total_revenue / transaction_count) if transaction_count > 0 else 0,
            }
        )


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing payments (read-only)."""

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'role', None) in ['super_admin', 'admin', 'manager', 'accountant']:
            return Payment.objects.all()
        return Payment.objects.filter(recorded_by=user)
