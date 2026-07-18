from rest_framework import serializers
from store.models import Product, Category, Order, OrderItem, Review
from django.contrib.auth.models import User


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'product_count']

    def get_product_count(self, obj):
        return obj.products.filter(available=True).count()


class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'username', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'username', 'created_at']


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )
    reviews = ReviewSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    get_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'category', 'category_id',
            'price', 'discount_price', 'get_price', 'discount_percentage',
            'image', 'stock', 'available', 'featured', 'average_rating',
            'reviews', 'created_at',
        ]
        read_only_fields = ['slug', 'created_at']


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product list endpoints."""
    category_name = serializers.CharField(source='category.name', read_only=True)
    get_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'category_name', 'price', 'discount_price',
            'get_price', 'discount_percentage', 'image', 'stock', 'available',
            'featured', 'average_rating',
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_slug', 'quantity', 'price', 'total_price']

    def get_total_price(self, obj):
        return obj.get_total_price()


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'username', 'full_name', 'email', 'phone',
            'address', 'city', 'state', 'pincode', 'status',
            'total_price', 'items', 'created_at',
        ]
        read_only_fields = ['id', 'username', 'status', 'total_price', 'created_at']
