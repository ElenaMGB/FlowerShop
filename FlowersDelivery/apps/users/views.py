from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..shop.models import TelegramUser, TelegramNotification

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'users/register.html', {'form': form})


@login_required
def profile(request):
    """Страница профиля пользователя"""
    # Проверяем, привязан ли уже Telegram
    telegram_connected = TelegramUser.objects.filter(user=request.user).exists()

    return render(request, 'users/profile.html', {
        'telegram_connected': telegram_connected
    })


@login_required
def connect_telegram(request):
    """Привязка аккаунта Telegram к профилю"""
    if request.method == 'POST':
        code = request.POST.get('telegram_code')
        if code:
            try:
                # Ищем пользователя Telegram с таким кодом
                telegram_user = TelegramUser.objects.get(verification_code=code)

                # Проверяем, не привязан ли уже пользователь
                if telegram_user.user:
                    messages.error(request, 'Этот код уже использован или недействителен')
                    return redirect('profile')

                # Привязываем Telegram к пользователю сайта
                telegram_user.user = request.user
                telegram_user.verification_code = None  # Сбрасываем код после использования
                telegram_user.save()

                # Создаем уведомление о привязке
                TelegramNotification.objects.create(
                    telegram_id=telegram_user.telegram_id,
                    message_text=f"Ваш аккаунт успешно привязан к профилю на сайте FlowerDelivery!\n\n"
                                 f"Теперь вы будете получать уведомления о ваших заказах."
                )

                messages.success(request, 'Telegram успешно привязан к вашему аккаунту!')
                return redirect('profile')

            except TelegramUser.DoesNotExist:
                messages.error(request, 'Неверный код. Пожалуйста, проверьте и попробуйте снова.')
        else:
            messages.error(request, 'Пожалуйста, введите код привязки')

    return render(request, 'users/connect_telegram.html')