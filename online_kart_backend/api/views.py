from decimal import Decimal

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, viewsets, mixins
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response

from .models import Category, Product, Cart, CartItem, Order, OrderItem
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    CategorySerializer,
    ProductSerializer,
    CartSerializer,
    AddToCartSerializer,
    OrderSerializer,
    CheckoutSerializer,
)

User = get_user_model()


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def health(request):
    """Simple health check endpoint."""
    return Response({"message": "Server is up!"})


# PUBLIC_INTERFACE
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@swagger_auto_schema(
    method="post",
    operation_id="auth_register",
    operation_description="Register a new user.",
    request_body=RegisterSerializer,
    responses={201: UserSerializer},
    tags=["auth"],
)
def register(request):
    """Register a new user account and return basic profile."""
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


# PUBLIC_INTERFACE
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@swagger_auto_schema(
    method="post",
    operation_id="auth_login",
    operation_description="Login a user with username and password.",
    request_body=None,
    tags=["auth"],
)
def login_view(request):
    """Login with username and password and establish session."""
    username = request.data.get("username")
    password = request.data.get("password")
    user = authenticate(request, username=username, password=password)
    if not user:
        return Response(
            {"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST
        )
    login(request, user)
    return Response(UserSerializer(user).data)


# PUBLIC_INTERFACE
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@swagger_auto_schema(
    method="post",
    operation_id="auth_logout",
    operation_description="Logout current user.",
    tags=["auth"],
)
def logout_view(request):
    """Logout current authenticated user."""
    logout(request)
    return Response({"detail": "Logged out."})


class IsAdminOrReadOnly(permissions.BasePermission):
    """Read-only for all; write for staff."""

    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return bool(request.user and request.user.is_staff)


# PUBLIC_INTERFACE
class CategoryViewSet(viewsets.ModelViewSet):
    """CRUD for product categories."""

    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

    @swagger_auto_schema(operation_summary="List categories", tags=["catalog"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Create category", tags=["catalog"])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


# PUBLIC_INTERFACE
class ProductViewSet(viewsets.ModelViewSet):
    """CRUD for products with simple filtering."""

    queryset = Product.objects.filter(is_active=True).select_related("category").order_by(
        "-created_at"
    )
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get("category")
        search = self.request.query_params.get("q")
        if category:
            qs = qs.filter(category__slug=category)
        if search:
            qs = qs.filter(title__icontains=search)
        return qs

    @swagger_auto_schema(operation_summary="List products", tags=["catalog"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Retrieve product", tags=["catalog"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Create product", tags=["catalog"])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Update product", tags=["catalog"])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Partial update product", tags=["catalog"])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Delete product", tags=["catalog"])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


# PUBLIC_INTERFACE
class CartViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """Cart API for current authenticated user to view and manage cart items."""

    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only single cart per user
        return Cart.objects.filter(user=self.request.user).prefetch_related(
            "items__product"
        )

    def _get_or_create_cart(self, user) -> Cart:
        cart, _ = Cart.objects.get_or_create(user=user)
        return cart

    @swagger_auto_schema(operation_summary="Get current user's cart", tags=["cart"])
    def list(self, request, *args, **kwargs):
        cart = self._get_or_create_cart(request.user)
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    # PUBLIC_INTERFACE
    @action(detail=False, methods=["post"])
    @swagger_auto_schema(
        method="post",
        operation_id="cart_add_item",
        operation_summary="Add or update a product in the cart",
        request_body=AddToCartSerializer,
        tags=["cart"],
    )
    def add_item(self, request):
        """Add/update a product in the current user's cart."""
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_id = serializer.validated_data["product_id"]
        quantity = serializer.validated_data["quantity"]

        product = get_object_or_404(Product, id=product_id, is_active=True)

        if product.stock < quantity:
            return Response(
                {"detail": "Insufficient stock."}, status=status.HTTP_400_BAD_REQUEST
            )

        cart = self._get_or_create_cart(request.user)
        item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, defaults={"quantity": quantity}
        )
        if not created:
            item.quantity = quantity
            item.save(update_fields=["quantity", "updated_at"])
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)

    # PUBLIC_INTERFACE
    @action(detail=False, methods=["post"])
    @swagger_auto_schema(
        method="post",
        operation_id="cart_remove_item",
        operation_summary="Remove a product from the cart",
        request_body=AddToCartSerializer,
        tags=["cart"],
    )
    def remove_item(self, request):
        """Remove a product from the current user's cart."""
        product_id = request.data.get("product_id")
        if not product_id:
            return Response(
                {"detail": "product_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cart = self._get_or_create_cart(request.user)
        CartItem.objects.filter(cart=cart, product_id=product_id).delete()
        return Response(CartSerializer(cart).data)

    # PUBLIC_INTERFACE
    @action(detail=False, methods=["post"])
    @swagger_auto_schema(
        method="post",
        operation_id="cart_clear",
        operation_summary="Clear all items from the cart",
        tags=["cart"],
    )
    def clear(self, request):
        """Clear all items from current user's cart."""
        cart = self._get_or_create_cart(request.user)
        cart.items.all().delete()
        return Response({"detail": "Cart cleared."})

    # PUBLIC_INTERFACE
    @action(detail=False, methods=["post"])
    @swagger_auto_schema(
        method="post",
        operation_id="cart_checkout",
        operation_summary="Checkout the cart and create an order",
        request_body=CheckoutSerializer,
        responses={201: OrderSerializer},
        tags=["orders"],
    )
    @transaction.atomic
    def checkout(self, request):
        """Checkout the cart, reduce inventory, and create an order."""
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shipping_address = serializer.validated_data["shipping_address"]

        cart = self._get_or_create_cart(request.user)
        items = list(
            cart.items.select_related("product").select_for_update(of=("self", "product"))
        )
        if not items:
            return Response(
                {"detail": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST
            )

        # Stock validation
        for it in items:
            if it.product.stock < it.quantity:
                return Response(
                    {
                        "detail": f"Insufficient stock for {it.product.title}",
                        "product_id": it.product_id,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Create order
        order = Order.objects.create(user=request.user, shipping_address=shipping_address)

        total = Decimal("0.00")
        order_items = []
        for it in items:
            unit_price = it.product.price
            line_total = unit_price * it.quantity
            total += line_total
            order_items.append(
                OrderItem(
                    order=order,
                    product=it.product,
                    quantity=it.quantity,
                    unit_price=unit_price,
                )
            )
            # Deduct stock
            it.product.stock -= it.quantity
            it.product.save(update_fields=["stock", "updated_at"])

        OrderItem.objects.bulk_create(order_items)
        order.total_amount = total
        order.status = "paid"  # For demo purposes, mark as paid immediately
        order.save(update_fields=["total_amount", "status", "updated_at"])

        # Clear cart
        cart.items.all().delete()

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


# PUBLIC_INTERFACE
class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for orders belonging to the current user."""

    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .order_by("-created_at")
            .prefetch_related("items__product")
        )

    @swagger_auto_schema(operation_summary="List my orders", tags=["orders"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Retrieve my order", tags=["orders"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
