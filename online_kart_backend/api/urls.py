from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    health,
    register,
    login_view,
    logout_view,
    CategoryViewSet,
    ProductViewSet,
    CartViewSet,
    OrderViewSet,
)

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"products", ProductViewSet, basename="product")
router.register(r"cart", CartViewSet, basename="cart")
router.register(r"orders", OrderViewSet, basename="order")

urlpatterns = [
    path("health/", health, name="Health"),
    path("auth/register/", register, name="auth-register"),
    path("auth/login/", login_view, name="auth-login"),
    path("auth/logout/", logout_view, name="auth-logout"),
    path("", include(router.urls)),
]
