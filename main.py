import os
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query

load_dotenv()

app = FastAPI(
    title="Time Server API",
    description="Простое API для получения текущего времени сервера",
    version="1.0.0",
)

# Русские названия городов → IANA timezone
TIMEZONE_ALIASES: dict[str, str] = {
    "екатеринбург": "Asia/Yekaterinburg",
    "екб": "Asia/Yekaterinburg",
    "москва": "Europe/Moscow",
    "мск": "Europe/Moscow",
    "санкт-петербург": "Europe/Moscow",
    "спб": "Europe/Moscow",
    "новосибирск": "Asia/Novosibirsk",
    "красноярск": "Asia/Krasnoyarsk",
    "иркутск": "Asia/Irkutsk",
    "владивосток": "Asia/Vladivostok",
    "калининград": "Europe/Kaliningrad",
    "самара": "Europe/Samara",
    "омск": "Asia/Omsk",
    "якутск": "Asia/Yakutsk",
    "хабаровск": "Asia/Vladivostok",
    "utc": "UTC",
    "лондон": "Europe/London",
    "берлин": "Europe/Berlin",
    "париж": "Europe/Paris",
    "токио": "Asia/Tokyo",
    "нью-йорк": "America/New_York",
}


def resolve_timezone(name: str) -> ZoneInfo:
    key = name.strip().lower().replace("ё", "е")
    iana = TIMEZONE_ALIASES.get(key, name.strip())
    try:
        return ZoneInfo(iana)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Неизвестный часовой пояс: {name!r}. "
                "Укажите город (например Екатеринбург) или IANA-имя (Asia/Yekaterinburg)."
            ),
        ) from exc


def parse_utc_time(value: str) -> datetime:
    """Парсит время вроде 15.00, 15:00, 15:00:00 как сегодняшнюю дату в UTC."""
    raw = value.strip()
    match = re.fullmatch(r"(\d{1,2})[.:](\d{2})(?:[.:](\d{2}))?", raw)
    if not match:
        raise HTTPException(
            status_code=400,
            detail="Неверный формат времени. Примеры: 15.00, 15:00, 15:00:00",
        )

    hour = int(match.group(1))
    minute = int(match.group(2))
    second = int(match.group(3) or 0)

    if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
        raise HTTPException(status_code=400, detail="Некорректные значения времени")

    today = datetime.now(timezone.utc).date()
    return datetime(
        today.year,
        today.month,
        today.day,
        hour,
        minute,
        second,
        tzinfo=timezone.utc,
    )


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "Добро пожаловать в Time Server API",
        "docs": "/docs",
    }


@app.get("/time")
async def get_current_time() -> dict[str, str | float | None]:
    now = datetime.now()
    return {
        "current_time": now.isoformat(),
        "timestamp": now.timestamp(),
        "formatted_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": str(now.astimezone().tzinfo),
    }


@app.get("/date")
async def get_current_date() -> dict[str, str | int]:
    today = datetime.now().date()
    return {
        "date": today.isoformat(),
        "formatted_date": today.strftime("%d.%m.%Y"),
        "year": today.year,
        "month": today.month,
        "day": today.day,
        "weekday": today.strftime("%A"),
    }


@app.get("/convert")
async def convert_time(
    time: str = Query(..., description="Время UTC, например 15.00 или 15:00"),
    timezone_name: str = Query(
        ...,
        alias="timezone",
        description="Часовой пояс: Екатеринбург или Asia/Yekaterinburg",
    ),
) -> dict[str, str]:
    utc_dt = parse_utc_time(time)
    tz = resolve_timezone(timezone_name)
    local_dt = utc_dt.astimezone(tz)

    return {
        "input_time_utc": utc_dt.strftime("%H:%M:%S"),
        "timezone": str(tz),
        "converted_time": local_dt.strftime("%H:%M:%S"),
        "converted_datetime": local_dt.isoformat(),
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"}
    uvicorn.run("main:app", host=host, port=port, reload=debug)
