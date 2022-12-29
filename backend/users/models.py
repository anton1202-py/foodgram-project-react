from django.db import models
from django.contrib.auth.models import AbstractUser

class MyUser(AbstractUser):
    """Модель пользователя."""
    username = models.CharField(db_index=True, max_length=100, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=255, default='')
    last_name = models.CharField(max_length=255, default='')
    password = models.CharField(verbose_name='Пароль', max_length=24,
        help_text='Введите пароль')
    subscribe = models.ManyToManyField(
        verbose_name='Подписка',
        related_name='subscribers',
        to='self')

    def __str__(self):
        return f'{self.username}: {self.email}'


class Subscription(models.Model):
    """Модель подписчиков."""
    user = models.ForeignKey(MyUser, 
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
        related_name='subcriber')
    author = models.ForeignKey(MyUser,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='subcribing')