from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.core.files import File
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from datetime import timedelta, datetime
from .models import Product, Category, Order, OrderItem, ProductReview, ContactMessage, NewsletterSubscriber, Courier
from pathlib import Path
import os
import json
from functools import wraps

def staff_required(view_func):
    @wraps(view_func)
    def _wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.shortcuts import resolve_url
            from django.conf import settings
            from urllib.parse import urlencode
            path = request.get_full_path()
            login_url = resolve_url(settings.LOGIN_URL)
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(login_url + '?next=' + path)
        if not request.user.is_staff:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)
    return _wrapper

@staff_required
def dashboard_home(request):
    product_count = Product.objects.count()
    category_count = Category.objects.count()
    order_count = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    review_count = ProductReview.objects.filter(is_approved=False).count()
    unread_messages = ContactMessage.objects.filter(is_read=False).count()
    total_revenue = Order.objects.filter(status='delivered').aggregate(Sum('total'))['total__sum'] or 0
    recent_orders = Order.objects.order_by('-created_at')[:5]

    cat_data = Category.objects.annotate(pcount=Count('products')).filter(pcount__gt=0).values('name', 'pcount')
    cat_labels = [c['name'] for c in cat_data]
    cat_counts = [c['pcount'] for c in cat_data]

    today = timezone.now().date()
    last_14 = [today - timedelta(days=i) for i in range(13, -1, -1)]
    order_daily = Order.objects.filter(created_at__gte=last_14[0]) \
        .annotate(date=TruncDate('created_at')) \
        .values('date').annotate(count=Count('id'), rev=Sum('total'))
    od_map = {str(o['date']): {'count': o['count'], 'rev': float(o['rev'] or 0)} for o in order_daily}
    od_labels = [str(d) for d in last_14]
    od_counts = [od_map.get(str(d), {}).get('count', 0) for d in last_14]
    od_revenue = [od_map.get(str(d), {}).get('rev', 0) for d in last_14]

    last_6_months = []
    for i in range(5, -1, -1):
        m = today.month - i
        y = today.year
        while m < 1:
            m += 12
            y -= 1
        last_6_months.append(f'{y}-{m:02d}')
    monthly_revenue = []
    for m in last_6_months:
        y, mo = m.split('-')
        rev = Order.objects.filter(status='delivered', created_at__year=int(y), created_at__month=int(mo)) \
            .aggregate(Sum('total'))['total__sum'] or 0
        monthly_revenue.append(float(rev))

    return render(request, 'dashboard/home.html', {
        'product_count': product_count, 'category_count': category_count,
        'order_count': order_count, 'pending_orders': pending_orders,
        'review_count': review_count, 'unread_messages': unread_messages,
        'total_revenue': total_revenue, 'recent_orders': recent_orders,
        'cat_labels': json.dumps(cat_labels), 'cat_counts': json.dumps(cat_counts),
        'od_labels': json.dumps(od_labels), 'od_counts': json.dumps(od_counts),
        'od_revenue': json.dumps(od_revenue),
        'monthly_labels': json.dumps(last_6_months), 'monthly_revenue': json.dumps(monthly_revenue),
    })

@staff_required
def product_list(request):
    products = Product.objects.select_related('category').all().order_by('-created_at')
    return render(request, 'dashboard/product_list.html', {'products': products})

@staff_required
def product_add(request):
    categories = Category.objects.filter(is_active=True)
    if request.method == 'POST':
        name = request.POST.get('name')
        slug = request.POST.get('slug') or name.lower().replace(' ', '-')
        category_id = request.POST.get('category')
        description = request.POST.get('description', '')
        additional_info = request.POST.get('additional_info', '')
        price = request.POST.get('price')
        compare_price = request.POST.get('compare_price') or None
        stock = request.POST.get('stock', 0)
        is_featured = request.POST.get('is_featured') == 'on'
        is_new = request.POST.get('is_new') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        category = get_object_or_404(Category, id=category_id)
        product = Product.objects.create(
            name=name, slug=slug, category=category,
            description=description, additional_info=additional_info,
            price=price, compare_price=compare_price,
            stock=stock, is_featured=is_featured, is_new=is_new, is_active=is_active,
        )
        if 'image' in request.FILES:
            product.image = request.FILES['image']
            product.save()
        messages.success(request, f'Product "{name}" created!')
        return redirect('dashboard:product_list')
    return render(request, 'dashboard/product_form.html', {'categories': categories, 'action': 'Add'})

