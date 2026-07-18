from .models import Product


def cart_count(request):
    """Inject cart item count into every template context."""
    cart = request.session.get('cart', {})
    count = sum(item['quantity'] for item in cart.values())
    return {'cart_count': count}
