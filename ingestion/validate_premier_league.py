import pandas as pd
from pathlib import Path


DATA_DIR = Path("data/raw/premier_league")

EXPECTED_COLUMNS = {
    "Date",
    "HomeTeam",
    "AwayTeam",
    "FTHG",
    "FTAG",
    "FTR",
}


for file in DATA_DIR.glob("*.csv"):

    print(f"\nValidando: {file.name}")

    df = pd.read_csv(file)

    # 1. Arquivo não vazio
    assert not df.empty, "Arquivo vazio"

    # 2. Colunas obrigatórias
    missing_columns = EXPECTED_COLUMNS - set(df.columns)

    assert not missing_columns, (
        f"Colunas ausentes: {missing_columns}"
    )

    # 3. Times preenchidos
    assert df["HomeTeam"].notna().all()
    assert df["AwayTeam"].notna().all()

    # 4. Resultado preenchido
    assert df["FTR"].notna().all()

    # 5. Quantidade esperada de partidas
    assert len(df) == 380, (
        f"Esperávamos 380 partidas, encontramos {len(df)}"
    )

    print(f"OK - {len(df)} partidas")