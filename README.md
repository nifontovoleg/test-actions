# Time Server API

Небольшой FastAPI-сервис: отдаёт время и дату сервера, конвертирует UTC в нужный часовой пояс и деплоится одной кнопкой через GitHub Actions → Docker → VPS.

Подходит как учебный стенд CI/CD и как простой time-backend для ботов, фронтенда и внутренних скриптов.

---

## Зачем этот проект

| Задача | Как закрывает |
|--------|----------------|
| Узнать время/дату на сервере | `GET /time`, `GET /date` |
| Перевести UTC → город/пояс | `GET /convert` |
| Проверить, что сервис жив | `GET /health` |
| Научиться деплоить API | Docker + GHCR + SSH в [DEPLOYMENT.md](DEPLOYMENT.md) |

Это не «ещё одни мировые часы», а **понятный каркас**: минимальный бэкенд + контейнер + автоматический выкат на сервер. На нём удобно отрабатывать пайплайн и потом наращивать фичи.

---

## Для кого

- **Разработчики**, которым нужен простой time-API без лишней инфраструктуры
- **Те, кто изучает FastAPI / Docker / GitHub Actions** — от кода до продакшен-деплоя
- **Авторы Telegram-ботов и мини-приложений**, где нужна серверная дата/конвертация поясов
- **Команды**, которым нужен эталон «push в main → контейнер на VPS»

---

## Как применять

### В учебных целях
Склонировал → поднял локально → посмотрел Swagger → запушил в `main` → увидел контейнер на сервере. Весь путь от кода до продакшена в одном репозитории.

### Как микросервис
Дёрни HTTP из бота, фронта или cron:

```text
GET /time
GET /date
GET /convert?time=15.00&timezone=Екатеринбург
GET /health
```

### Как шаблон деплоя
Скопируй `Dockerfile` + `.github/workflows/deploy.yml`, подставь свои секреты — и тот же пайплайн заработает для другого FastAPI-приложения.

### Живой стенд (пример)
После деплоя API доступен на VPS, например:

- Health: `http://<HOST>:8000/health`
- Docs: `http://<HOST>:8000/docs`

---

## Возможности

- Время сервера в ISO, unix timestamp и человекочитаемом виде
- Дата с разбивкой по year/month/day и днём недели
- Конвертация **UTC → часовой пояс** (город по-русски или IANA-имя)
- Health-check для мониторинга и балансировщиков
- Docker-образ из одного `Dockerfile`
- CI/CD: сборка → GHCR → SSH-деплой

---

## Быстрый старт

### Требования

- Python **3.11+**
- (опционально) Docker
- (для деплоя) GitHub-репозиторий и VPS с Docker

### Установка

```powershell
git clone https://github.com/nifontovoleg/test-actions.git
cd test-actions
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy env.example .env
```

### Запуск локально

```powershell
python main.py
```

или:

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

| Что | URL |
|-----|-----|
| API | http://127.0.0.1:8000 |
| Swagger | http://127.0.0.1:8000/docs |
| ReDoc | http://127.0.0.1:8000/redoc |

### Запуск в Docker

```powershell
docker build -t time-server-api .
docker run -d --name time-server -p 8000:8000 time-server-api
```

Проверка:

```powershell
curl http://127.0.0.1:8000/health
```

---

## Структура репозитория

```text
.
├── main.py                      # FastAPI-приложение
├── requirements.txt             # зависимости
├── env.example                  # пример переменных окружения
├── Dockerfile                   # образ приложения
├── .dockerignore
├── .gitignore
├── README.md                    # этот файл
├── DEPLOYMENT.md                # деплой и секреты
└── .github/workflows/deploy.yml # CI/CD: build → GHCR → SSH
```

| Файл | Роль |
|------|------|
| `main.py` | Эндпоинты и бизнес-логика времени |
| `DEPLOYMENT.md` | Секреты, SSH, GHCR, troubleshooting |
| `deploy.yml` | Две джобы: сборка образа и выкат на сервер |

---

## API

