from .models import Cart, Category

def cart_count(request):
    count = 0
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            count = cart.item_count()
    elif request.session.session_key:
        cart = Cart.objects.filter(session_id=request.session.session_key).first()
        if cart:
            count = cart.item_count()
    return {'cart_item_count': count}

def categories(request):
    return {'categories': Category.objects.filter(is_active=True)}
