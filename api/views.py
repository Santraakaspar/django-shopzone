from rest_framework import viewsets, generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.decorators import action
from django.db.models import Q
from store.models import Product, Category, Order, OrderItem
from .serializers import (
    ProductSerializer, ProductListSerializer,
    CategorySerializer, OrderSerializer
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve product categories.
    GET /api/categories/
    GET /api/categories/{id}/
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve products with search and category filter.
    GET /api/products/
    GET /api/products/{slug}/
    GET /api/products/?search=laptop
    GET /api/products/?category=electronics
    GET /api/products/featured/
    """
    queryset = Product.objects.filter(available=True)
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if category:
            queryset = queryset.filter(category__slug=category)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        return queryset

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """GET /api/products/featured/ — Return featured products."""
        featured = self.get_queryset().filter(featured=True)
        serializer = ProductListSerializer(featured, many=True, context={'request': request})
        return Response(serializer.data)


class CartAPIView(APIView):
    """
    Session-based cart API.
    GET  /api/cart/       — View cart
    POST /api/cart/add/   — Add item {product_id, quantity}
    POST /api/cart/remove/ — Remove item {product_id}
    POST /api/cart/clear/ — Clear cart
    """

    def _get_cart_data(self, request):
        cart = request.session.get('cart', {})
        items = []
        total = 0
        for product_id, item in cart.items():
            try:
                product = Product.objects.get(pk=int(product_id), available=True)
                subtotal = float(product.get_price) * item['quantity']
                total += subtotal
                items.append({
                    'product_id': product.pk,
                    'name': product.name,
                    'price': float(product.get_price),
                    'quantity': item['quantity'],
                    'subtotal': subtotal,
                })
            except Product.DoesNotExist:
                pass
        return {'items': items, 'total': round(total, 2), 'item_count': len(items)}

    def get(self, request):
        return Response(self._get_cart_data(request))

    def post(self, request):
        action = request.data.get('action')
        if action == 'add':
            product_id = request.data.get('product_id')
            quantity = int(request.data.get('quantity', 1))
            try:
                product = Product.objects.get(pk=product_id, available=True)
                cart = request.session.get('cart', {})
                key = str(product_id)
                if key in cart:
                    cart[key]['quantity'] += quantity
                else:
                    cart[key] = {'quantity': quantity}
                request.session['cart'] = cart
                return Response({'message': f'Added {product.name} to cart', 'cart': self._get_cart_data(request)})
            except Product.DoesNotExist:
                return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        elif action == 'remove':
            product_id = str(request.data.get('product_id'))
            cart = request.session.get('cart', {})
            cart.pop(product_id, None)
            request.session['cart'] = cart
            return Response({'message': 'Item removed', 'cart': self._get_cart_data(request)})

        elif action == 'clear':
            request.session['cart'] = {}
            return Response({'message': 'Cart cleared'})

        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)


class OrderViewSet(viewsets.ModelViewSet):
    """
    CRUD for orders. Requires authentication.
    GET  /api/orders/     — List user's orders
    POST /api/orders/     — Place a new order from current cart
    GET  /api/orders/{id}/ — Order detail
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items__product')

    def create(self, request, *args, **kwargs):
        cart = request.session.get('cart', {})
        if not cart:
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        total = 0
        order_items_data = []
        for product_id, item in cart.items():
            try:
                product = Product.objects.get(pk=int(product_id), available=True)
                subtotal = product.get_price * item['quantity']
                total += subtotal
                order_items_data.append({'product': product, 'quantity': item['quantity'], 'price': product.get_price})
            except Product.DoesNotExist:
                pass

        order = serializer.save(user=request.user, total_price=total)
        for item_data in order_items_data:
            OrderItem.objects.create(order=order, **item_data)

        request.session['cart'] = {}
        return Response(self.get_serializer(order).data, status=status.HTTP_201_CREATED)
