from pathlib import Path

import boto3


BUCKET_NAME = "football-data-engineering-dev"
AWS_PROFILE = "football-dev"

DATA_DIR = Path("data/raw/premier_league")


def upload_files():
    session = boto3.Session(profile_name=AWS_PROFILE)

    s3 = session.client(
        "s3",
        region_name="us-east-2"
    )

    files = sorted(DATA_DIR.glob("*.csv"))

    if not files:
        raise FileNotFoundError(
            f"Nenhum arquivo CSV encontrado em {DATA_DIR}"
        )

    for file in files:
        season = file.stem

        s3_key = (
            f"raw/premier_league/"
            f"season={season}/"
            f"matches.csv"
        )

        print(f"Enviando {file}...")
        print(f"Destino: s3://{BUCKET_NAME}/{s3_key}")

        s3.upload_file(
            str(file),
            BUCKET_NAME,
            s3_key
        )

        print("Upload concluído.\n")


if __name__ == "__main__":
    upload_files()