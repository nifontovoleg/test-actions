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

# Названия городов/поясов → IANA timezone
TIMEZONE_ALIASES: dict[str, str] = {
    "utc": "UTC",
    "gmt": "UTC",
    "москва": "Europe/Moscow",
    "moscow": "Europe/Moscow",
    "екатеринбург": "Asia/Yekaterinburg",
    "екб": "Asia/Yekaterinburg",
    "yekaterinburg": "Asia/Yekaterinburg",
    "ekaterinburg": "Asia/Yekaterinburg",
    "новосибирск": "Asia/Novosibirsk",
    "novosibirsk": "Asia/Novosibirsk",
    "красноярск": "Asia/Krasnoyarsk",
    "krasnoyarsk": "Asia/Krasnoyarsk",
    "иркутск": "Asia/Irkutsk",
    "irkutsk": "Asia/Irkutsk",
    "владивосток": "Asia/Vladivostok",
    "vladivostok": "Asia/Vladivostok",
    "калининград": "Europe/Kaliningrad",
    "kaliningrad": "Europe/Kaliningrad",
    "самара": "Europe/Samara",
    "samara": "Europe/Samara",
    "омск": "Asia/Omsk",
    "omsk": "Asia/Omsk",
    "камчатка": "Asia/Kamchatka",
    "kamchatka": "Asia/Kamchatka",
    "лондон": "Europe/London",
    "london": "Europe/London",
    "берлин": "Europe/Berlin",
    "berlin": "Europe/Berlin",
    "токио": "Asia/Tokyo",
    "tokyo": "Asia/Tokyo",
    "нью-йорк": "America/New_York",
    "new-york": "America/New_York",
    "new_york": "America/New_York",
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
                "Примеры: Екатеринбург, Москва, UTC, Asia/Yekaterinburg"
            ),
        ) from exc


def parse_utc_time(value: str) -> datetime:
    """Парсит время UTC из строки: 15:00, 15.00, 15:00:00, ISO datetime."""
    raw = value.strip()

    # ISO / datetime
    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M",
    ):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    # 15:00 / 15.00 / 15:00:00 / 15.00.00
    match = re.fullmatch(
        r"(?P<h>\d{1,2})[:.](?P<m>\d{2})(?:[:.](?P<s>\d{2}))?",
        raw,
    )
    if match:
        hour = int(match.group("h"))
        minute = int(match.group("m"))
        second = int(match.group("s") or 0)
        if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
            raise HTTPException(status_code=400, detail=f"Некорректное время: {value!r}")
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

    raise HTTPException(
        status_code=400,
        detail=f"Не удалось разобрать время: {value!r}. Примеры: 15:00, 15.00, 2026-07-21T15:00:00",
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
async def convert_timezone(
    time: str = Query(..., description="Время в UTC, например 15:00 или 15.00"),
    timezone_name: str = Query(
        ...,
        alias="timezone",
        description="Часовой пояс: Екатеринбург, Москва или Asia/Yekaterinburg",
    ),
) -> dict[str, str]:
    utc_dt = parse_utc_time(time)
    tz = resolve_timezone(timezone_name)
    local_dt = utc_dt.astimezone(tz)

    return {
        "input_time_utc": utc_dt.strftime("%H:%M:%S"),
        "timezone": timezone_name,
        "iana": str(tz),
        "converted_time": local_dt.strftime("%H:%M:%S"),
        "converted_datetime": local_dt.isoformat(),
        "utc_offset": local_dt.strftime("%z"),
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
