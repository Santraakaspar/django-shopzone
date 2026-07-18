from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/category/<slug:category_slug>/', views.ProductListView.as_view(), name='product_list_by_category'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/<int:product_id>/', views.AddToCartView.as_view(), name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('cart/update/<int:product_id>/', views.UpdateCartView.as_view(), name='update_cart'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('orders/', views.OrderHistoryView.as_view(), name='order_history'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
]
