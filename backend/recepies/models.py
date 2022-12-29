from django.db import models
from django.core.validators import MinValueValidator

from users.models import MyUser


class Tag(models.Model):
    """Модель для тегов"""
    name = models.CharField(max_length=30, verbose_name='name', unique=True)
    slug = models.SlugField(max_length=200, verbose_name='slug', unique=True)
    color = models.CharField(max_length=7, verbose_name='color', unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
   
    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель для ингредиентов."""
    name = models.CharField(max_length=200,
        verbose_name='Название ингредиента')
    measurement_unit = models.CharField(max_length=30, verbose_name='единица измерения')

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recepie(models.Model):
    """Модель для рецептов."""
    tag = models.ManyToManyField(
        Tag,
        verbose_name='Тег',
        help_text='Выберете тег',
        related_name='recepies'
    )
    author = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recepies'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='RecepieIngredient',
        related_name='recepies'
    )
    name = models.CharField(max_length=200,
        verbose_name='Название рецепта')
    image = models.ImageField(
        verbose_name='Изображение рецепта',
        upload_to='recepies/',
        blank=True
    )
    text = models.TextField(verbose_name='Описание рецепта')
    cooking_time = models.SmallIntegerField(
        verbose_name='Время приготовления',
        validators=[MinValueValidator(1, message='Минимальное число 1')]) # Нужен валидатор 
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )


class RecepieIngredient(models.Model):
    """Модель ингредиенты в рецепте."""
    recepie = models.ForeignKey(Recepie,
        related_name='recepie_ingredient',
        verbose_name='Рецепт',
        on_delete=models.CASCADE)
    ingredients = models.ForeignKey(Ingredient,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE)
    amount = models.IntegerField(verbose_name='Количество ингредиента')

    def __str__(self):
        return (f'{self.ingredients.name} {self.ingredients.measurement_unit}'
                f'{self.amount}')


class Shopping_list(models.Model):
    """Модель Список Покупок."""
    user = models.ForeignKey(MyUser,
        on_delete=models.CASCADE,
        related_name='shopping_list',
        verbose_name='Пользователь')
    recepie = models.ForeignKey(Recepie,
        on_delete=models.CASCADE,
        related_name='shopping_list',
        verbose_name='Рецепт')

    class Meta:
        verbose_name = 'Список покупок'

    def __str__(self):
        return f'{self.user} добавил в список покупок "{self.recepie}"'


class Favorite(models.Model):
    """Модель Избранное."""
    user = models.ForeignKey(MyUser,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorite')
    recepie = models.ForeignKey(Recepie,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorite')

    def __str__(self):
        return f'{self.user} добавил {self.recepie} в избранное'
