
import os
from pathlib import Path

import joblib
import pandas as pd

from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    log_loss,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ML_DATASET_PATH = os.getenv(
    "ML_DATASET_PATH",
    "/data/features/match_features",
)

MODEL_PATH = os.getenv(
    "MODEL_PATH",
    "/app/models/football_model.joblib",
)

FEATURE_COLUMNS = [
    "home_points_last_5",
    "home_goals_avg_last_5",
    "home_conceded_avg_last_5",
    "home_win_rate_last_5",
    "home_goal_difference_last_5",
    "home_home_points_avg",
    "away_points_last_5",
    "away_goals_avg_last_5",
    "away_conceded_avg_last_5",
    "away_win_rate_last_5",
    "away_goal_difference_last_5",
    "away_away_points_avg",
    "points_difference_last_5",
]

REQUIRED_HISTORY_COLUMNS = [
    "home_matches_last_5",
    "away_matches_last_5",
    "home_venue_matches_last_5",
    "away_venue_matches_last_5",
]


def load_dataset():
    df = pd.read_parquet(ML_DATASET_PATH)

    df["match_date"] = pd.to_datetime(df["match_date"])

    df = df.sort_values(
        ["match_date", "home_team", "away_team"]
    ).reset_index(drop=True)

    # Historico minimo para as features gerais
    df = df[
        (df["home_matches_last_5"] == 5)
        & (df["away_matches_last_5"] == 5)
    ].copy()

    # Historico minimo no mando correspondente
    df = df[
        (df["home_venue_matches_last_5"] == 5)
        & (df["away_venue_matches_last_5"] == 5)
    ].copy()

    df = df.dropna(
        subset=FEATURE_COLUMNS + ["result"]
    )

    return df


def split_dataset(df):
    # Divisao cronologica por datas distintas:
    # 70% treino, 15% validacao, 15% teste.
    dates = sorted(df["match_date"].unique())

    train_end = int(len(dates) * 0.70)
    val_end = int(len(dates) * 0.85)

    if train_end == 0 or val_end <= train_end or val_end >= len(dates):
        raise ValueError("Datas insuficientes para divisao temporal.")

    train_cutoff = dates[train_end]
    val_cutoff = dates[val_end]

    train = df[df["match_date"] < train_cutoff]
    validation = df[
        (df["match_date"] >= train_cutoff)
        & (df["match_date"] < val_cutoff)
    ]
    test = df[df["match_date"] >= val_cutoff]

    return train, validation, test


def evaluate(model, X, y):
    predictions = model.predict(X)
    probabilities = model.predict_proba(X)

    return {
        "accuracy": accuracy_score(y, predictions),
        "f1_macro": f1_score(
            y,
            predictions,
            labels=["H", "D", "A"],
            average="macro",
            zero_division=0,
        ),
        "log_loss": log_loss(
            y,
            probabilities,
            labels=model.classes_,
        ),
    }


def main():
    print("Iniciando treinamento de Machine Learning...")

    df = load_dataset()

    print(f"Partidas disponiveis: {len(df)}")

    if df.empty:
        raise ValueError("Dataset vazio apos os filtros.")

    train, validation, test = split_dataset(df)

    print(f"Treino: {len(train)} partidas")
    print(f"Validacao: {len(validation)} partidas")
    print(f"Teste: {len(test)} partidas")

    X_train = train[FEATURE_COLUMNS]
    y_train = train["result"]

    X_val = validation[FEATURE_COLUMNS]
    y_val = validation["result"]

    X_test = test[FEATURE_COLUMNS]
    y_test = test["result"]

    models = {
        "Logistic Regression": Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(
                max_iter=1000,
                random_state=42,
            )),
        ]),

        "Random Forest": RandomForestClassifier(
            n_estimators=200,
            max_depth=6,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1,
        ),

        "HistGradientBoosting": HistGradientBoostingClassifier(
            max_iter=150,
            max_leaf_nodes=15,
            learning_rate=0.05,
            random_state=42,
        ),
    }

    results = []

    for name, model in models.items():
        print(f"\nTreinando: {name}")

        model.fit(X_train, y_train)

        metrics = evaluate(model, X_val, y_val)

        results.append({
            "model": name,
            **metrics,
        })

    results_df = pd.DataFrame(results).sort_values(
        "log_loss"
    )

    print("\n=== RESULTADOS NA VALIDACAO ===")
    print(results_df.to_string(index=False))

    best_name = results_df.iloc[0]["model"]

    print(f"\nMelhor modelo: {best_name}")

    # Retreinar o vencedor com treino + validacao
    final_train = pd.concat(
        [train, validation],
        ignore_index=True,
    )

    best_model = models[best_name]

    best_model.fit(
        final_train[FEATURE_COLUMNS],
        final_train["result"],
    )

    # Avaliacao final no conjunto de teste
    final_metrics = evaluate(
        best_model,
        X_test,
        y_test,
    )

    print("\n=== AVALIACAO FINAL NO TESTE ===")
    print(f"Modelo: {best_name}")
    print(f"Acuracia: {final_metrics['accuracy']:.4f}")
    print(f"F1 Macro: {final_metrics['f1_macro']:.4f}")
    print(f"Log Loss: {final_metrics['log_loss']:.4f}")

    # Salvar modelo e metadados
    Path(MODEL_PATH).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    artifact = {
        "model": best_model,
        "features": FEATURE_COLUMNS,
        "model_name": best_name,
        "metrics": final_metrics,
    }

    joblib.dump(artifact, MODEL_PATH)

    print(f"\nModelo salvo em: {MODEL_PATH}")


if __name__ == "__main__":
    main()
