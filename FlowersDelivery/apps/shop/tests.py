from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Product, Cart, CartItem, Order, OrderItem


class ProductTests(TestCase):
    def setUp(self):
        Product.objects.create(
            name="Розы красные",
            description="Букет из 11 красных роз",
            price=2500.00
        )

    def test_product_creation(self):
        product = Product.objects.get(name="Розы красные")
        self.assertEqual(product.price, 2500.00)

    def test_catalog_view(self):
        response = self.client.get(reverse('catalog'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shop/catalog.html')


class CartTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.product = Product.objects.create(name="Тюльпаны", price=1500.00)

    def test_add_to_cart(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('add_to_cart', args=[self.product.id]))
        self.assertEqual(response.status_code, 302)  # Redirect

        cart = Cart.objects.get(user=self.user)
        cart_item = CartItem.objects.get(cart=cart, product=self.product)
        self.assertEqual(cart_item.quantity, 1)

