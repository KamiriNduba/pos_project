from rest_framework import serializers
from .models import Category, Supplier, Product, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.SerializerMethodField()
    children_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'parent', 'parent_name',
            'is_active', 'children_count', 'created_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at']

    def get_parent_name(self, obj):
        return obj.parent.name if obj.parent else None

    def get_children_count(self, obj):
        return Category.objects.filter(parent=obj, is_active=True).count()


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'code', 'contact_person', 'phone', 'email',
            'address', 'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'code', 'created_at', 'updated_at']


class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'image_url', 'caption', 'is_primary', 'order']
        read_only_fields = ['id']

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()
    supplier_name = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True, read_only=True)

    price = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()
    base_unit_name = serializers.CharField(source='unit', read_only=True)
    image_url = serializers.SerializerMethodField()

    profit_margin = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()
    stock_value = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'uuid', 'sku', 'barcode', 'name', 'description',
            'category', 'category_name', 'supplier', 'supplier_name',
            'cost_price', 'retail_price', 'wholesale_price',
            'stock_quantity', 'reorder_level', 'reorder_quantity',
            'unit', 'tax_rate', 'is_active', 'is_featured', 'main_image',
            'price', 'quantity', 'base_unit_name', 'image_url',
            'profit_margin', 'is_low_stock', 'stock_value',
            'created_at', 'updated_at',
            'images',
        ]
        read_only_fields = [
            'id', 'uuid', 'sku', 'created_at', 'updated_at',
            'price', 'quantity', 'base_unit_name', 'image_url',
            'profit_margin', 'is_low_stock', 'stock_value',
        ]

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_supplier_name(self, obj):
        return obj.supplier.name if obj.supplier else None

    def get_price(self, obj):
        return float(obj.retail_price)

    def get_quantity(self, obj):
        return float(obj.stock_quantity)

    def get_image_url(self, obj):
        if obj.main_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.main_image.url)
            return obj.main_image.url
        return None

    def get_profit_margin(self, obj):
        if obj.cost_price and obj.cost_price > 0:
            return round(float((obj.retail_price - obj.cost_price) / obj.cost_price * 100), 2)
        return 0.0

    def get_is_low_stock(self, obj):
        if obj.reorder_level and obj.reorder_level > 0:
            return obj.stock_quantity <= obj.reorder_level
        return False

    def get_stock_value(self, obj):
        return float(obj.stock_quantity * obj.cost_price)

    def validate_retail_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Retail price must be greater than zero")
        return value


class ProductImportSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        if not value.name.endswith(('.xlsx', '.xls', '.csv')):
            raise serializers.ValidationError("File must be Excel or CSV format")
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size must be less than 10MB")
        return value


class BulkPriceUpdateSerializer(serializers.Serializer):
    product_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    category_id = serializers.IntegerField(required=False)
    supplier_id = serializers.IntegerField(required=False)
    update_type = serializers.ChoiceField(choices=['percentage', 'fixed'])
    adjustment = serializers.DecimalField(max_digits=10, decimal_places=2)
    price_field = serializers.ChoiceField(
        choices=['retail_price', 'wholesale_price', 'cost_price'],
        default='retail_price'
    )

    def validate(self, data):
        if not data.get('product_ids') and not data.get('category_id') and not data.get('supplier_id'):
            raise serializers.ValidationError(
                "Either product_ids, category_id, or supplier_id must be provided"
            )
        return data
