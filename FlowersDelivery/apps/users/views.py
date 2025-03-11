from decimal import Decimal
from django.shortcuts import render, redirect
from .models import Product, Order
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Автоматически входит после регистрации
            return redirect('index')  # Перенаправляем на главную страницу
    else:
        form = UserCreationForm()
    return render(request, 'shop/register.html', {'form': form})

def index(request):
    products_list = Product.objects.all()
    paginator = Paginator(products_list, 10)  # Показывать 10 товаров на странице
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    return render(request, 'shop/index.html', {'products': products})

def product_detail(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return render(request, 'shop/404.html', status=404)
    return render(request, 'shop/product_detail.html', {'product': product})

@login_required
def cart(request):
    if 'cart' not in request.session:
        request.session['cart'] = []
    cart_items = Product.objects.filter(id__in=request.session['cart'])
    total_price = sum(product.price for product in cart_items)
    return render(request, 'shop/cart.html', {'cart_items': cart_items, 'total_price': total_price})

@login_required
def add_to_cart(request, product_id):
    if 'cart' not in request.session:
        request.session['cart'] = []
    if product_id not in request.session['cart']:
        request.session['cart'].append(product_id)
        request.session.modified = True
    return redirect('cart')

@login_required
def remove_from_cart(request, product_id):
    if 'cart' in request.session:
        request.session['cart'] = [item for item in request.session['cart'] if item != product_id]
        request.session.modified = True
    return redirect('cart')

@login_required
def checkout(request):
    if request.method == 'POST':
        # Создаем заказ
        order = Order.objects.create(
            user=request.user,
            total_price=Decimal('0.00')  # Заглушка, пока не считаем общую стоимость
        )
        # Добавляем товары из корзины в заказ
        cart_items = Product.objects.filter(id__in=request.session.get('cart', []))
        for product in cart_items:
            order.products.add(product)
            order.total_price += product.price
        order.save()
        # Очищаем корзину
        request.session['cart'] = []
        # Перенаправляем на страницу подтверждения оплаты
        return redirect('payment_confirmation')

    # Если метод GET, просто отображаем страницу оформления заказа
    cart_items = Product.objects.filter(id__in=request.session.get('cart', []))
    total_price = sum(product.price for product in cart_items)
    return render(request, 'shop/checkout.html', {'total_price': total_price})

@login_required
def payment_confirmation(request):
    return render(request, 'shop/payment_confirmation.html')
