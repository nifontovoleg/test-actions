# Deployment

Деплой Time Server API через GitHub Actions: сборка Docker-образа → push в GHCR → SSH на сервер → pull и запуск контейнера.

## Архитектура

```text
push в main / workflow_dispatch
        │
        ▼
┌─────────────────────┐
│  Job 1: build-and-  │
│  push               │
│  • docker build     │
│  • push → ghcr.io   │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Job 2: deploy      │
│  • SSH на сервер    │
│  • docker login     │
│  • pull + run       │
└─────────────────────┘
```

Workflow-файл: `.github/workflows/deploy.yml`

## Образ

| Параметр | Значение |
|----------|----------|
| Registry | `ghcr.io` |
| Имя | `ghcr.io/<owner>/<repo>` (lowercase) |
| Теги | `latest`, `<commit-sha>` |
| Контейнер на сервере | `time-server` |
| Порт | `8000` |

Пример: `ghcr.io/myuser/actions:latest`

## Требования к серверу

- Docker установлен и доступен пользователю SSH
- Открыт порт `8000` (или прокси перед контейнером)
- Исходящий доступ к `ghcr.io`

## Секреты GitHub

Settings → Secrets and variables → Actions:

| Секрет | Обязательный | Описание |
|--------|--------------|----------|
| `SSH_HOST` | да | IP или hostname сервера |
| `SSH_USER` | да | SSH-пользователь |
| `SSH_PRIVATE_KEY` | да | Приватный ключ (полный PEM, включая `BEGIN/END`) |
| `SSH_PASSPHRASE` | нет | Пароль ключа, если ключ защищён passphrase |
| `SSH_PORT` | нет | SSH-порт, по умолчанию `22` |
| `GHCR_USERNAME` | нет* | Больше не обязателен: deploy тянет образ через `GITHUB_TOKEN` |
| `GHCR_TOKEN` | нет* | Больше не обязателен: deploy тянет образ через `GITHUB_TOKEN` |

\* Секреты `GHCR_*` можно оставить, но текущий workflow их не использует.

### Как создать GHCR_TOKEN (опционально)

Текущий workflow для pull на сервере использует встроенный `GITHUB_TOKEN`.
Отдельный PAT нужен только если будешь тянуть образ вручную с сервера.

### SSH-ключ

На сервере публичный ключ в `~/.ssh/authorized_keys`, приватный — в `SSH_PRIVATE_KEY`.

## Запуск деплоя

Автоматически при push в ветку `main`, либо вручную:

Actions → **Build and Deploy** → **Run workflow**

## Что делает деплой на сервере

```bash
docker login ghcr.io
docker pull ghcr.io/<owner>/<repo>:latest
docker stop time-server || true
docker rm time-server || true
docker run -d \
  --name time-server \
  --restart unless-stopped \
  -p 8000:8000 \
  ghcr.io/<owner>/<repo>:latest
docker image prune -f
```

## Проверка после деплоя

```bash
curl http://<SSH_HOST>:8000/health
curl http://<SSH_HOST>:8000/time
curl http://<SSH_HOST>:8000/date
```

На сервере:

```bash
docker ps --filter name=time-server
docker logs time-server
```

## Локальная сборка (без CI)

```bash
docker build -t time-server-api .
docker run -d --name time-server -p 8000:8000 time-server-api
```

## Troubleshooting

| Проблема | Что проверить |
|----------|----------------|
| Push в GHCR падает с 403 | У workflow есть `packages: write`; репозиторий не блокирует packages |
| Pull на сервере 401/403 | Верны `GHCR_USERNAME` / `GHCR_TOKEN`; у token есть `read:packages` |
| `ssh: overflow reading version string` | На том хосте/порту **нет SSH**. Обычно неверный `SSH_HOST` или `SSH_PORT` (см. ниже) |
| SSH timeout / connection refused | `SSH_HOST`, `SSH_PORT`, firewall, ключ в `authorized_keys` |
| Порт занят | `docker ps`, другой процесс на `8000` |
| Контейнер сразу падает | `docker logs time-server` |

### `ssh: overflow reading version string`

Клиент подключился, но ответ — не баннер SSH (часто HTTP/TLS с портов 80/443/8000).

Проверь секреты:

| Секрет | Как должно быть | Как не должно |
|--------|-----------------|---------------|
| `SSH_HOST` | `203.0.113.10` или `vps.example.com` | `https://...`, `ssh://...`, URL с путём, IP от Cloudflare/прокси сайта |
| `SSH_PORT` | `22` или свой SSH-порт (например `2222`) | `8000`, `80`, `443`, пусто с пробелами/переносами |
| `SSH_USER` | `root` / `ubuntu` / и т.п. | email |

Локальная проверка (с твоего ПК):

```bash
ssh -i ./key -p 22 USER@HOST
```

### `unable to authenticate, attempted methods [none publickey]`

Хост и порт ок, сервер отклонил ключ.

Проверь по порядку:

1. **`SSH_USER`** — тот пользователь, для которого лежит ключ в `~/.ssh/authorized_keys` (часто `root` или `ubuntu`, не GitHub-логин).
2. **`SSH_PRIVATE_KEY`** — именно **приватный** ключ целиком:
   ```text
   -----BEGIN OPENSSH PRIVATE KEY-----
   ...
   -----END OPENSSH PRIVATE KEY-----
   ```
   или `BEGIN RSA PRIVATE KEY`. Не публичный (`.pub`), без кавычек вокруг, без лишних пробелов в начале строк.
3. На сервере публичная пара должна быть в `authorized_keys`:
   ```bash
   # на сервере, под тем же USER
   mkdir -p ~/.ssh
   chmod 700 ~/.ssh
   echo "ssh-ed25519 AAAA... comment" >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```
4. Если ключ с **passphrase** — добавь секрет `SSH_PASSPHRASE` и в workflow:
   ```yaml
   passphrase: ${{ secrets.SSH_PASSPHRASE }}
   ```
5. Локально тем же ключом и юзером:
   ```bash
   ssh -i ./private_key -p 22 USER@HOST
   ```
   Если локально не пускает — чини ключ/authorized_keys, не Actions.
