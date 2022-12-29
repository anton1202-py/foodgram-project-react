from string import hexdigits

from drf_extra_fields.fields import Base64ImageField
from recepies.models import (Favorite, Ingredient, Recepie, RecepieIngredient,
                             Shopping_list, Tag)
from rest_framework import serializers
from rest_framework.fields import IntegerField, SerializerMethodField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ValidationError
from users.models import MyUser, Subscription


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели User."""
    is_subscribed = SerializerMethodField()

    class Meta:
        model = MyUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'password',
        )
        read_only_fields = 'is_subscribed'

    def get_is_subscribed(self, obj):
        """Проверка подписки пользователей."""
        user = self.context.get('request').user
        if user.is_anonymous or (user == obj):
            return False
        return MyUser.objects.filter(user=user, id=obj.id).exists()

    def create(self, validated_data):
        """ Создание нового пользователя"""
        user = MyUser(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

    def validate_username(self, username):
        """Проверяет введённый username."""
        if len(username) < 3:
            raise ValidationError(
                'Длина username допустима от '
                f'{3} до {100}'
            )
        return username



class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag"""
    class Meta:
        model = Tag
        fields = ('color', 'name', 'slug',)

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
        fields = ('name', 'measurement_unit')


class RecepieReadSerializer(serializers.ModelSerializer):
    """Сериализатор только для чтения модели Recepie"""
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientSerializer()
    image = Base64ImageField()
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_anonimus:
            return False
        return Favorite.objects.filter(recipe=obj, user=user).exist()
    
    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_anonimus:
            return False
        return Shopping_list.objects.filter(recipe=obj, user=user).exist()

    class Meta:
        model = Recepie
        fields = ('tag', 'author', 'ingredients', 'name', 'image', 'text',
                  'cooking_time', 'pub_date', 'is_favorited',  'is_in_shopping_cart')


class RecepieIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор выведения количества ингридиента"""
    model = RecepieIngredient

    class Meta:
        fields = ('amount')


class RecepieWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов"""
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recepie
        fields = ('tags', 'author', 'ingredients', 'name', 
                  'image', 'text', 'cooking_time')

    def recepie_amount_ingredients_write(recepie, ingredients):
        """Записывает ингредиенты вложенные в рецепт."""
        for ingredient in ingredients:
            RecepieIngredient.objects.get_or_create(
                recepie=recepie,
                ingredients=ingredient['ingredient'],
                amount=ingredient['amount']
            )

    def create(self, validated_data):
        """Создание рецепта"""
        tags = validated_data.pop('tag')
        ingredients = validated_data.pop('ingredients')
        image = validated_data.pop('image')
        recepie = Recepie.objects.create(**validated_data)
        recepie.tags.set(tags)
        RecepieWriteSerializer.recepie_amount_ingredients_write(recepie, ingredients)
        return recepie

    def update(self, recepie, validated_data):
        """Обновление рецепта."""
        tags = validated_data.get('tags')
        ingredients = validated_data.get('ingredients')
        recepie.image = validated_data.get(
            'image', recepie.image)
        recepie.name = validated_data.get(
            'name', recepie.name)
        recepie.text = validated_data.get(
            'text', recepie.text)
        recepie.cooking_time = validated_data.get(
            'cooking_time', recepie.cooking_time)
        if tags:
            recepie.tags.clear()
            recepie.tags.set(tags)

        if ingredients:
            recepie.ingredients.clear()
            RecepieWriteSerializer.recepie_amount_ingredients_write(recepie, ingredients)

        recepie.save()
        return recepie


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для использования модели Subcription"""
    recipes = RecepieReadSerializer(many=True, read_only=True)
    recipes_count = SerializerMethodField()

    class Meta:
        model = MyUser
        fields = (
            'email',
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
        """ Показывает количество рецептов у автора."""
        return obj.recipes.count()
