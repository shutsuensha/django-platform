## 📦 EffectiveMobile Job Task
#### Старт: 16.05.2025
#### Завершение: 17.05.2025
---

### 🔧 Технологии
- Python 3.10.12  
- Django 5.2.1  
- Django ORM  
- Django Templates  
- Django REST Framework
- Django Test
- PostgreSQL
- TailwindCSS
- Ruff

---
### 🔗 Репозиторий
```bash
git clone git@github.com:shutsuensha/effectivemobile-job-task.git
cd effectivemobile-job-task/
```

### 🐍 Виртуальное окружение и зависимости
#### Создайте и активируйте виртуальное окружение:
```bash
python3 -m venv .venv
source .venv/bin/activate
```
#### Установите зависимости из requirements.txt
```bash
pip3 install -r requirements.txt
```

### 🗃 Настройка PostgreSQL
#### Перейдите под пользователя postgres и запустите psql
```bash
sudo -i -u postgres
psql
```
#### В psql выполните:
```sql
CREATE DATABASE mydatabase;
CREATE USER myuser WITH ENCRYPTED PASSWORD 'mypassword';
GRANT ALL PRIVILEGES ON DATABASE mydatabase TO myuser;
\q
```

### ⚙️ Конфигурация окружения
#### Создайте файл .env в корне проекта, скопировав структуру из .env.example
```bash
touch .env
cp .env.example .env
```

#### Откройте .env и задайте переменные
```ini
DB_HOST=localhost
DB_PORT=5432
DB_USER=myuser
DB_PASS=mypassword
DB_NAME=mydatabase

# Сгенерируйте SECRET_KEY:
SECRET_KEY=ваш_сгенерированный_ключ
DEBUG=True
```
#### Сгенерировать SECRET_KEY можно командой
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 🚀 Применение миграций и запуск сервера
#### Примените миграции:
```bash
python3 manage.py migrate
```
#### Запустите локальный сервер
```bash
python3 manage.py runserver
```
#### Откройте в браузере
http://127.0.0.1:8000/

### 📚 REST API документация
#### Swagger UI
http://127.0.0.1:8000/swagger/
#### ReDoc
http://127.0.0.1:8000/redoc/

## ✅ Запуск тестов
```bash
python3 manage.py test
```

