
from pathlib import Path

import joblib
import pandas as pd


# Raiz do repositório
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
MODEL_PATH = BASE_DIR / "models" / "football_model.joblib"


def load_parquet(relative_path):
    """Carrega um dataset Parquet particionado."""

    path = DATA_DIR / relative_path

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset não encontrado: {path}"
        )

    return pd.read_parquet(path, engine="pyarrow")


def load_matches():
    """Carrega as partidas históricas."""

    df = load_parquet("processed/premier_league")
    df["match_date"] = pd.to_datetime(df["match_date"])

    return df.sort_values("match_date").reset_index(drop=True)


def load_team_stats():
    """Carrega estatísticas por equipe e temporada."""

    return load_parquet("analytics/team_season_stats")


def load_match_features():
    """Carrega o dataset utilizado no treinamento."""

    df = load_parquet("features/match_features")
    df["match_date"] = pd.to_datetime(df["match_date"])

    return df.sort_values("match_date").reset_index(drop=True)


def load_team_history():
    """Carrega o histórico de partidas por equipe."""

    df = load_parquet("features/team_match_history")
    df["match_date"] = pd.to_datetime(df["match_date"])

    return df.sort_values("match_date").reset_index(drop=True)


def load_model():
    """Carrega o modelo treinado e seus metadados."""

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Modelo não encontrado: {MODEL_PATH}"
        )

    artifact = joblib.load(MODEL_PATH)

    required_keys = {
        "model",
        "features",
        "model_name",
        "metrics",
    }

    if not required_keys.issubset(artifact):
        raise ValueError(
            "O artefato do modelo está incompleto."
        )

    return artifact
