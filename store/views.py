from decimal import Decimal
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.db.models import Avg
from django.http import JsonResponse
from django.conf import settings
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Category, Product, Cart, CartItem, Order, OrderItem
from .forms import ReviewForm, ContactForm, CheckoutForm

def home(request):
    featured = Product.objects.filter(is_featured=True, is_active=True)[:8]
    new_products = Product.objects.filter(is_new=True, is_active=True)[:8]
    home_categories = Category.objects.filter(is_active=True)[:6]
    return render(request, 'index.html', {
        'home_categories': home_categories,
        'featured_products': featured,
        'new_products': new_products,
    })

def shop(request):
    category_slug = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort = request.GET.get('sort', '-created_at')
    search = request.GET.get('q', '')

    products = Product.objects.filter(is_active=True)

    if category_slug:
        products = products.filter(category__slug=category_slug)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    if search:
        products = products.filter(Q(name__icontains=search) | Q(description__icontains=search))

    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'popularity':
        products = products.annotate(order_count=Count('orderitem')).order_by('-order_count')
    else:
        products = products.order_by('-created_at')

    paginator = Paginator(products, 9)
    page = request.GET.get('page', 1)
    products_page = paginator.get_page(page)

    return render(request, 'shop.html', {
        'products': products_page,
        'selected_category': category_slug,
        'sort': sort,
        'search': search,
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id)[:8]

    if request.method == 'POST' and request.user.is_authenticated:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.name = request.user.get_full_name() or request.user.username
            review.email = request.user.email
            review.save()
            messages.success(request, 'Your review has been submitted!')
            return redirect('store:product_detail', slug=slug)
    else:
        form = ReviewForm()

    reviews = product.reviews.filter(is_approved=True)
    return render(request, 'product_detail.html', {
        'product': product,
        'related_products': related,
        'form': form,
        'reviews': reviews,
    })

def cart_view(request):
    cart = _get_cart(request)
    return render(request, 'cart.html', {'cart': cart})

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = _get_cart(request)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': 1})
    if not created:
        cart_item.quantity += 1
        cart_item.save()
        messages.info(request, f'Increased {product.name} quantity to {cart_item.quantity}')
    else:
        messages.success(request, f'{product.name} added to cart!')
    return redirect(request.META.get('HTTP_REFERER', 'store:cart'))

def _get_item(request, item_id):
    return get_object_or_404(CartItem, id=item_id, cart=_get_cart(request))

def cart_increase(request, item_id):
    item = _get_item(request, item_id)
    item.quantity += 1
    item.save()
    return redirect('store:cart')

def cart_decrease(request, item_id):
    item = _get_item(request, item_id)
    item.quantity -= 1
    if item.quantity <= 0:
        item.delete()
    else:
        item.save()
    return redirect('store:cart')

def cart_remove(request, item_id):
    item = _get_item(request, item_id)
    item.delete()
    return redirect('store:cart')

def checkout(request):
    cart = _get_cart(request)
    if cart.item_count() == 0:
        messages.warning(request, 'Your cart is empty!')
        return redirect('store:shop')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            subtotal = cart.total()
            shipping_cost = Decimal('1.00')
            total = subtotal + shipping_cost
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                first_name=data['first_name'], last_name=data['last_name'], email=data['email'],
                phone=data['phone'], address_line1=data['address_line1'],
                address_line2=data.get('address_line2', ''), country=data['country'],
                city=data['city'], state=data['state'], zip_code=data['zip_code'],
                shipping_to_different=data.get('shipping_to_different', False),
                shipping_first_name=data.get('shipping_first_name', ''),
                shipping_last_name=data.get('shipping_last_name', ''),
                shipping_email=data.get('shipping_email', ''),
                shipping_phone=data.get('shipping_phone', ''),
                shipping_address_line1=data.get('shipping_address_line1', ''),
                shipping_address_line2=data.get('shipping_address_line2', ''),
                shipping_country=data.get('shipping_country', ''),
                shipping_city=data.get('shipping_city', ''),
                shipping_state=data.get('shipping_state', ''),
                shipping_zip_code=data.get('shipping_zip_code', ''),
                payment_method=data.get('payment_method', 'direct_check'),
                mpesa_phone=data.get('mpesa_phone', ''),
                subtotal=subtotal, shipping_cost=shipping_cost, total=total,
            )
            for cart_item in cart.items.all():
                OrderItem.objects.create(order=order, product=cart_item.product,
                    product_name=cart_item.product.name, product_price=cart_item.product.price,
                    quantity=cart_item.quantity, subtotal=cart_item.subtotal())
            cart.items.all().delete()

            try:
                send_mail(
                    subject=f'Order Confirmation - SokoyaNguo (#{order.id})',
                    message=f'Hi {order.first_name},\n\n'
                            f'Your order has been placed successfully!\n\n'
                            f'Order #: {order.id}\n'
                            f'Total: Ksh {order.total}\n'
                            f'Payment: {order.get_payment_method_display()}\n'
                            f'Status: {order.get_status_display()}\n\n'
                            f'We will notify you when your order status changes.\n\n'
                            f'Thank you for shopping with SokoyaNguo!',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[order.email],
                )
            except Exception:
                pass

            if data.get('payment_method') == 'mpesa' and data.get('mpesa_phone'):
                from .mpesa import stk_push
                callback_url = settings.MPESA_CALLBACK_URL
                try:
                    response = stk_push(data['mpesa_phone'], int(total), order.id, callback_url)
                    if response.get('ResponseCode') == '0':
                        order.mpesa_request_id = response.get('CheckoutRequestID', '')
                        order.save()
                        return redirect('store:mpesa_prompt', order_id=order.id)
                except Exception as e:
                    pass
            messages.success(request, 'Order placed successfully!')
            return redirect('store:order_complete', order_id=order.id)
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {'first_name': request.user.first_name, 'last_name': request.user.last_name, 'email': request.user.email}
        form = CheckoutForm(initial=initial)
    return render(request, 'checkout.html', {'form': form, 'cart': cart})

