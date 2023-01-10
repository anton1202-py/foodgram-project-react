from django.contrib.auth.models import AbstractUser
from django.db.models import (CharField, CheckConstraint, EmailField,
                              ManyToManyField, Q)
from django.db.models.functions import Length
from django.utils.translation import gettext_lazy as _

from .validators import MinLenValidator

CharField.register_lookup(Length)


class MyUser(AbstractUser):
    """Модель пользователя."""
    email = EmailField(
        verbose_name='Адрес электронной почты',
        max_length=150,
        unique=True,
        help_text=('Обязательно для заполнения. '
                   'Максимум 255 символов.')
    )
    username = CharField(
        verbose_name='Уникальный юзернейм',
        max_length=150,
        unique=True,
        help_text=('Обязательно для заполнения. '
                   'От 3 до 150 букв.'),
        validators=(
            MinLenValidator(min_len=3),
        ),
    )
    first_name = CharField(
        verbose_name='Имя',
        max_length=150,
        help_text=('Обязательно для заполнения.Максимум 150 букв.'))

    last_name = CharField(
        verbose_name='Фамилия',
        max_length=150,
        help_text=('Обязательно для заполнения.Максимум 150 букв.')
    )
    password = CharField(
        verbose_name=_('Пароль'),
        max_length=150,
        help_text=('Обязательно для заполнения.Максимум 150 букв.')
    )
    subscribe = ManyToManyField(
        verbose_name='Подписка',
        related_name='subscribers',
        to='self',
        symmetrical=False,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)
        constraints = (
            CheckConstraint(
                check=Q(username__length__gte=3),
                name='username too short',
            ),
        )

    def __str__(self):
        return f'{self.username}: {self.email}'
