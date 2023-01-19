from string import hexdigits

from django.contrib.auth import get_user_model
from django.db.models import F
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ValidationError

from recipes.models import AmountIngredient, Ingredient, Recipe, Tag
from .mixins import GetIsSubscribedMixin

User = get_user_model()


class UserSerializer(serializers.ModelSerializer, GetIsSubscribedMixin):
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
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = ShortRecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data

    def get_recipes_count(self, obj):
        """ Показывает общее количество рецептов у каждого автора."""
        return obj.recipes.count()

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


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag"""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug',)

    def is_hex_color(self, value):
        """Проверка на шестнадцатеричный цвет."""
        if len(value) not in (4, 8):
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
        self.is_hex_color(color)
        return f'#{color}'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient"""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientsEditSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = Ingredient
        fields = ('id', 'amount')


class AmountIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source='ingredients.id')
    name = serializers.ReadOnlyField(
        source='ingredients.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredients.measurement_unit')

    class Meta:
        model = AmountIngredient
        fields = (
            'id', 'name', 'measurement_unit', 'amount'
        )


class RecipeUserSerializer(
        GetIsSubscribedMixin,
        serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField(
        read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра рецептов"""
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = AmountIngredientSerializer(
        many=True,
        required=True,
        source='ingredient')
    image = Base64ImageField()
    is_in_shopping_cart = SerializerMethodField()
    is_favorited = SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'tags', 'author', 'ingredients',
                  'image', 'text', 'cooking_time', 'is_favorited', 'is_in_shopping_cart')
    
    def get_is_in_shopping_cart(self, obj): 
        """Находится ли рецепт в списке  покупок.""" 
        user = self.context.get('request').user 
        if user.is_anonymous: 
            return False 
        return user.carts.filter(id=obj.id).exists()

    def get_is_favorited(self, obj): 
        """Находится ли рецепт в избранном.""" 
        user = self.context.get('request').user 
        if user.is_anonymous: 
            return False 
        return user.favorites.filter(id=obj.id).exists()

    def get_ingredients(self, obj):
        """Получает список ингридиентов для рецепта."""
        ingredients = obj.ingredients.values(
            'id', 'name', 'measurement_unit', quantity=F('recipe__amount')
        )
        return ingredients


class RecepieWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов"""
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all())
    author = serializers.ReadOnlyField(required=False)
    ingredients = IngredientsEditSerializer(
        many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        read_only_fields = (
            'is_favorited',
            'is_shopping_cart',
        )

    def get_ingredients(self, obj):
        """Получает список ингридиентов для рецепта."""
        ingredients = obj.ingredients.values(
            'id', 'name', 'measurement_unit', quantity=F('recipe__amount')
        )
        return ingredients

    def check_value_validate(self, value, klass=None): 
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
        ingredients = data['ingredients']
        ingredient_list = []
        for items in ingredients:
            ingredient = get_object_or_404(
                Ingredient, id=items['id'])
            if ingredient in ingredient_list:
                raise serializers.ValidationError(
                    'Ингредиент должен быть уникальным!')
            ingredient_list.append(ingredient)

        tags = data['tags']
        if not tags:
            raise serializers.ValidationError(
                'Нужен хотя бы один тэг для рецепта!')

        valid_ingredients = []
        for ing in ingredients:
            ing_id = ing.get('id')
            ingredient = self.check_value_validate(
                ing_id, Ingredient)
            amount = ing.get('amount')
            self.check_value_validate(amount)

            valid_ingredients.append(
                {'ingredient': ingredient, 'amount': amount}
            )
        return data

    def recipe_amount_ingredients_write(self, recipe, ingredients):
        """Записывает ингредиенты вложенные в рецепт."""
        AmountIngredient.objects.bulk_create(
            [AmountIngredient(
                recipe=recipe,
                ingredients=get_object_or_404(Ingredient, id=ingr.get('id')),
                amount=ingr.get('amount')) for ingr in ingredients])

    def create(self, validated_data):
        """Создание рецепта."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.recipe_amount_ingredients_write(recipe, ingredients)
        return recipe

    def update(self, recipe, validated_data):
        """Обновление рецепта."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe.tags.set(tags)
        AmountIngredient.objects.filter(recipe=recipe).delete()
        self.recipe_amount_ingredients_write(recipe, ingredients)
        return super().update(recipe, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }).data
