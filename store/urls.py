from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('shop/', views.shop, name='shop'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('category/<slug:slug>/', views.category_products, name='category_products'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/increase/<int:item_id>/', views.cart_increase, name='cart_increase'),
    path('cart/decrease/<int:item_id>/', views.cart_decrease, name='cart_decrease'),
    path('cart/remove/<int:item_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('order-complete/<int:order_id>/', views.order_complete, name='order_complete'),
    path('contact/', views.contact, name='contact'),
    path('subscribe/', views.subscribe_newsletter, name='subscribe'),
    path('search-autocomplete/', views.search_autocomplete, name='search_autocomplete'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('mpesa/prompt/<int:order_id>/', views.mpesa_prompt, name='mpesa_prompt'),
    path('mpesa/status/<int:order_id>/', views.mpesa_status, name='mpesa_status'),
    path('track/', views.track_order, name='track_order'),
    path('track/<int:order_id>/', views.track_order, name='track_order_detail'),
]
