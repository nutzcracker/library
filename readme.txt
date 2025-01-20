1. Введение
Приложение "Библиотека" — это RESTful API для управления библиотечным каталогом. Оно позволяет управлять книгами, авторами, читателями и выдачей книг. Приложение разработано с использованием FastAPI, SQLAlchemy и PostgreSQL.

2. Требования
Для запуска приложения необходимо установить следующие зависимости:

Python 3.8+

PostgreSQL

Зависимости из файла requirements.txt

3. Установка
3.1. Клонирование репозитория
Склонируйте репозиторий с проектом:
git clone <ваш-репозиторий>
cd <папка-проекта>

3.2. Установка зависимостей
Установите зависимости, указанные в файле requirements.txt:
pip install -r requirements.txt

3.3. Настройка базы данных
Создайте базу данных в PostgreSQL с именем library_db.

Создайте пользователя library_user с паролем 1622 и предоставьте ему права на доступ к базе данных library_db.

Убедитесь, что строка подключения в файле database.py корректна:
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://library_user:1622@localhost/library_db?options=-c%20search_path=public"

3.4. Применение миграций
Примените миграции Alembic для создания таблиц в базе данных:
alembic upgrade head

4. Запуск приложения
Запустите приложение с помощью Uvicorn:
uvicorn app.main:app --reload
Приложение будет доступно по адресу: http://127.0.0.1:8000

5. Использование API
5.1. Регистрация пользователя
Для регистрации нового пользователя отправьте POST-запрос на /register:
curl -X POST "http://127.0.0.1:8000/register" -H "Content-Type: application/json" -d '{
"name": "Иван Иванов",
"email": "ivan@example.com",
"password": "password123",
"role": "reader"
}'

5.2. Вход пользователя
Для входа отправьте POST-запрос на /login:
curl -X POST "http://127.0.0.1:8000/login" -H "Content-Type: application/json" -d '{
"email": "ivan@example.com",
"password": "password123"
}'
В ответ вы получите JWT токен, который нужно использовать для доступа к защищенным эндпоинтам.

5.3. Управление книгами
Создание книги (только для администраторов):
curl -X POST "http://127.0.0.1:8000/books/" -H "Authorization: Bearer <токен>" -H "Content-Type: application/json" -d '{
"title": "Новая книга",
"description": "Описание книги",
"publication_date": "2023-01-01",
"available_copies": 5,
"author_ids": [1],
"genre_ids": [1]
}'

Получение списка книг:
curl -X GET "http://127.0.0.1:8000/books/"

Обновление книги (только для администраторов):
curl -X PUT "http://127.0.0.1:8000/books/1" -H "Authorization: Bearer <токен>" -H "Content-Type: application/json" -d '{
"title": "Обновленное название"
}'

Удаление книги (только для администраторов):
curl -X DELETE "http://127.0.0.1:8000/books/1" -H "Authorization: Bearer <токен>"

5.4. Управление авторами
Создание автора (только для администраторов):
curl -X POST "http://127.0.0.1:8000/authors/" -H "Authorization: Bearer <токен>" -H "Content-Type: application/json" -d '{
"name": "Лев Толстой",
"biography": "Русский писатель",
"date_of_birth": "1828-09-09"
}'

Получение списка авторов:
curl -X GET "http://127.0.0.1:8000/authors/"

5.5. Управление читателями
Получение списка читателей (только для администраторов):
curl -X GET "http://127.0.0.1:8000/readers/" -H "Authorization: Bearer <токен>"

Обновление информации о читателе:
curl -X PUT "http://127.0.0.1:8000/readers/1" -H "Authorization: Bearer <токен>" -H "Content-Type: application/json" -d '{
"name": "Новое имя"
}'

5.6. Выдача и возврат книг
Выдача книги:
curl -X POST "http://127.0.0.1:8000/loans/" -H "Authorization: Bearer <токен>" -H "Content-Type: application/json" -d '{
"book_id": 1
}'

Возврат книги:
curl -X PUT "http://127.0.0.1:8000/loans/1/return" -H "Authorization: Bearer <токен>"

6. Тестирование
Для запуска тестов используйте команду:
pytest tests/

7. Логирование
Логи приложения записываются в файл app.log. Вы можете настроить уровень логирования и формат в файле main.py.