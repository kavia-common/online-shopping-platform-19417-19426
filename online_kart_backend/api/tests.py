from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class HealthTests(APITestCase):
    def test_health(self):
        url = reverse("Health")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"message": "Server is up!"})


class CatalogCartOrderFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="secret123")

    def test_register_and_login(self):
        # Register
        url = reverse("auth-register")
        resp = self.client.post(
            url,
            {"username": "bob", "email": "b@example.com", "password": "secret456"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["username"], "bob")

        # Login
        url = reverse("auth-login")
        resp = self.client.post(
            url, {"username": "alice", "password": "secret123"}, format="json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["username"], "alice")

    def test_catalog_and_cart_checkout(self):
        # Staff creates category and product
        User.objects.create_user(username="admin", password="adminpass", is_staff=True)
        self.client.login(username="admin", password="adminpass")

        # Create category
        resp = self.client.post(
            "/api/categories/",
            {"name": "Electronics"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        category_id = resp.data["id"]

        # Create product
        resp = self.client.post(
            "/api/products/",
            {
                "title": "Headphones",
                "description": "Noise cancelling",
                "price": "99.99",
                "stock": 10,
                "is_active": True,
                "category_id": category_id,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        product_id = resp.data["id"]

        self.client.logout()

        # Login as shopper
        self.client.login(username="alice", password="secret123")

        # List products
        resp = self.client.get("/api/products/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.data) >= 1)

        # Add to cart
        resp = self.client.post(
            "/api/cart/add_item/",
            {"product_id": product_id, "quantity": 2},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["items"]), 1)

        # Checkout
        resp = self.client.post(
            "/api/cart/checkout/",
            {"shipping_address": "123 Main St"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["status"], "paid")

        # Orders list
        resp = self.client.get("/api/orders/")
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(len(resp.data), 1)
