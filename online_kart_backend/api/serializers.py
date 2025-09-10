from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Category, Product, Cart, CartItem, Order, OrderItem

User = get_user_model()


# PUBLIC_INTERFACE
class UserSerializer(serializers.ModelSerializer):
    """Serializer for user information, limited fields for basic profile."""

    class Meta:
        model = User
        fields = ["id", "username", "email"]


# PUBLIC_INTERFACE
class RegisterSerializer(serializers.ModelSerializer):
    """Serializer to handle user registration."""

    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email"),
            password=validated_data["password"],
        )


# PUBLIC_INTERFACE
class CategorySerializer(serializers.ModelSerializer):
    """Serializer for product categories."""

    class Meta:
        model = Category
        fields = ["id", "name", "slug"]
        read_only_fields = ["id", "slug"]


# PUBLIC_INTERFACE
class ProductSerializer(serializers.ModelSerializer):
    """Serializer for products, including category name."""

    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), write_only=True, source="category"
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "price",
            "stock",
            "is_active",
            "category",
            "category_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]


# PUBLIC_INTERFACE
class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for items in a cart, with computed line total."""

    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True),
        write_only=True,
        source="product",
    )
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_id", "quantity", "line_total"]
        read_only_fields = ["id", "line_total"]

    def get_line_total(self, obj) -> str:
        return str(obj.get_line_total())

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value


# PUBLIC_INTERFACE
class CartSerializer(serializers.ModelSerializer):
    """Serializer for a user's cart, with items and totals."""

    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "user", "items", "subtotal", "updated_at"]
        read_only_fields = ["id", "user", "items", "subtotal", "updated_at"]

    def get_subtotal(self, obj) -> str:
        return str(obj.get_subtotal())


# PUBLIC_INTERFACE
class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items."""

    product = ProductSerializer(read_only=True)
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity", "unit_price", "line_total"]
        read_only_fields = ["id", "product", "quantity", "unit_price", "line_total"]

    def get_line_total(self, obj) -> str:
        return str(obj.get_line_total())


# PUBLIC_INTERFACE
class OrderSerializer(serializers.ModelSerializer):
    """Serializer for orders including items and totals."""

    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "status",
            "total_amount",
            "shipping_address",
            "created_at",
            "updated_at",
            "items",
        ]
        read_only_fields = [
            "id",
            "user",
            "status",
            "total_amount",
            "created_at",
            "updated_at",
            "items",
        ]


# PUBLIC_INTERFACE
class AddToCartSerializer(serializers.Serializer):
    """Input serializer for adding/updating a cart item."""

    product_id = serializers.IntegerField(help_text="ID of the product to add")
    quantity = serializers.IntegerField(default=1, help_text="Quantity to add")

    def validate(self, attrs):
        try:
            product = Product.objects.get(id=attrs["product_id"], is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or inactive.")
        if attrs["quantity"] < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        if product.stock < attrs["quantity"]:
            raise serializers.ValidationError("Insufficient stock for this product.")
        return attrs


# PUBLIC_INTERFACE
class CheckoutSerializer(serializers.Serializer):
    """Input serializer for performing checkout on current cart."""

    shipping_address = serializers.CharField(max_length=500)

