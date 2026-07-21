# Time Server API

Простое API на FastAPI для получения текущего времени сервера.

## Структура

- `main.py` — приложение с эндпоинтами `/`, `/time`, `/date`, `/health`
- `requirements.txt` — зависимости
- `env.example` — пример переменных окружения
- `README.md` — документация
- `DEPLOYMENT.md` — деплой через GitHub Actions + GHCR
- `Dockerfile` — образ приложения
- `.github/workflows/deploy.yml` — CI/CD pipeline

## Требования

- Python 3.11+

## Установка

```powershell
pip install -r requirements.txt
copy env.example .env
```

## Запуск

```powershell
python main.py
```

Или через uvicorn:

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```powershell
# Сборка образа
docker build -t time-server-api .

# Запуск контейнера
docker run -p 8000:8000 time-server-api

# Запуск в фоне
docker run -d -p 8000:8000 --name time-server time-server-api
```

- Сервер: http://localhost:8000
- Swagger: http://localhost:8000/docs

## CI/CD (GitHub Actions)

Подробная инструкция: [DEPLOYMENT.md](DEPLOYMENT.md)

Кратко: push в `main` → сборка образа → push в `ghcr.io` → SSH-деплой на сервер.

## Переменные окружения

| Переменная | По умолчанию | Описание        |
|------------|--------------|-----------------|
| `HOST`     | `0.0.0.0`    | Хост сервера    |
| `PORT`     | `8000`       | Порт сервера    |
| `DEBUG`    | `false`      | Reload uvicorn  |

## Эндпоинты

| Метод | Путь      | Описание                |
|-------|-----------|-------------------------|
| GET   | `/`       | Приветствие и ссылка на docs |
| GET   | `/time`   | Текущее время сервера   |
| GET   | `/date`   | Текущая дата сервера    |
| GET   | `/convert`| Конвертация UTC → часовой пояс |
| GET   | `/health` | Health-check            |

### Пример ответа `/time`

```json
{
  "current_time": "2026-07-21T20:17:00.123456",
  "timestamp": 1753112220.123456,
  "formatted_time": "2026-07-21 20:17:00",
  "timezone": "UTC+05:00"
}
```

### Пример ответа `/date`

```json
{
  "date": "2026-07-21",
  "formatted_date": "21.07.2026",
  "year": 2026,
  "month": 7,
  "day": 21,
  "weekday": "Tuesday"
}
```

### Пример `/convert`

```text
GET /convert?time=15:00&timezone=Екатеринбург
```

```json
{
  "input_time_utc": "15:00:00",
  "timezone": "Екатеринбург",
  "iana": "Asia/Yekaterinburg",
  "converted_time": "20:00:00",
  "converted_datetime": "2026-07-21T20:00:00+05:00",
  "utc_offset": "+0500"
}
```