Базовый префикс: `/`

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/` | Приветствие и ссылка на docs |
| `GET` | `/time` | Текущее время сервера |
| `GET` | `/date` | Текущая дата сервера |
| `GET` | `/convert` | Конвертация времени из UTC |
| `GET` | `/health` | Статус сервиса |

Интерактивная документация всегда здесь: [`/docs`](http://127.0.0.1:8000/docs).

### `GET /time`

```json
{
  "current_time": "2026-07-21T20:17:00.123456",
  "timestamp": 1753112220.123456,
  "formatted_time": "2026-07-21 20:17:00",
  "timezone": "UTC"
}
```

### `GET /date`

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

### `GET /convert`

Переводит время из **UTC** в указанный пояс.

| Параметр | Пример | Описание |
|----------|--------|----------|
| `time` | `15.00` | Время UTC (`15.00`, `15:00`, `15:00:00`) |
| `timezone` | `Екатеринбург` | Город или IANA (`Asia/Yekaterinburg`) |

```text
GET /convert?time=15.00&timezone=Екатеринбург
```

```json
{
  "input_time_utc": "15:00:00",
  "timezone": "Asia/Yekaterinburg",
  "converted_time": "20:00:00",
  "converted_datetime": "2026-07-21T20:00:00+05:00"
}
```

Логика: `15:00 UTC` + Екатеринбург (`UTC+5`) → `20:00`.

Поддерживаемые алиасы городов (часть списка):  
Екатеринбург, Москва, СПб, Новосибирск, Красноярск, Владивосток, Лондон, Берлин, Токио, Нью-Йорк — либо любое валидное IANA-имя.

### `GET /health`

```json
{
  "status": "healthy",
  "timestamp": "2026-07-21T19:19:28.224821"
}
```

---

## Переменные окружения

Скопируй `env.example` → `.env`:

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `HOST` | `0.0.0.0` | Интерфейс прослушивания |
| `PORT` | `8000` | Порт |
| `DEBUG` | `false` | `true` включает reload у uvicorn |

`.env` в git не коммитится.

---

## CI/CD и деплой

Краткий путь:

```text
push в main
   → Docker build
   → push в ghcr.io/<owner>/<repo>
   → SSH на VPS
   → docker pull + run (контейнер time-server, порт 8000)
```

Подробно (секреты, SSH-ключ, GHCR, ошибки): **[DEPLOYMENT.md](DEPLOYMENT.md)**

Нужные секреты репозитория: `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY` (+ опционально `SSH_PORT`).

---

## Как развивать проект

Идеи по приоритету — от простого к серьёзному:

### Ближайшие улучшения
1. **Больше поясов** — расширить словарь городов или отдать список через `GET /timezones`
2. **Дата в `/convert`** — принимать не только время, но и полную дату (`2026-07-21T15:00`)
3. **Обратная конвертация** — из локального пояса обратно в UTC
4. **Тесты** — `pytest` + `httpx`/`TestClient` на `/time`, `/date`, `/convert`
5. **Линтеры в CI** — ruff / mypy отдельной job перед деплоем

### Продуктовые направления
- Rate limit и простой API-key для публичного стенда
- Метрики (`/metrics`) и алерты по `/health`
- Nginx/Caddy + HTTPS перед контейнером
- Версионирование API (`/api/v1/...`)
- Отдача времени для нескольких серверов/регионов сразу

### Инфраструктура
- Staging-окружение (деплой с `develop`)
- Откат на предыдущий SHA-тег образа
- docker compose для локальной связки api + reverse-proxy

Паттерн развития: **сначала стабильный контракт API и тесты**, потом обвязка (auth, https, мониторинг).

---

## Примеры запросов

```powershell
# локально
curl http://127.0.0.1:8000/time
curl http://127.0.0.1:8000/date
curl "http://127.0.0.1:8000/convert?time=15.00&timezone=Екатеринбург"
curl http://127.0.0.1:8000/health
```

```powershell
# с Python
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/time').read().decode())"
```

---

## Стек

| Слой | Технологии |
|------|------------|
| API | Python 3.11+, FastAPI, Uvicorn |
| Время | `datetime`, `zoneinfo` |
| Конфиг | `python-dotenv` |
| Контейнер | Docker (`python:3.11-slim`) |
| CI/CD | GitHub Actions, GHCR, SSH deploy |

---

## Лицензия и вклад

Учебно-практический репозиторий. Можно форкать, менять под себя, забирать workflow деплоя.

Если добавляешь фичу:
1. ветка от `main`
2. правки + обновление README при изменении API
3. PR или merge в `main` → автоматический деплой

---

## Полезные ссылки

- [DEPLOYMENT.md](DEPLOYMENT.md) — деплой, секреты, troubleshooting
- Swagger UI — `/docs`
- FastAPI — https://fastapi.tiangolo.com/
- GitHub Container Registry — https://docs.github.com/packages/learn-github-packages
