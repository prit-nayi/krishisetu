"""
common/permissions.py — Role-based access control (RBAC) permission classes.
"""
from rest_framework import permissions


class IsFarmer(permissions.BasePermission):
    """Allows access only to authenticated users with the 'farmer' role."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "farmer"
        )


class IsBuyer(permissions.BasePermission):
    """Allows access only to authenticated users with the 'buyer' role."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "buyer"
        )


class IsAdminUser(permissions.BasePermission):
    """Allows access only to authenticated users with the 'admin' role or is_staff."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.role == "admin" or request.user.is_staff or request.user.is_superuser)
        )


class IsFarmerOrReadOnly(permissions.BasePermission):
    """Allows write permissions to farmers and read-only access to others."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "farmer"
        )


class IsBuyerOrReadOnly(permissions.BasePermission):
    """Allows write permissions to buyers and read-only access to others."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "buyer"
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """Object-level permission allowing owners or admins to view/edit."""

    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin" or request.user.is_staff or request.user.is_superuser:
            return True
        # Check standard ownership attributes
        if hasattr(obj, "user"):
            return obj.user == request.user
        if hasattr(obj, "farmer") and hasattr(obj.farmer, "user"):
            return obj.farmer.user == request.user
        if hasattr(obj, "farmer") and isinstance(obj.farmer, request.user.__class__):
            return obj.farmer == request.user
        if hasattr(obj, "buyer") and isinstance(obj.buyer, request.user.__class__):
            return obj.buyer == request.user
        return False