def order_complete(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'order_complete.html', {'order': order})

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_msg = form.save()
            try:
                send_mail(
                    subject=f'Contact Form: {contact_msg.subject}',
                    message=f'From: {contact_msg.name} ({contact_msg.email})\n\n{contact_msg.message}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=settings.CONTACT_EMAIL,
                )
            except Exception:
                pass
            messages.success(request, 'Your message has been sent! We will get back to you soon.')
            return redirect('store:contact')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})

def subscribe_newsletter(request):
    if request.method == 'POST':
        email = request.POST.get('email', '')
        name = request.POST.get('name', '')
        if email:
            from .models import NewsletterSubscriber
            NewsletterSubscriber.objects.get_or_create(email=email, defaults={'name': name})
            messages.success(request, 'Subscribed successfully!')
    return redirect(request.META.get('HTTP_REFERER', 'store:home'))

def category_products(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = Product.objects.filter(category=category, is_active=True).order_by('-created_at')
    paginator = Paginator(products, 9)
    page = request.GET.get('page', 1)
    products_page = paginator.get_page(page)
    return render(request, 'shop.html', {
        'products': products_page,
        'selected_category': slug,
        'category': category,
        'sort': '-created_at',
        'search': '',
    })

def search_autocomplete(request):
    q = request.GET.get('q', '')
    if len(q) < 2:
        return JsonResponse({'results': []})
    products = Product.objects.filter(
        Q(name__icontains=q) | Q(description__icontains=q),
        is_active=True
    )[:6]
    results = [{
        'id': p.id,
        'name': p.name,
        'price': str(p.price),
        'image': p.image.url,
        'slug': p.slug,
    } for p in products]
    return JsonResponse({'results': results})

def _get_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.save()
        cart, created = Cart.objects.get_or_create(session_id=request.session.session_key)
    return cart

@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            stk_callback = data.get('Body', {}).get('stkCallback', {})
            result_code = stk_callback.get('ResultCode', 1)
            checkout_request_id = stk_callback.get('CheckoutRequestID', '')
            result_desc = stk_callback.get('ResultDesc', '')

            order = Order.objects.filter(mpesa_request_id=checkout_request_id).first()
            if order:
                if result_code == 0:
                    metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
                    txn_id = ''
                    for item in metadata:
                        if item.get('Name') == 'MpesaReceiptNumber':
                            txn_id = item.get('Value', '')
                            break
                    order.mpesa_transaction_id = txn_id
                    order.status = 'processing'
                    order.save()
                    if order.email:
                        try:
                            send_mail(
                                subject=f'Payment Confirmed - SokoyaNguo (#{order.id})',
                                message=f'Hi {order.first_name},\n\n'
                                        f'Your M-Pesa payment of Ksh {order.total} has been received!\n'
                                        f'Transaction ID: {txn_id}\n\n'
                                        f'Order #: {order.id}\n'
                                        f'Status: Processing\n\n'
                                        f'We will notify you when your order ships.\n\n'
                                        f'Thank you for shopping with SokoyaNguo!',
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[order.email],
                            )
                        except Exception:
                            pass
                else:
                    order.status = 'cancelled'
                    order.notes = result_desc
                    order.save()
        except Exception:
            pass
    return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})

def mpesa_prompt(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'mpesa_prompt.html', {'order': order})

def mpesa_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return JsonResponse({
        'status': order.status,
        'mpesa_transaction_id': order.mpesa_transaction_id,
    })

def track_order(request, order_id=None):
    if order_id:
        order = get_object_or_404(Order, id=order_id)
        email = request.GET.get('email', '')
        if order.email.lower() != email.lower():
            return render(request, 'track_order.html', {'order': None, 'error': 'Invalid order ID or email.'})

        if request.method == 'POST' and request.POST.get('confirm_delivery'):
            if order.status == 'shipped':
                order.status = 'delivered'
                order.save()
                messages.success(request, 'Delivery confirmed! Thank you for shopping with SokoyaNguo.')
                try:
                    send_mail(
                        subject=f'Order #{order.id} Delivered - SokoyaNguo',
                        message=f'Order #{order.id} has been confirmed as delivered by {order.first_name}.\n\n'
                                f'Customer: {order.first_name} {order.last_name}\n'
                                f'Email: {order.email}',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=settings.CONTACT_EMAIL,
                    )
                except Exception:
                    pass
            return redirect('store:track_order_detail', order_id=order.id)

        return render(request, 'track_order.html', {'order': order})
    return render(request, 'track_order.html', {'order': None})
