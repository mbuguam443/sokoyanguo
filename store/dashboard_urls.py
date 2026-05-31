from django.urls import path
from . import dashboard_views

app_name = 'dashboard'

urlpatterns = [
    path('', dashboard_views.dashboard_home, name='dashboard_home'),
    path('products/', dashboard_views.product_list, name='product_list'),
    path('products/add/', dashboard_views.product_add, name='product_add'),
    path('products/<int:product_id>/edit/', dashboard_views.product_edit, name='product_edit'),
    path('products/<int:product_id>/delete/', dashboard_views.product_delete, name='product_delete'),
    path('categories/', dashboard_views.category_list, name='category_list'),
    path('categories/add/', dashboard_views.category_add, name='category_add'),
    path('categories/<int:category_id>/edit/', dashboard_views.category_edit, name='category_edit'),
    path('categories/<int:category_id>/delete/', dashboard_views.category_delete, name='category_delete'),
    path('orders/', dashboard_views.order_list, name='order_list'),
    path('orders/<int:order_id>/', dashboard_views.order_detail, name='order_detail'),
    path('reviews/', dashboard_views.review_list, name='review_list'),
    path('reviews/<int:review_id>/approve/', dashboard_views.review_approve, name='review_approve'),
    path('reviews/<int:review_id>/delete/', dashboard_views.review_delete, name='review_delete'),
    path('contacts/', dashboard_views.contact_list, name='contact_list'),
    path('contacts/<int:contact_id>/mark-read/', dashboard_views.contact_mark_read, name='contact_mark_read'),
    path('contacts/<int:contact_id>/delete/', dashboard_views.contact_delete, name='contact_delete'),
    path('subscribers/', dashboard_views.subscriber_list, name='subscriber_list'),
    path('couriers/', dashboard_views.courier_list, name='courier_list'),
    path('couriers/add/', dashboard_views.courier_add, name='courier_add'),
    path('couriers/<int:courier_id>/edit/', dashboard_views.courier_edit, name='courier_edit'),
    path('couriers/<int:courier_id>/delete/', dashboard_views.courier_delete, name='courier_delete'),
]
