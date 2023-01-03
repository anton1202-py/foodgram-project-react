from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, RecepieViewSet, TagViewSet, UserViewSet



router = DefaultRouter()
router.register('tags', TagViewSet, 'tags')
router.register('ingredients', IngredientViewSet, 'ingredients')
router.register('recepies', RecepieViewSet, 'recepies')
router.register('users', UserViewSet, 'users')

app_name = 'api'

urlpatterns = (
    path('', include(router.urls)),
)