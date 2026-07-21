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
    description="Server time, date, and UTC → timezone conversion API",
    version="1.0.0",
)

# City aliases → IANA timezone (English + Russian)
TIMEZONE_ALIASES: dict[str, str] = {
    "yekaterinburg": "Asia/Yekaterinburg",
    "ekaterinburg": "Asia/Yekaterinburg",
    "екатеринбург": "Asia/Yekaterinburg",
    "екб": "Asia/Yekaterinburg",
    "moscow": "Europe/Moscow",
    "москва": "Europe/Moscow",
    "мск": "Europe/Moscow",
    "saint petersburg": "Europe/Moscow",
    "st petersburg": "Europe/Moscow",
    "санкт-петербург": "Europe/Moscow",
    "спб": "Europe/Moscow",
    "novosibirsk": "Asia/Novosibirsk",
    "новосибирск": "Asia/Novosibirsk",
    "krasnoyarsk": "Asia/Krasnoyarsk",
    "красноярск": "Asia/Krasnoyarsk",
    "irkutsk": "Asia/Irkutsk",
    "иркутск": "Asia/Irkutsk",
    "vladivostok": "Asia/Vladivostok",
    "владивосток": "Asia/Vladivostok",
    "kaliningrad": "Europe/Kaliningrad",
    "калининград": "Europe/Kaliningrad",
    "samara": "Europe/Samara",
    "самара": "Europe/Samara",
    "omsk": "Asia/Omsk",
    "омск": "Asia/Omsk",
    "yakutsk": "Asia/Yakutsk",
    "якутск": "Asia/Yakutsk",
    "khabarovsk": "Asia/Vladivostok",
    "хабаровск": "Asia/Vladivostok",
    "utc": "UTC",
    "london": "Europe/London",
    "лондон": "Europe/London",
    "berlin": "Europe/Berlin",
    "берлин": "Europe/Berlin",
    "paris": "Europe/Paris",
    "париж": "Europe/Paris",
    "tokyo": "Asia/Tokyo",
    "токио": "Asia/Tokyo",
    "new york": "America/New_York",
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
                f"Unknown timezone: {name!r}. "
                "Use a city name (e.g. Yekaterinburg) or an IANA id (Asia/Yekaterinburg)."
            ),
        ) from exc


def parse_utc_time(value: str) -> datetime:
    """Parse times like 15.00, 15:00, 15:00:00 as today's date in UTC."""
    raw = value.strip()
    match = re.fullmatch(r"(\d{1,2})[.:](\d{2})(?:[.:](\d{2}))?", raw)
    if not match:
        raise HTTPException(
            status_code=400,
            detail="Invalid time format. Examples: 15.00, 15:00, 15:00:00",
        )

    hour = int(match.group(1))
    minute = int(match.group(2))
    second = int(match.group(3) or 0)

    if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
        raise HTTPException(status_code=400, detail="Invalid time values")

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
        "message": "Welcome to Time Server API",
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
    time: str = Query(..., description="UTC time, e.g. 15.00 or 15:00"),
    timezone_name: str = Query(
        ...,
        alias="timezone",
        description="Timezone: Yekaterinburg or Asia/Yekaterinburg",
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
