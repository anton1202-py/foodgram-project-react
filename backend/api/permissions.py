from rest_framework import permissions
from rest_framework.permissions import (BasePermission,
                                        IsAuthenticatedOrReadOnly)


class AdminAuthorOrReadOnly(IsAuthenticatedOrReadOnly):
    """Permission на уровне объекта, чтобы разрешить редактирование
    только автору объекта, администратору или модератору"""
    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or (request.user == obj.author)
            or request.user.is_staff
        )


class AdminOrReadOnly(BasePermission):
    """Permission на уровне объекта, чтобы разрешить редактирование
    только для админов. Остальным - чтение объекта."""
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
            and request.user.is_admin
        )


class OwnerUserOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Разрешение на изменение только для админа и пользователя.
    Остальным только чтение объекта.
    """
    def has_object_permission(self, request, view, obj):
        return (
            request.method in ('GET',)
            or (request.user == obj)
            or request.user.is_admin
        )
