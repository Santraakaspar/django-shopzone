from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from .models import Product, Category, Order, OrderItem, Review
from .forms import CheckoutForm, ReviewForm


# ──────────────────────────────────────────
# Home Page
# ──────────────────────────────────────────
class HomeView(View):
    def get(self, request):
        featured_products = Product.objects.filter(available=True, featured=True)[:8]
        all_products = Product.objects.filter(available=True)[:12]
        categories = Category.objects.all()
        context = {
            'featured_products': featured_products,
            'all_products': all_products,
            'categories': categories,
        }
        return render(request, 'store/home.html', context)


# ──────────────────────────────────────────
# Product List (with category filter)
# ──────────────────────────────────────────
class ProductListView(ListView):
    model = Product
    template_name = 'store/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(available=True)
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            self.category = get_object_or_404(Category, slug=category_slug)
            queryset = queryset.filter(category=self.category)
        else:
            self.category = None
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['current_category'] = self.category
        return context


# ──────────────────────────────────────────
# Product Detail
# ──────────────────────────────────────────
class ProductDetailView(DetailView):
    model = Product
    template_name = 'store/product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context['review_form'] = ReviewForm()
        context['reviews'] = product.reviews.all()
        context['related_products'] = Product.objects.filter(
            category=product.category, available=True
        ).exclude(pk=product.pk)[:4]
        context['user_reviewed'] = (
            self.request.user.is_authenticated and
            Review.objects.filter(product=product, user=self.request.user).exists()
        )
        return context

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to submit a review.')
            return redirect('accounts:login')
        product = self.get_object()
        if Review.objects.filter(product=product, user=request.user).exists():
            messages.warning(request, 'You have already reviewed this product.')
            return redirect(product.get_absolute_url())
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, 'Review submitted successfully!')
        return redirect(product.get_absolute_url())


# ──────────────────────────────────────────
# Search
# ──────────────────────────────────────────
class SearchView(View):
    def get(self, request):
        query = request.GET.get('q', '')
        products = Product.objects.none()
        if query:
            products = Product.objects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query),
                available=True
            ).distinct()
        context = {'products': products, 'query': query}
        return render(request, 'store/search_results.html', context)


# ──────────────────────────────────────────
# Cart (Session-based)
# ──────────────────────────────────────────
class CartView(View):
    def get(self, request):
        cart = request.session.get('cart', {})
        cart_items = []
        total = 0
        for product_id, item in cart.items():
            try:
                product = Product.objects.get(pk=int(product_id))
                subtotal = product.get_price * item['quantity']
                total += subtotal
                cart_items.append({
                    'product': product,
                    'quantity': item['quantity'],
                    'subtotal': subtotal,
                })
            except Product.DoesNotExist:
                pass
        return render(request, 'store/cart.html', {'cart_items': cart_items, 'total': total})


class AddToCartView(View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id, available=True)
        cart = request.session.get('cart', {})
        key = str(product_id)
        quantity = int(request.POST.get('quantity', 1))
        if key in cart:
            cart[key]['quantity'] += quantity
        else:
            cart[key] = {'quantity': quantity}
        request.session['cart'] = cart
        messages.success(request, f'"{product.name}" added to cart!')
        return redirect(request.META.get('HTTP_REFERER', '/'))


class RemoveFromCartView(View):
    def post(self, request, product_id):
        cart = request.session.get('cart', {})
        cart.pop(str(product_id), None)
        request.session['cart'] = cart
        messages.info(request, 'Item removed from cart.')
        return redirect('store:cart')


class UpdateCartView(View):
    def post(self, request, product_id):
        cart = request.session.get('cart', {})
        key = str(product_id)
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0 and key in cart:
            cart[key]['quantity'] = quantity
        elif quantity <= 0:
            cart.pop(key, None)
        request.session['cart'] = cart
        return redirect('store:cart')


# ──────────────────────────────────────────
# Checkout & Orders
# ──────────────────────────────────────────
class CheckoutView(LoginRequiredMixin, View):
    def get(self, request):
        cart = request.session.get('cart', {})
        if not cart:
            messages.warning(request, 'Your cart is empty.')
            return redirect('store:cart')
        cart_items, total = self._get_cart_data(cart)
        form = CheckoutForm(initial={
            'full_name': request.user.get_full_name(),
            'email': request.user.email,
        })
        return render(request, 'store/checkout.html', {
            'form': form, 'cart_items': cart_items, 'total': total
        })

    def post(self, request):
        cart = request.session.get('cart', {})
        if not cart:
            return redirect('store:cart')
        cart_items, total = self._get_cart_data(cart)
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.total_price = total
            order.save()
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    quantity=item['quantity'],
                    price=item['product'].get_price,
                )
            request.session['cart'] = {}
            messages.success(request, f'Order #{order.pk} placed successfully! 🎉')
            return redirect('store:order_detail', pk=order.pk)
        return render(request, 'store/checkout.html', {
            'form': form, 'cart_items': cart_items, 'total': total
        })

    def _get_cart_data(self, cart):
        cart_items, total = [], 0
        for product_id, item in cart.items():
            try:
                product = Product.objects.get(pk=int(product_id))
                subtotal = product.get_price * item['quantity']
                total += subtotal
                cart_items.append({'product': product, 'quantity': item['quantity'], 'subtotal': subtotal})
            except Product.DoesNotExist:
                pass
        return cart_items, total


class OrderHistoryView(LoginRequiredMixin, ListView):
    template_name = 'store/order_history.html'
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items__product')


class OrderDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)
        return render(request, 'store/order_detail.html', {'order': order})
