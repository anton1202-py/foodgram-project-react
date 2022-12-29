from django.contrib.auth import get_user_model
from django_filters.rest_framework import FilterSet, filters
from recepies.models import Ingredient, Recepie, Tag

User = get_user_model()

class IngredientFilter(FilterSet):
    name = filters.CharFilter(lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ['name']