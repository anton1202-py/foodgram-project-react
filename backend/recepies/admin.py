from django.contrib import admin

from .models import (Tag, Ingredient, Recepie, RecepieIngredient,
                    Shopping_list, Favorite)


admin.site.register(Ingredient)
admin.site.register(Tag)
admin.site.register(Recepie)
admin.site.register(RecepieIngredient)
admin.site.register(Shopping_list)
admin.site.register(Favorite)

