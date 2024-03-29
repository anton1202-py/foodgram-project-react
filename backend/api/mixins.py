from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.status import (HTTP_201_CREATED, HTTP_204_NO_CONTENT,
                                   HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED)

ADD_MET = ('GET', 'POST',)
DEL_MET = ('DELETE',)


class GetIsSubscribedMixin:
    def get_is_subscribed(self, obj):
        """Проверка подписки пользователей."""
        user = self.context.get('request').user
        if user.is_anonymous or (user == obj):
            return False
        return user.subscribe.filter(id=obj.id).exists()


class AddDelViewMixin:
    """Добавляет добавляющий и удаляющий методы."""
    add_serializer = None

    def add_del_method(self, object_id, manager):
        """Добавляет и удаляет связь через менеджер."""
        assert self.add_serializer is not None, (
            f'{self.__class__.__name__} should include '
            'an `add_serializer` attribute.'
        )

        user = self.request.user
        if user.is_anonymous:
            return Response(status=HTTP_401_UNAUTHORIZED)
        managers = {
            'subscribers': user.subscribe,
            'favorite': user.favorites,
            'shopping_cart': user.carts,
        }
        manager = managers[manager]
        object = get_object_or_404(self.queryset, id=object_id)
        serializer = self.add_serializer(
            object, context={'request': self.request}
        )
        object_exist = manager.filter(id=object_id).exists()
        if (self.request.method in ADD_MET) and not object_exist:
            manager.add(object)
            return Response(serializer.data, status=HTTP_201_CREATED)

        if (self.request.method in DEL_MET) and object_exist:
            manager.remove(object)
            return Response(status=HTTP_204_NO_CONTENT)
        return Response(status=HTTP_400_BAD_REQUEST)
