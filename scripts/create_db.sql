/*
  Скрипт создания БД для AutoService.
  Сервер: (localdb)\MSSQLLocalDB
  Далее структуру создаст Django через migrations (python manage.py migrate)
*/

IF DB_ID(N'autoservice_db') IS NULL
BEGIN
    PRINT 'Creating database autoservice_db...';
    CREATE DATABASE [autoservice_db];
END
GO

ALTER DATABASE [autoservice_db] SET RECOVERY SIMPLE;
GO

-- (Опционально) Можно создать отдельную схему:
USE [autoservice_db];
GO
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = N'autoservice')
BEGIN
    EXEC('CREATE SCHEMA [autoservice]');
END
GO

PRINT 'Database is ready. Run Django migrations next.';
GO
