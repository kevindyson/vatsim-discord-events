import os
import json
import urllib.request
from datetime import datetime, timezone

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
DATA_FILE = "published_events.json"

VATSIM_URL = "https://my.vatsim.net/api/v2/events/view"


def get_events():
    request = urllib.request.Request(
        VATSIM_URL,
        headers={"User-Agent": "AeroClub-MSFS-VATSIM-Bot/1.0"}
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def load_published():
    if not os.path.exists(DATA_FILE):
        return set()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_published(published):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(published), f, indent=2)


def send_to_discord(event):
    name = event.get("name", "Evento VATSIM")
    description = event.get("description", "")
    link = event.get("url", "")

    start = event.get("start", "")
    end = event.get("end", "")

    message = {
        "username": "AeroClub MSFS | VATSIM",
        "embeds": [
            {
                "title": f"🛫 Nuevo evento VATSIM: {name}",
                "description": description[:4000] if description else "Nuevo evento publicado en VATSIM.",
                "fields": [
                    {
                        "name": "📅 Inicio",
                        "value": start or "No especificado",
                        "inline": True
                    },
                    {
                        "name": "⏰ Finalización",
                        "value": end or "No especificado",
                        "inline": True
                    }
                ],
                "url": link if link else None
            }
        ]
    }

    # Discord no acepta valores None en algunos campos
    if not link:
        message["embeds"][0].pop("url", None)

    data = json.dumps(message).encode("utf-8")

    request = urllib.request.Request(
        WEBHOOK_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "AeroClub-MSFS-VATSIM-Bot/1.0"
        },
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return response.status


def main():
    events = get_events()
    published = load_published()

    # La API puede devolver una lista directamente o dentro de "data"
    if isinstance(events, dict):
        events = events.get("data", [])

    new_events = []

    for event in events:
        event_id = str(
            event.get("id")
            or event.get("event_id")
            or event.get("slug")
            or ""
        )

        if not event_id:
            continue

        if event_id in published:
            continue

        new_events.append((event_id, event))

    # Publicar primero los eventos nuevos
    for event_id, event in new_events:
        try:
            send_to_discord(event)
            published.add(event_id)
            print(f"Publicado: {event.get('name', 'Evento VATSIM')}")
        except Exception as error:
            print(f"Error publicando evento {event_id}: {error}")

    save_published(published)


if __name__ == "__main__":
    main()
