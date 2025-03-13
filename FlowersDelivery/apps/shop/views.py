from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Cart, CartItem, Order, OrderItem, TelegramUser, TelegramNotification
from django.core.paginator import Paginator
import time


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
    cart_items = CartItem.objects.filter(cart=cart)
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'shop/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)

    # Проверяем, есть ли товар в корзине
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )

    # Если товар уже был в корзине, увеличиваем количество
    if not item_created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('cart')


@login_required
def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart.objects.get(user=request.user)

    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        cart_item.delete()
    except CartItem.DoesNotExist:
        pass

    return redirect('cart')


#предложенные улучшения использования сообщений
# @login_required
# def checkout(request):
#     cart, created = Cart.objects.get_or_create(user=request.user)
#     cart_items = CartItem.objects.filter(cart=cart)
#     total_price = sum(item.product.price * item.quantity for item in cart_items)
#
#     if request.method == 'POST':
#         if not cart_items.exists():
#             messages.error(request, 'Ваша корзина пуста')
#             return redirect('cart')
#
#         address = request.POST.get('address', '')
#         if not address:
#             messages.error(request, 'Укажите адрес доставки')
#             return render(request, 'shop/checkout.html', {
#                 'cart_items': cart_items,
#                 'total_price': total_price
#             })
#
#         try:
#             # Создаем заказ
#             order = Order.objects.create(
#                 user=request.user,
#                 address=address,
#                 order_key=f"ORDER-{request.user.id}-{int(time.time())}"[:20],
#                 status='pending',
#                 total_price=total_price  # Добавьте это для корректного расчета
#             )
#
#             # Добавляем товары через OrderItem
#             for cart_item in cart_items:
#                 OrderItem.objects.create(
#                     order=order,
#                     product=cart_item.product,
#                     quantity=cart_item.quantity,
#                     price=cart_item.product.price
#                 )
#
#             # Очищаем корзину
#             cart_items.delete()
#
#             messages.success(request, 'Заказ успешно оформлен!')
#             return redirect('payment_confirmation')
#
#         except Exception as e:
#             messages.error(request, f'Ошибка при оформлении заказа: {str(e)}')
#
#     return render(request, 'shop/checkout.html', {
#         'cart_items': cart_items,
#         'total_price': total_price
#
#     })
#
@login_required
def payment_confirmation(request):
    # Логика оплаты заказа
    return render(request, 'shop/payment_confirmation.html')  # Обратите внимание на 'shop/'


@login_required
def checkout(request):
    # Проверяем, привязан ли Telegram
    telegram_connected = TelegramUser.objects.filter(user=request.user).exists()

    if not telegram_connected:
        messages.warning(request, "Чтобы получать уведомления о заказах, привяжите ваш Telegram в профиле.")

    # Получаем корзину пользователя
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    if request.method == 'POST':
        if not cart_items.exists():
            messages.error(request, 'Ваша корзина пуста')
            return redirect('cart')

        address = request.POST.get('address', '')
        if not address:
            messages.error(request, 'Укажите адрес доставки')
            return render(request, 'shop/checkout.html', {
                'cart_items': cart_items,
                'total_price': total_price
            })

        try:
            # Создаем заказ
            order = Order.objects.create(
                user=request.user,
                address=address,
                order_key=f"ORDER-{request.user.id}-{int(time.time())}"[:20],
                status='pending',
                total_price=total_price
            )
            # order.save() - не нужно, так как Order.objects.create() уже сохраняет объект

            # Добавляем товары через OrderItem
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price
                )

            # Очищаем корзину
            cart_items.delete()

            # Сообщение об успешном оформлении (объединенное)
            messages.success(request, "Заказ успешно оформлен! Проверьте уведомление в Telegram.")

            return redirect('payment', order_id=order.id)  # Перенаправляем на страницу оплаты

        except Exception as e:
            messages.error(request, f'Ошибка при оформлении заказа: {str(e)}')

    # Отображаем страницу оформления заказа при GET-запросе
    return render(request, 'shop/checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })
# def checkout(request):
#     # Получаем корзину пользователя
#     cart, created = Cart.objects.get_or_create(user=request.user)
#     cart_items = CartItem.objects.filter(cart=cart)
#
#     # Считаем общую стоимость
#     total_price = sum(item.product.price * item.quantity for item in cart_items)
#
#     if request.method == 'POST':
#         # Проверяем, что корзина не пуста
#         if cart_items.exists():
#             # Получаем адрес доставки из формы
#             address = request.POST.get('address', '')
#
#             # Проверяем, что адрес указан
#             if not address:
#                 # Возвращаемся на форму с сообщением об ошибке
#                 return render(request, 'shop/checkout.html', {
#                     'items': cart_items,  # Для совместимости с обоими шаблонами
#                     'cart_items': cart_items,
#                     'total_price': total_price,
#                     'error': 'Укажите адрес доставки'
#                 })
#
#             # Создаем заказ
#             order = Order.objects.create(
#                 user=request.user,
#                 address=address,
#                 order_key=f"ORDER-{request.user.id}-{int(time.time())}"[:20],
#                 status='pending'
#             )
#
#             # Добавляем товары через OrderItem
#             for cart_item in cart_items:
#                 OrderItem.objects.create(
#                     order=order,
#                     product=cart_item.product,
#                     quantity=cart_item.quantity,
#                     price=cart_item.product.price
#                 )
#
#             # Очищаем корзину
#             cart_items.delete()
#
#             # Перенаправляем на страницу подтверждения
#             return redirect('payment_confirmation')
#
#     # Отображаем страницу оформления заказа
#     return render(request, 'shop/checkout.html', {
#         'items': cart_items,  # Для совместимости с обоими шаблонами
#         'cart_items': cart_items,
#         'total_price': total_price

@login_required
def payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == 'POST':
        # Логика обработки платежа
        order.payment_status = 'completed'
        order.save()

        messages.success(request, 'Платеж успешно завершен!')
        return redirect('order_detail', order_id=order.id)

    return render(request, 'shop/payment.html', {'order': order})