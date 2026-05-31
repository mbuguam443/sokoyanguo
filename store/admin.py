from django.contrib import admin
from .models import Category, Product, ProductImage, ProductReview, Cart, CartItem, Order, OrderItem, ContactMessage, NewsletterSubscriber, Courier

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductReviewInline(admin.TabularInline):
    model = ProductReview
    extra = 0

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ['product', 'product_name', 'product_price', 'quantity', 'subtotal']
    extra = 0

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'is_featured', 'is_new', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['is_active', 'is_featured', 'is_new', 'category']
    search_fields = ['name', 'description']
    list_editable = ['price', 'stock', 'is_featured', 'is_new', 'is_active']
    inlines = [ProductImageInline, ProductReviewInline]

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'rating', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'rating']
    list_editable = ['is_approved']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'total', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    list_editable = ['status']
    inlines = [OrderItemInline]
    readonly_fields = ['subtotal', 'shipping_cost', 'total', 'created_at']

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'is_read', 'created_at']
    list_filter = ['is_read']
    list_editable = ['is_read']

@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_active', 'subscribed_at']
    list_filter = ['is_active']
    list_editable = ['is_active']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_id', 'item_count', 'total', 'created_at']

admin.site.register(CartItem)
admin.site.register(ProductImage)
admin.site.register(OrderItem)
admin.site.register(Courier)
