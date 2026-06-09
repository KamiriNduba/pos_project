# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.utils import timezone
import uuid

class User(AbstractUser):
    """
    Custom User model for ERP/POS system.
    Extends Django's AbstractUser with business-specific fields.
    """
    
    # === IDENTIFIERS ===
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Public identifier for API"
    )
    
    # === CONTACT INFORMATION ===
    phone = models.CharField(
        max_length=15,
        unique=True,
        blank=True,
        null=True,
        default=None,
        validators=[
            RegexValidator(
                regex=r'^(\+254|0)[17]\d{8}$',
                message="Phone must be Kenyan format: 0712345678 or +254712345678"
            )
        ],
        help_text="Kenyan phone number"
    )
    
    # === EMPLOYMENT INFORMATION ===
    EMPLOYMENT_TYPES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('casual', 'Casual'),
    ]
    
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text="Company employee ID"
    )
    
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPES,
        default='full_time'
    )
    
    hire_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)
    
    # === ROLE & PERMISSIONS ===
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),      # Full system access
        ('admin', 'Admin'),                   # Manage everything except super admin
        ('manager', 'Manager'),               # Manage store, staff, reports
        ('accountant', 'Accountant'),         # Financial access only
        ('cashier', 'Cashier'),               # POS only
        ('storekeeper', 'Storekeeper'),       # Stock & inventory management
        ('viewer', 'Viewer'),                 # Read-only access
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='cashier',
        help_text="User's role determines permissions"
    )
    
    # === SALARY & COMPENSATION ===
    base_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Monthly base salary in KES"
    )
    
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Commission percentage on sales (0-100)"
    )
    
    # === SHIFT & LOCATION ===
    SHIFT_CHOICES = [
        ('morning', 'Morning (6AM - 2PM)'),
        ('afternoon', 'Afternoon (2PM - 10PM)'),
        ('night', 'Night (10PM - 6AM)'),
        ('flexible', 'Flexible'),
    ]
    
    default_shift = models.CharField(
        max_length=20,
        choices=SHIFT_CHOICES,
        default='morning'
    )
    
    # For multi-store ERP
    # assigned_store = models.ForeignKey('stores.Store', null=True, blank=True, on_delete=models.SET_NULL)
    
    # === STATUS ===
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive users cannot log in"
    )
    
    is_online = models.BooleanField(
        default=False,
        help_text="Currently logged in"
    )
    
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # === NOTES ===
    notes = models.TextField(blank=True, help_text="Internal notes about employee")
    
    # === TIMESTAMPS ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
            models.Index(fields=['employee_id']),
            models.Index(fields=['phone']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
    
    def save(self, *args, **kwargs):
        """Auto-generate employee_id if not set"""
        if not self.employee_id:
            # Generate employee ID like EMP-000001
            last_user = User.objects.exclude(id=self.id).order_by('-id').first()
            if last_user and last_user.employee_id:
                try:
                    last_num = int(last_user.employee_id.split('-')[1])
                    self.employee_id = f"EMP-{last_num + 1:06d}"
                except (IndexError, ValueError):
                    self.employee_id = "EMP-000001"
            else:
                self.employee_id = "EMP-000001"
        super().save(*args, **kwargs)
    
    @property
    def is_cashier(self):
        """Check if user is cashier (for POS permissions)"""
        return self.role == 'cashier'
    
    @property
    def can_manage_products(self):
        """Check if user can manage products"""
        return self.role in ['super_admin', 'admin', 'manager', 'storekeeper']
    
    @property
    def can_view_reports(self):
        """Check if user can view reports"""
        return self.role in ['super_admin', 'admin', 'manager', 'accountant']
    
    @property
    def can_manage_users(self):
        """Check if user can manage other users"""
        return self.role in ['super_admin', 'admin']
    
    @property
    def can_process_refunds(self):
        """Check if user can process refunds"""
        return self.role in ['super_admin', 'admin', 'manager']
    
    def calculate_commission(self, sale_amount):
        """Calculate commission for a sale"""
        return (self.commission_rate / 100) * sale_amount
    
    def update_last_activity(self):
        """Update user's last activity timestamp"""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])
    
    def get_permissions_list(self):
        """Return list of permissions for frontend"""
        permissions = {
            'can_sell': self.is_cashier or self.can_manage_products,
            'can_manage_products': self.can_manage_products,
            'can_view_reports': self.can_view_reports,
            'can_manage_users': self.can_manage_users,
            'can_process_refunds': self.can_process_refunds,
            'can_view_stock': True,  # All active users can view stock
            'can_manage_stock': self.role in ['super_admin', 'admin', 'manager', 'storekeeper'],
        }
        return permissions