from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Product, Cart, CartItem, Order
from django.core.paginator import Paginator


def index(request):
    products = Product.objects.all()
    return render(request, 'shop/index.html', {'products': products})

def catalog(request):
    products_list = Product.objects.all()

    search_query = request.GET.get('search', '')
    if search_query:
        products_list = products_list.filter(name__icontains=search_query)

    paginator = Paginator( products_list, 10)  # Показывать 10 цветов на странице
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    return render(request, 'shop/catalog.html', {'products': products})


def product_detail(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return render(request, '404.html', status=404)
    return render(request, 'shop/product_detail.html', {'product': product})


@login_required
def cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = CartItem.objects.filter(cart=cart)
    return render(request, 'shop/cart.html', {'items': items})


@login_required
def add_to_cart(request, product_id):
   if 'cart' not in request.session:
       request.session['cart'] = []
   if product_id not in request.session['cart']:
        request.session['cart'].append(product_id)
        request.session.modified = True
   return redirect('shop/cart')


@login_required
def remove_from_cart(request, product_id):
    if 'cart' in request.session:
        request.session['cart'] = [item for item in request.session['cart'] if item != product_id]
        request.session.modified = True
    return redirect('shop/cart')
# def remove_from_cart(request, product_id):
    # cart = Cart.objects.get(user=request.user)
    # product = get_object_or_404(Product, id=product_id)
    # CartItem.objects.filter(cart=cart, product=product).delete()
    # return redirect('cart')

# @login_required
# def checkout(request):
    # cart = Cart.objects.get(user=request.user)
    # items = CartItem.objects.filter(cart=cart)
    # return render(request, 'shop/checkout.html', {'items': items})

@login_required
def checkout(request):
    if request.method == 'POST':
        # Создаем заказ
        order = Order.objects.create(
            user=request.user,
            total_price=Decimal('0.00')  # Заглушка, пока не считаем общую стоимость
        )
        # Добавляем продукты из корзины в заказ
        cart_items = Product.objects.filter(id__in=request.session.get('cart', []))
        for product in cart_items:
            order.products.add(product)
            order.total_price += product.price
        order.save()
        # Очищаем корзину
        request.session['cart'] = []
        # Перенаправляем на страницу подтверждения оплаты
        return redirect('shop/payment_confirmation')

    # Если метод GET, просто отображаем страницу оформления заказа
    cart_items = Product.objects.filter(id__in=request.session.get('cart', []))
    total_price = sum(product.price for product in cart_items)
    return render(request, 'shop/checkout.html', {'total_price': total_price})


@login_required
def payment_confirmation(request):
    # Логика оплаты заказа
    return render(request, 'shop/payment_confirmation.html')

