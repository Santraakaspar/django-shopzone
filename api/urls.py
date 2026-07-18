from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'orders', views.OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    path('cart/', views.CartAPIView.as_view(), name='api-cart'),
    path('auth/', include('rest_framework.urls')),
]
