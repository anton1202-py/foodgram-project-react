from django.contrib.auth import get_user_model
from django.db.models import F, Sum
from django.http.response import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from recepies.models import (Favorite, Ingredient, Recepie, RecepieIngredient,
                             Shopping_list, Tag)
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from djoser.views import UserViewSet as DjoserUserViewSet
from .mixins import AddDelViewMixin
from .filters import IngredientFilter
from .paginators import PagePagination
from .permissions import AdminAuthorOrReadOnly, AdminOrReadOnly
from .serializers import (IngredientSerializer, SubscriptionSerializer, RecepieWriteSerializer, TagSerializer)


class UserViewSet(DjoserUserViewSet, AddDelViewMixin):
    """Вьюсет для пользователей."""
    pagination_class = PagePagination
    add_serializer = SubscriptionSerializer

    @action(methods=('get', 'post', 'delete',), detail=True)
    def subscribe(self, request, id):
        """Создаёт и удалет связь между пользователями."""
        return self.add_del_method(id, 'subscribe')

    @action(methods=('get',), detail=False)
    def subscriptions(self, request):
        """Подписки пользоваетеля."""
        user = self.request.user
        if user.is_anonymous:
            return Response(status=HTTP_401_UNAUTHORIZED)
        authors = user.subscribe.all()
        pages = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
        

class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет для тегов.
    Создавать и изменять теги могут только админы"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AdminOrReadOnly,)


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов.
    Создавать и изменять ингредиенты могут только админы"""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecepieViewSet(ModelViewSet):
    """Вьюсет для рецептов. Создание, редактирование, вывод.
    Добавление и удаление в избранное и список покупок.
    Отправка файла со списком покупок."""
    queryset = Recepie.objects.all()
    serializer_class = RecepieWriteSerializer
    permission_classes = (AdminAuthorOrReadOnly,)


    