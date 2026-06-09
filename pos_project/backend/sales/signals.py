from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender='sales.Sale')
def check_stock_levels_after_sale(sender, instance, created, **kwargs):
    """
    After a Sale is saved with status='completed', check every item's
    product stock. If stock_quantity <= reorder_level, fire an in-app
    notification to all manager/admin users (once per product per day).
    """
    if instance.status != 'completed':
        return

    try:
        _fire_low_stock_alerts(instance)
    except Exception as exc:
        logger.error("Stock alert signal failed for sale %s: %s", instance.pk, exc)


def _fire_low_stock_alerts(sale):
    from notifications.models import Notification, NotificationChannel
    from users.models import User

    channel = _get_or_create_inapp_channel()
    recipients = list(
        User.objects.filter(role__in=['super_admin', 'admin', 'manager'], is_active=True)
    )
    if not recipients:
        return

    today = timezone.now().date()

    for item in sale.items.select_related('product').all():
        product = item.product
        if product is None:
            continue

        stock = float(product.stock_quantity)
        reorder = float(product.reorder_level)

        if reorder <= 0:
            continue

        if stock > reorder:
            continue

        if stock <= 0:
            severity = 'critical'
            title = f"OUT OF STOCK: {product.name}"
            message = (
                f"{product.name} (SKU: {product.sku}) is completely out of stock. "
                f"Reorder level is {reorder:.0f}. Immediate restocking required."
            )
        else:
            severity = 'high' if stock <= reorder * 0.5 else 'medium'
            title = f"Low Stock Alert: {product.name}"
            message = (
                f"{product.name} (SKU: {product.sku}) has only {stock:.0f} units remaining "
                f"(reorder level: {reorder:.0f}). Please restock soon."
            )

        for user in recipients:
            already_notified = Notification.objects.filter(
                recipient_user=user,
                related_product=product,
                created_at__date=today,
                title__startswith=title[:30]
            ).exists()
            if already_notified:
                continue

            notif = Notification.objects.create(
                title=title,
                message=message,
                channel=channel,
                priority=severity,
                recipient_user=user,
                related_product=product,
                related_sale=sale,
                status='sent',
                sent_at=timezone.now(),
                metadata={
                    'stock_quantity': stock,
                    'reorder_level': reorder,
                    'product_id': product.pk,
                    'triggered_by_sale': sale.sale_id,
                }
            )
            notif.save()
            logger.info(
                "Stock alert created for product %s (stock=%s, reorder=%s) → user %s",
                product.name, stock, reorder, user.username
            )


def _get_or_create_inapp_channel():
    from notifications.models import NotificationChannel
    channel, _ = NotificationChannel.objects.get_or_create(
        channel_type='in_app',
        defaults={
            'name': 'In-App',
            'is_active': True,
            'is_default': True,
            'priority': 1,
        }
    )
    return channel
