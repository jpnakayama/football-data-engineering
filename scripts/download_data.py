import requests
from pathlib import Path


BASE_URL = "https://www.football-data.co.uk/mmz4281"

SEASONS = {
    "2022-23": "2223",
    "2023-24": "2324",
    "2024-25": "2425",
    "2025-26": "2526",
}


OUTPUT_DIR = Path("data/raw/premier_league")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


for season, code in SEASONS.items():

    url = f"{BASE_URL}/{code}/E0.csv"
    output_file = OUTPUT_DIR / f"{season}.csv"

    print(f"Baixando {season}...")

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    output_file.write_bytes(response.content)

    print(f"OK: {output_file}")