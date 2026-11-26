"""Baixa os dados brutos da parte 2 (Data Warehouse).

Fontes:
- Transfermarkt datasets (dcaribou/transfermarkt-datasets, licença CC0),
  pelos links públicos indicados no README do dataset.
- Football-Data.co.uk: partidas, estatísticas e odds das cinco grandes ligas
  da Europa, temporadas 2012-13 a 2025-26.

Os arquivos vão para data/raw/, que não é versionado.
"""

from pathlib import Path

import requests

TRANSFERMARKT_BASE_URL = "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data"
TRANSFERMARKT_TABLES = [
    "competitions",
    "clubs",
    "players",
    "games",
    "club_games",
    "appearances",
    "game_events",
    "player_valuations",
    "transfers",
    "countries",
    "national_teams",
]

FOOTBALL_DATA_BASE_URL = "https://www.football-data.co.uk/mmz4281"
# Código da divisão no Football-Data.co.uk -> nome da pasta local.
FOOTBALL_DATA_LEAGUES = {
    "E0": "premier_league",
    "SP1": "la_liga",
    "D1": "bundesliga",
    "I1": "serie_a",
    "F1": "ligue_1",
}
FIRST_SEASON_START = 2012
LAST_SEASON_START = 2025

TRANSFERMARKT_DIR = Path("data/raw/transfermarkt")
FOOTBALL_DATA_DIR = Path("data/raw/football_data")


def download(url: str, output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with output_file.open("wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
    size_mb = output_file.stat().st_size / 1024 / 1024
    print(f"OK: {output_file} ({size_mb:.1f} MB)")


def season_codes() -> list[tuple[str, str]]:
    """Retorna pares (rótulo '2012-13', código '1213')."""
    seasons = []
    for start in range(FIRST_SEASON_START, LAST_SEASON_START + 1):
        end = start + 1
        seasons.append((f"{start}-{str(end)[-2:]}", f"{str(start)[-2:]}{str(end)[-2:]}"))
    return seasons


def main() -> None:
    for table in TRANSFERMARKT_TABLES:
        download(
            f"{TRANSFERMARKT_BASE_URL}/{table}.csv.gz",
            TRANSFERMARKT_DIR / f"{table}.csv.gz",
        )
    for division, league in FOOTBALL_DATA_LEAGUES.items():
        for label, code in season_codes():
            download(
                f"{FOOTBALL_DATA_BASE_URL}/{code}/{division}.csv",
                FOOTBALL_DATA_DIR / league / f"{label}.csv",
            )


if __name__ == "__main__":
    main()
