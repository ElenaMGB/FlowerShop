from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
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



@login_required
def checkout(request):
    # Получаем корзину пользователя
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)

    # Считаем общую стоимость
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    if request.method == 'POST':
        # Проверяем, что корзина не пуста
        if cart_items.exists():
            # Получаем адрес доставки из формы
            address = request.POST.get('address', '')

            # Проверяем, что адрес указан
            if not address:
                # Возвращаемся на форму с сообщением об ошибке
                return render(request, 'shop/checkout.html', {
                    'items': cart_items,  # Для совместимости с обоими шаблонами
                    'cart_items': cart_items,
                    'total_price': total_price,
                    'error': 'Укажите адрес доставки'
                })

            # Создаем заказ
            order = Order.objects.create(
                user=request.user,
                address=address,
                order_key=f"ORDER-{request.user.id}-{int(time.time())}"[:20],
                status='pending'
            )

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

            # Перенаправляем на страницу подтверждения
            return redirect('payment_confirmation')

    # Отображаем страницу оформления заказа
    return render(request, 'shop/checkout.html', {
        'items': cart_items,  # Для совместимости с обоими шаблонами
        'cart_items': cart_items,
        'total_price': total_price
    })

@login_required
def payment_confirmation(request):
    # Логика оплаты заказа
    return render(request, 'shop/payment_confirmation.html')  # Обратите внимание на 'shop/'


# @login_required #для связывания аккаунтов
# def connect_telegram(request):
#     if request.method == 'POST':
#         code = request.POST.get('telegram_code')
#         if code:
#             try:
#                 # Ищем пользователя Telegram с таким кодом
#                 telegram_user = TelegramUser.objects.get(verification_code=code)
#
#                 # Проверяем, не привязан ли уже пользователь
#                 if telegram_user.user:
#                     return render(request, 'shop/profile.html', {
#                         'error': 'Этот код уже использован или недействителен'
#                     })
#
#                 # Привязываем Telegram к пользователю сайта
#                 telegram_user.user = request.user
#                 telegram_user.save()
#
#                 # Создаем уведомление о привязке
#                 TelegramNotification.objects.create(
#                     telegram_id=telegram_user.telegram_id,
#                     message_text=f"Ваш аккаунт успешно привязан к профилю на сайте FlowerDelivery!\n\n"
#                                  f"Теперь вы будете получать уведомления о ваших заказах."
#                 )
#
#                 return render(request, 'shop/profile.html', {
#                     'message': 'Telegram успешно привязан к вашему аккаунту!'
#                 })
#
#             except TelegramUser.DoesNotExist:
#                 return render(request, 'shop/profile.html', {
#                     'error': 'Неверный код. Пожалуйста, проверьте и попробуйте снова.'
#                 })
#
#         return render(request, 'shop/profile.html', {
#             'error': 'Пожалуйста, введите код привязки'
#         })
#
#     # Проверка, привязан ли уже Telegram
#     telegram_connected = TelegramUser.objects.filter(user=request.user).exists()
#
#     return render(request, 'shop/profile.html', {
#         'telegram_connected': telegram_connected
#     })