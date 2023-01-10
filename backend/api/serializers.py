from string import hexdigits

from django.contrib.auth import get_user_model
from django.db.models import F
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ValidationError

from recipes.models import AmountIngredient, Ingredient, Recipe, Tag

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели User."""
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'password',
        )
        extra_kwargs = {'password': {'write_only': True}}
        read_only_fields = ('is_subscribed',)

    def get_is_subscribed(self, obj):
        """Проверка подписки пользователей."""
        user = self.context.get('request').user
        if user.is_anonymous or (user == obj):
            return False
        return user.subscribe.filter(id=obj.id).exists()

    def create(self, validated_data):
        """ Создание нового пользователя"""
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe."""
    class Meta:
        model = Recipe
        fields = 'id', 'name', 'image', 'cooking_time'
        read_only_fields = '__all__',


class UserSubscribeSerializer(UserSerializer):
    """Сериализатор вывода авторов на которых подписан текущий пользователь.
    """
    recipes = ShortRecipeSerializer(many=True, read_only=True)
    recipes_count = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )
        read_only_fields = '__all__',

    def get_is_subscribed(*args):
        """Проверка подписки пользователей."""
        return True

    def get_recipes_count(self, obj):
        """ Показывает общее количество рецептов у каждого автора."""
        return obj.recipes.count()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag"""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug',)

    def is_hex_color(value):
        """Проверка на шестнадцатеричный цвет."""
        if len(value) not in (3, 6):
            raise ValidationError(
                f'{value} не правильной длины ({len(value)}).'
            )
        if not set(value).issubset(hexdigits):
            raise ValidationError(
                f'{value} не шестнадцатиричное.'
            )

    def validate_color(self, color):
        """Проверяет введенный код цвета."""
        color = str(color).strip(' #')
        TagSerializer.is_hex_color(color)
        return f'#{color}'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient"""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecepieWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов"""
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = SerializerMethodField()
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        read_only_fields = (
            'is_favorite',
            'is_shopping_cart',
        )

    def get_ingredients(self, obj):
        """Получает список ингридиентов для рецепта."""
        ingredients = obj.ingredients.values(
            'id', 'name', 'measurement_unit', amount=F('recipe__amount')
        )
        return ingredients
    
    def get_is_favorited(self, obj):
        """Находится ли рецепт в избранном."""
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.favorites.filter(id=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        """Находится ли рецепт в списке  покупок."""
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.carts.filter(id=obj.id).exists()

    def check_value_validate(value, klass=None):
        """Проверяет правильно ли передано значение."""
        if not str(value).isdecimal():
            raise ValidationError(f'{value} должно содержать цифру')
        if klass:
            obj = klass.objects.filter(id=value)
            if not obj:
                raise ValidationError(
                    f'Значения {value} не существует'
                )
            return obj[0]

    def validate(self, data):
        """Проверка вводных данных при создании и редактировании рецепта. """
        name = str(self.initial_data.get('name')).strip()
        tags = self.initial_data.get('tags')
        ingredients = self.initial_data.get('ingredients')
        values_as_list = (tags, ingredients)

        for value in values_as_list:
            if not isinstance(value, list):
                raise ValidationError(
                    f'Значение "{value}" должно быть в формате "[]"'
                )

        for tag in tags:
            RecepieWriteSerializer.check_value_validate(tag, Tag)

        valid_ingredients = []
        for ing in ingredients:
            ing_id = ing.get('id')
            ingredient = RecepieWriteSerializer.check_value_validate(
                ing_id, Ingredient)
            amount = ing.get('amount')
            RecepieWriteSerializer.check_value_validate(amount)

            valid_ingredients.append(
                {'ingredient': ingredient, 'amount': amount}
            )

        data['name'] = name.capitalize()
        data['tags'] = tags
        data['ingredients'] = valid_ingredients
        data['author'] = self.context.get('request').user
        return data

    def recipe_amount_ingredients_write(recipe, ingredients):
        """Записывает ингредиенты вложенные в рецепт."""
        for ingredient in ingredients:
            AmountIngredient.objects.get_or_create(
                recipe=recipe,
                ingredients=ingredient['ingredient'],
                amount=ingredient['amount']
            )

    def create(self, validated_data):
        """Создание рецепта."""
        image = validated_data.pop('image')
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(image=image, **validated_data)
        recipe.tags.set(tags)
        RecepieWriteSerializer.recipe_amount_ingredients_write(
            recipe, ingredients)
        return recipe

    def update(self, recipe, validated_data):
        """Обновление рецепта."""
        tags = validated_data.get('tags')
        ingredients = validated_data.get('ingredients')
        recipe.image = validated_data.get(
            'image', recipe.image)
        recipe.name = validated_data.get(
            'name', recipe.name)
        recipe.text = validated_data.get(
            'text', recipe.text)
        recipe.cooking_time = validated_data.get(
            'cooking_time', recipe.cooking_time)

        if tags:
            recipe.tags.clear()
            recipe.tags.set(tags)

        if ingredients:
            recipe.ingredients.clear()
            RecepieWriteSerializer.recipe_amount_ingredients_write(
                recipe, ingredients)

        recipe.save()
        return recipe
