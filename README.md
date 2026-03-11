# AutoService (Django + MS SQL LocalDB)

## Требования
- Python 3.10+
- Windows + MS SQL LocalDB `(localdb)\MSSQLLocalDB`
- Установлен ODBC Driver 17/18 for SQL Server

## Быстрый старт (VS Code)
```powershell
cd autoservice_web_full
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env
# 1) Создать базу:
sqlcmd -S "(localdb)\MSSQLLocalDB" -i scripts\create_db.sql

# 2) Миграции и запуск:
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Открыть: http://127.0.0.1:8000

## Роли
- admin — администратор (пользователи/поставщики/отчеты)
- manager — менеджер (клиенты/авто/заказ-наряды)
- mechanic — автомеханик (свои заказ-наряды, добавление запчастей, смена статуса)

## PDF
В карточке заказ-наряда есть кнопка PDF (акт выполненных работ / заказ-наряд).