@staff_required
def product_edit(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.filter(is_active=True)
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.slug = request.POST.get('slug') or product.name.lower().replace(' ', '-')
        product.category = get_object_or_404(Category, id=request.POST.get('category'))
        product.description = request.POST.get('description', '')
        product.additional_info = request.POST.get('additional_info', '')
        product.price = request.POST.get('price')
        product.compare_price = request.POST.get('compare_price') or None
        product.stock = request.POST.get('stock', 0)
        product.is_featured = request.POST.get('is_featured') == 'on'
        product.is_new = request.POST.get('is_new') == 'on'
        product.is_active = request.POST.get('is_active') == 'on'
        if 'image' in request.FILES:
            product.image = request.FILES['image']
        product.save()
        messages.success(request, f'Product "{product.name}" updated!')
        return redirect('dashboard:product_list')
    return render(request, 'dashboard/product_form.html', {'product': product, 'categories': categories, 'action': 'Edit'})

@staff_required
def product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.delete()
        messages.success(request, f'Product "{product.name}" deleted!')
        return redirect('dashboard:product_list')
    return render(request, 'dashboard/product_confirm_delete.html', {'product': product})

@staff_required
def category_list(request):
    categories = Category.objects.annotate(product_count=Count('products')).all().order_by('name')
    return render(request, 'dashboard/category_list.html', {'categories': categories})

@staff_required
def category_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        slug = request.POST.get('slug') or name.lower().replace(' ', '-')
        is_active = request.POST.get('is_active') == 'on'
        category = Category.objects.create(name=name, slug=slug, is_active=is_active)
        if 'image' in request.FILES:
            category.image = request.FILES['image']
            category.save()
        messages.success(request, f'Category "{name}" created!')
        return redirect('dashboard:category_list')
    return render(request, 'dashboard/category_form.html', {'action': 'Add'})

@staff_required
def category_edit(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.slug = request.POST.get('slug') or category.name.lower().replace(' ', '-')
        category.is_active = request.POST.get('is_active') == 'on'
        if 'image' in request.FILES:
            category.image = request.FILES['image']
        category.save()
        messages.success(request, f'Category "{category.name}" updated!')
        return redirect('dashboard:category_list')
    return render(request, 'dashboard/category_form.html', {'category': category, 'action': 'Edit'})

@staff_required
def category_delete(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category.delete()
        messages.success(request, f'Category "{category.name}" deleted!')
        return redirect('dashboard:category_list')
    return render(request, 'dashboard/category_confirm_delete.html', {'category': category})

@staff_required
def order_list(request):
    status_filter = request.GET.get('status', '')
    orders = Order.objects.all().order_by('-created_at')
    if status_filter:
        orders = orders.filter(status=status_filter)
    return render(request, 'dashboard/order_list.html', {'orders': orders, 'status_filter': status_filter})

@staff_required
def order_detail(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items'), id=order_id)
    if request.method == 'POST':
        if 'update_status' in request.POST and 'status' in request.POST:
            old_status = order.status
            order.status = request.POST.get('status')
            order.save()
            messages.success(request, f'Order #{order.id} status updated to {order.get_status_display()}')
            if old_status != order.status and order.email:
                try:
                    send_mail(
                        subject=f'Order #{order.id} Status Update - SokoyaNguo',
                        message=f'Hi {order.first_name},\n\n'
                                f'Your order #{order.id} status has been updated:\n'
                                f'From: {dict(Order.STATUS_CHOICES).get(old_status, old_status)}\n'
                                f'To: {order.get_status_display()}\n\n'
                                f'Track your order: {request.build_absolute_uri("/track/" + str(order.id) + "/?email=" + order.email)}\n\n'
                                f'Thank you for shopping with SokoyaNguo!',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[order.email],
                    )
                except Exception:
                    pass
            return redirect('dashboard:order_detail', order_id=order.id)

        if 'mark_paid' in request.POST:
            if not order.is_paid:
                order.is_paid = True
                order.paid_at = timezone.now()
                order.save()
                messages.success(request, f'Order #{order.id} marked as paid!')
                if order.email:
                    try:
                        send_mail(
                            subject=f'Payment Confirmed - SokoyaNguo (#{order.id})',
                            message=f'Hi {order.first_name},\n\n'
                                    f'Your payment of Ksh {order.total} has been confirmed!\n'
                                    f'Order #: {order.id}\n'
                                    f'Payment: {order.get_payment_method_display()}\n'
                                    f'Status: {order.get_status_display()}\n\n'
                                    f'Thank you for shopping with SokoyaNguo!',
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[order.email],
                        )
                    except Exception:
                        pass
            return redirect('dashboard:order_detail', order_id=order.id)

        if 'update_tracking' in request.POST:
            had_tracking = bool(order.tracking_number)
            order.courier_name = request.POST.get('courier_name', '')
            order.tracking_number = request.POST.get('tracking_number', '')
            est = request.POST.get('estimated_delivery', '')
            if est:
                from datetime import datetime as dt
                order.estimated_delivery = dt.strptime(est, '%Y-%m-%d').date()
            else:
                order.estimated_delivery = None
            order.save()
            messages.success(request, f'Tracking info updated for Order #{order.id}')
            if order.tracking_number and order.email:
                try:
                    send_mail(
                        subject=f'Order #{order.id} Shipped - SokoyaNguo',
                        message=f'Hi {order.first_name},\n\n'
                                f'Your order #{order.id} has been shipped!\n\n'
                                f'Courier: {order.courier_name}\n'
                                f'Tracking: {order.tracking_number}\n'
                                f'Estimated Delivery: {order.estimated_delivery or "TBD"}\n\n'
                                f'Track your order: {request.build_absolute_uri("/track/" + str(order.id) + "/?email=" + order.email)}\n\n'
                                f'Thank you for shopping with SokoyaNguo!',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[order.email],
                    )
                except Exception:
                    pass
            return redirect('dashboard:order_detail', order_id=order.id)

    return render(request, 'dashboard/order_detail.html', {'order': order, 'couriers': Courier.objects.filter(is_active=True)})

@staff_required
def review_list(request):
    reviews = ProductReview.objects.select_related('product', 'user').all().order_by('-created_at')
    return render(request, 'dashboard/review_list.html', {'reviews': reviews})

@staff_required
def review_approve(request, review_id):
    review = get_object_or_404(ProductReview, id=review_id)
    review.is_approved = True
    review.save()
    messages.success(request, 'Review approved!')
    return redirect('dashboard:review_list')

@staff_required
def review_delete(request, review_id):
    review = get_object_or_404(ProductReview, id=review_id)
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Review deleted!')
        return redirect('dashboard:review_list')
    return render(request, 'dashboard/review_confirm_delete.html', {'review': review})

@staff_required
def contact_list(request):
    contacts = ContactMessage.objects.all().order_by('-created_at')
    return render(request, 'dashboard/contact_list.html', {'contacts': contacts})

@staff_required
def contact_mark_read(request, contact_id):
    contact = get_object_or_404(ContactMessage, id=contact_id)
    contact.is_read = True
    contact.save()
    return redirect('dashboard:contact_list')

@staff_required
def contact_delete(request, contact_id):
    contact = get_object_or_404(ContactMessage, id=contact_id)
    if request.method == 'POST':
        contact.delete()
        messages.success(request, 'Message deleted!')
        return redirect('dashboard:contact_list')
    return render(request, 'dashboard/contact_confirm_delete.html', {'contact': contact})

@staff_required
def subscriber_list(request):
    subscribers = NewsletterSubscriber.objects.all().order_by('-subscribed_at')
    return render(request, 'dashboard/subscriber_list.html', {'subscribers': subscribers})

@staff_required
def courier_list(request):
    couriers = Courier.objects.all().order_by('name')
    return render(request, 'dashboard/courier_list.html', {'couriers': couriers})

@staff_required
def courier_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if name:
            Courier.objects.create(name=name, description=description)
            messages.success(request, f'Courier "{name}" added!')
            return redirect('dashboard:courier_list')
        messages.error(request, 'Courier name is required.')
    return render(request, 'dashboard/courier_form.html', {'courier': None})

@staff_required
def courier_edit(request, courier_id):
    courier = get_object_or_404(Courier, id=courier_id)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if name:
            courier.name = name
            courier.description = description
            courier.save()
            messages.success(request, f'Courier "{name}" updated!')
            return redirect('dashboard:courier_list')
        messages.error(request, 'Courier name is required.')
    return render(request, 'dashboard/courier_form.html', {'courier': courier})

@staff_required
def courier_delete(request, courier_id):
    courier = get_object_or_404(Courier, id=courier_id)
    if request.method == 'POST':
        courier.delete()
        messages.success(request, f'Courier "{courier.name}" deleted!')
        return redirect('dashboard:courier_list')
    return render(request, 'dashboard/courier_confirm_delete.html', {'courier': courier})
