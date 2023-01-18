# Foodgram - Продуктовый помощник  
### Описание проекта  
Foodgram - это онлайн сервис, на котором пользователи могут публиковать сови рецепты, 
смотреть рецепты других, а так же сохранять их в любимые и скачивать список
покупок для приготовления этих рецептов.

### Проект доступен по ссылке:
http://51.250.77.154

### Как развернуть проект:
1. Клонировать проект с репозитория
2. Установить виртуальное окружение (*python - m venv venv*)
3. Запустить виртуальное окружение (*. venv/scripts/activate*)
4. Установить зависимости (*pip install -r requirements.txt*)
5. Создать файл .env со своими данными для базы данных PosgreSQL
>DB_ENGINE=django.db.backends.postgresql
>DB_NAME='postgres'
>POSTGRES_USER='ваше имя юзера'
>POSTGRES_PASSWORD='ваш пароль'
>DB_HOST='db'
>DB_PORT=5432
6. Создать миграции (*python manage.py makemigrations*)
7. Выполнить миграции (*python manage.py migrate*)
8. Собрать статику (*python manage.py collectstatic*)
9. Импортировать базу данных с ингредиентами (*python manage.py import_data*)
10. Создать суперпользователя (*python manage.py createsuperuser*)





