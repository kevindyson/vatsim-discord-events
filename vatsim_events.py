import os
import json
import urllib.request
from datetime import datetime, timezone

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

DATA_FILE = "published_events.json"

VATSIM_URL = "https://my.vatsim.net/api/v2/events/latest"


def get_events():
    request = urllib.request.Request(
        VATSIM_URL,
        headers={
            "User-Agent": "AeroClub-MSFS-VATSIM-Bot/1.0",
            "Accept": "application/json"
        }
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def load_published():
    if not os.path.exists(DATA_FILE):
        return set()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        return set(str(event_id) for event_id in data)

    except Exception:
        return set()


def save_published(published):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(
            sorted(published),
            file,
            indent=2
        )


def format_date(date_string):
    if not date_string:
        return "No especificado"

    try:
        date = datetime.fromisoformat(
            date_string.replace("Z", "+00:00")
        )

        return date.strftime("%d/%m/%Y %H:%M UTC")

    except Exception:
        return date_string


def send_to_discord(event):
    name = event.get("name", "Evento VATSIM")
    link = event.get("link", "")

    start_time = format_date(
        event.get("start_time")
    )

    end_time = format_date(
        event.get("end_time")
    )

    short_description = event.get(
        "short_description",
        ""
    )

    banner = event.get(
        "banner",
        ""
    )

    airports = event.get(
        "airports",
        []
    )

    airport_names = []

    for airport in airports:
        icao = airport.get("icao")

        if icao:
            airport_names.append(icao)

    airport_text = ", ".join(airport_names)

    embed = {
        "title": f"🛫 Nuevo evento VATSIM",
        "description": (
            f"**{name}**\n\n"
            f"{short_description[:3500]}"
        ),
        "fields": [
            {
                "name": "📅 Inicio",
                "value": start_time,
                "inline": True
            },
            {
                "name": "⏰ Fin",
                "value": end_time,
                "inline": True
            }
        ],
        "footer": {
            "text": "AeroClub MSFS • VATSIM Events"
        }
    }

    if airport_text:
        embed["fields"].append(
            {
                "name": "🛫 Aeropuertos",
                "value": airport_text[:1024],
                "inline": False
            }
        )

    if link:
        embed["url"] = link

    if banner:
        embed["image"] = {
            "url": banner
        }

    message = {
        "username": "AeroClub MSFS",
        "embeds": [embed]
    }

    data = json.dumps(
        message
    ).encode("utf-8")

    request = urllib.request.Request(
        WEBHOOK_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "AeroClub-MSFS-VATSIM-Bot/1.0"
        },
        method="POST"
    )

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:

        if response.status not in (200, 204):
            raise RuntimeError(
                f"Discord respondió con HTTP {response.status}"
            )


def main():

    print("Consultando eventos de VATSIM...")

    response = get_events()

    events = response.get(
        "data",
        []
    )

    print(
        f"Eventos encontrados: {len(events)}"
    )

    published = load_published()

    # Primera ejecución:
    # guardamos los eventos existentes para no
    # llenar Discord con eventos antiguos.
    if not published:

        for event in events:

            event_id = str(
                event.get("id", "")
            )

            if event_id:
                published.add(event_id)

        save_published(published)

        print(
            "Primera ejecución completada."
        )

        print(
            "Los eventos actuales han sido guardados."
        )

        print(
            "A partir de ahora solo se publicarán eventos nuevos."
        )

        return

    new_events = []

    for event in events:

        event_id = str(
            event.get("id", "")
        )

        if not event_id:
            continue

        if event_id in published:
            continue

        new_events.append(
            (event_id, event)
        )

    print(
        f"Eventos nuevos: {len(new_events)}"
    )

    for event_id, event in new_events:

        try:

            print(
                f"Publicando: {event.get('name', 'Evento VATSIM')}"
            )

            send_to_discord(event)

            published.add(
                event_id
            )

            print(
                "Publicado correctamente."
            )

        except Exception as error:

            print(
                f"Error publicando {event_id}: {error}"
            )

    save_published(published)

    print("Proceso terminado.")


if __name__ == "__main__":
    main()
