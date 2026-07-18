from django.contrib import admin
from .models import Category, Product, Review, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'discount_price', 'stock', 'available', 'featured', 'created_at']
    list_filter = ['available', 'featured', 'category', 'created_at']
    list_editable = ['price', 'stock', 'available', 'featured']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Info', {'fields': ('name', 'slug', 'category', 'description', 'image')}),
        ('Pricing & Stock', {'fields': ('price', 'discount_price', 'stock', 'available', 'featured')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['product__name', 'user__username']
    readonly_fields = ['product', 'user', 'created_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'full_name', 'status', 'total_price', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['full_name', 'email', 'user__username']
    list_editable = ['status']
    readonly_fields = ['user', 'total_price', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    fieldsets = (
        ('Order Info', {'fields': ('user', 'status', 'total_price')}),
        ('Customer Details', {'fields': ('full_name', 'email', 'phone')}),
        ('Shipping Address', {'fields': ('address', 'city', 'state', 'pincode')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price']
    readonly_fields = ['order', 'product', 'quantity', 'price']
