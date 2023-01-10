from datetime import datetime as dt
from urllib.parse import unquote

from django.db.models import F, Sum
from django.http.response import HttpResponse
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from recipes.models import AmountIngredient, Ingredient, Recipe, Tag
from .mixins import AddDelViewMixin
from .paginators import PagePagination
from .permissions import AdminAuthorOrReadOnly, AdminOrReadOnly
from .serializers import (IngredientSerializer, RecepieWriteSerializer,
                          ShortRecipeSerializer, TagSerializer,
                          UserSubscribeSerializer)

DATE_FORMAT = '%d/%m/%Y %H:%M'
ADD_METHODS = ('GET', 'POST',)

DEL_METHODS = ('DELETE',)


class UserViewSet(DjoserUserViewSet, AddDelViewMixin):
    """Вьюсет для пользователей."""
    pagination_class = PagePagination
    add_serializer = UserSubscribeSerializer

    @action(methods=('get', 'post', 'delete',), detail=True)
    def subscribe(self, request, id):
        """Создаёт и удалет связь между пользователями."""
        return self.add_del_method(id, 'subscribers')

    @action(methods=('get',), detail=False)
    def subscriptions(self, request):
        """Подписки пользоваетеля."""
        user = self.request.user
        if user.is_anonymous:
            return Response(status=HTTP_401_UNAUTHORIZED)
        authors = user.subscribe.all()
        pages = self.paginate_queryset(authors)
        serializer = UserSubscribeSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет для тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AdminOrReadOnly,)


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AdminOrReadOnly,)

    def get_queryset(self):
        """Получает queryset в соответствии с параметрами запроса."""
        name = self.request.query_params.get('name')
        queryset = self.queryset
        if name:
            if name[0] == '%':
                name = unquote(name)
            name = name.lower()
            stw_queryset = list(queryset.filter(name__startswith=name))
            cnt_queryset = queryset.filter(name__contains=name)
            stw_queryset.extend(
                [i for i in cnt_queryset if i not in stw_queryset]
            )
            queryset = stw_queryset
        return queryset


class RecipeViewSet(ModelViewSet, AddDelViewMixin):
    """Вьюсет для работы с рецептами."""
    queryset = Recipe.objects.select_related('author')
    serializer_class = RecepieWriteSerializer
    permission_classes = (AdminAuthorOrReadOnly,)
    pagination_class = PagePagination
    add_serializer = ShortRecipeSerializer

    def get_queryset(self):
        """Получает queryset в соответствии с параметрами запроса."""
        queryset = self.queryset
        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(
                tags__slug__in=tags).distinct()

        author = self.request.query_params.get('author')
        if author:
            queryset = queryset.filter(author=author)
            print(queryset)

        user = self.request.user
        if user.is_anonymous:
            return queryset

        is_in_shopping = self.request.query_params.get('is_in_shopping_cart')
        if is_in_shopping in ('1', 'true',):
            queryset = queryset.filter(cart=user.id)
        elif is_in_shopping in ('0', 'false',):
            queryset = queryset.exclude(cart=user.id)

        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited in ('1', 'true',):
            queryset = queryset.filter(favorite=user.id)
        if is_favorited in ('0', 'false',):
            queryset = queryset.exclude(favorite=user.id)
        return queryset

    @action(methods=('get', 'post', 'delete',), detail=True)
    def favorite(self, request, pk):
        """Добавляет/удалет рецепт в `избранное`."""
        return self.add_del_method(pk, 'favorite')

    @action(methods=('get', 'post', 'delete',), detail=True)
    def shopping_cart(self, request, pk):
        """Добавляет/удалет рецепт в `список покупок`."""
        return self.add_del_method(pk, 'shopping_cart')

    @action(methods=('get',), detail=False)
    def download_shopping_cart(self, request):
        """Загружает файл *.txt со списком покупок."""
        user = self.request.user
        if not user.carts.exists():
            return Response(status=HTTP_400_BAD_REQUEST)
        ingredients = AmountIngredient.objects.filter(
            recipe__in=(user.carts.values('id'))
        ).values(
            ingredient=F('ingredients__name'),
            measure=F('ingredients__measurement_unit')
        ).annotate(amount=Sum('amount'))

        filename = f'{user.username}_shopping_list.txt'
        shopping_list = (
            f'Список покупок для:\n\n{user.first_name}\n'
            f'{dt.now().strftime(DATE_FORMAT)}\n'
        )
        for ing in ingredients:
            shopping_list += (
                f'{ing["ingredient"]}: {ing["amount"]} {ing["measure"]}\n'
            )

        shopping_list += '\n\nПосчитано в Foodgram'

        response = HttpResponse(
            shopping_list, content_type='text.txt; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
