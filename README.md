# Argo Spotify Integration

Django-приложение для синхронизации данных Spotify пользователей.<br>
Стек: Django, Celery, PostgreSQL, Redis.

## Features

- Авторизация через Spotify OAuth 2.0, бэкенд авторизации основан на сессиях, авторизация доступна в том числе в DRF.
- Токены хранятся в зашифрованном виде и не доступны никому без ключа шифрования. Метод шифрования - Fernet.
- Токены обновляются автоматически и при необходимости в ручном режиме.
- State при OAuth-запросах генерируется и хранится в Redis вместо текущей сессии для доступа в продакшене вне зависиости
  от инстанса приложения.
- Синхронизация данных пользователя Spotify осуществляется в ручном и атоматическом режиме..
- При синхронизации данных о треках запросы к Spotify API осуществляются в параллельных потоках для ускорения процесса.
  Предполагается, что у пользователя может быть 10000 записей, а Спотифай позволяет за раз получить только 50 треков.
- Синхронизация данных в БД осущеставляется в рамках одной транзакции, при больших объемах данные записываются батчами.
- Для быстрого доступа к данным используются составные HASH-индексы в PostgreSQL, в том числе для быстрого поиска уже
  существующих записей.

## Prerequisites

- Docker & Docker Compose
- Python 3.12+
- [UV manager](https://github.com/astral-sh/uv) for running the Django application
- Ruff for code linting
- Celery for background tasks
- [cryptography](https://pypi.org/project/cryptography/) (for generating FERNET_KEY)
- [Redis](https://redis.io/) (for state management)
- [PostgreSQL](https://www.postgresql.org/) (for database storage)
- [Spotify Developer Account](https://developer.spotify.com/) (for API access)

Here is a Markdown-formatted API section for your `README.md`:

## API Endpoints

All endpoints are prefixed with `/spotify/`.

| Endpoint                   | Method | Description                                  | Auth Required |
|----------------------------|--------|----------------------------------------------|:-------------:|
| `/spotify/auth/`           | GET    | Start Spotify OAuth2 authentication flow     |      Yes      |
| `/spotify/callback/`       | GET    | OAuth2 callback endpoint for Spotify         |      No       |
| `/spotify/refresh/`        | POST   | Refresh Spotify access token                 |      Yes      |
| `/spotify/disconnect/`     | POST   | Disconnect Spotify account from user profile |      Yes      |
| `/spotify/sync/tracks/`    | POST   | Sync user’s Spotify tracks                   |      Yes      |
| `/spotify/sync/playlists/` | POST   | Sync user’s Spotify playlists                |      Yes      |
| `/spotify/sync/following/` | POST   | Sync user’s followed artists                 |      Yes      |


## Makefile Commands

| Command               | Description                                             |
|-----------------------|---------------------------------------------------------|
| `make start`          | Start all services with Docker Compose                  |
| `make stop`           | Stop all services                                       |
| `make restart`        | Restart all services                                    |
| `make restart-celery` | Restart only the Celery service                         |
| `make ruff-fix`       | Run Ruff linter with `--fix` in the `project` directory |
| `make gen-env`        | Generate `.env` from `env.sample` with a new FERNET_KEY |
| `make help`           | Show all available make commands                        |

## TODO
Написать тесты<br>
Добавить в БД данные о синхронизациях

