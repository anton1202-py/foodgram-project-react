from django.contrib.admin import ModelAdmin, TabularInline, register, site
from django.utils.safestring import mark_safe

from .models import Ingredient, Recepie, RecepieIngredient, Tag

site.site_header = 'Админка Foodgram'


class IngredientInline(TabularInline):
    model = RecepieIngredient
    extra = 3


@register(RecepieIngredient)
class LinksAdmin(ModelAdmin):
    pass


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = (
        'name', 'measurement_unit',
    )
    search_fields = (
        'name',
    )
    list_filter = (
        'name',
    )

    save_on_top = True
    empty_value_display = 'Значение не указано'


@register(Recepie)
class RecipeAdmin(ModelAdmin):
    list_display = (
        'name', 'author', 'get_image',
    )
    fields = (
        ('name', 'cooking_time',),
        ('author', 'tag',),
        ('text',),
        ('image',),
    )
    raw_id_fields = ('author', )
    search_fields = (
        'name', 'author',
    )
    list_filter = (
        'name', 'author__username',
    )

    inlines = (IngredientInline,)
    save_on_top = True
    empty_value_display = 'Значение не указано'

    def get_image(self, obj):
        return mark_safe(f'<img src={obj.image.url} width="80" height="30"')

    get_image.short_description = 'Изображение'


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = (
        'name', 'color', 'slug',
    )
    search_fields = (
        'name', 'color'
    )

    save_on_top = True
    empty_value_display = 'Значение не указано'