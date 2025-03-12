from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Product, Cart, CartItem, Order


def index(request):
    products = Product.objects.all()
    return render(request, 'shop/index.html', {'products': products})


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'shop/product_detail.html', {'product': product})


@login_required
def cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = CartItem.objects.filter(cart=cart)
    return render(request, 'shop/cart.html', {'items': items})


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('cart')


@login_required
def remove_from_cart(request, product_id):
    cart = Cart.objects.get(user=request.user)
    product = get_object_or_404(Product, id=product_id)
    CartItem.objects.filter(cart=cart, product=product).delete()
    return redirect('cart')


@login_required
def checkout(request):
    cart = Cart.objects.get(user=request.user)
    items = CartItem.objects.filter(cart=cart)
    return render(request, 'shop/checkout.html', {'items': items})


@login_required
def payment_confirmation(request):
    # Логика оплаты заказа
    return render(request, 'shop/payment_confirmation.html')


from django.shortcuts import render

# Create your views here.
