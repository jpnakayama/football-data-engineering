
import os

from pyspark.sql import SparkSession, Window
from pyspark.sql.functions import (
    avg,
    col,
    count,
    lit,
    sum as spark_sum,
    when,
)


ML_DATASET_PATH = os.getenv(
    "ML_DATASET_PATH",
    "/data/features/match_features",
)

PROCESSED_PATH = os.getenv(
    "PROCESSED_PATH",
    "/data/processed/premier_league",
)

FEATURES_PATH = os.getenv(
    "FEATURES_PATH",
    "/data/features/team_match_history",
)


def build_team_match_history(df):
    home = df.select(
        "season",
        "match_date",
        col("home_team").alias("team"),
        col("away_team").alias("opponent"),
        lit("home").alias("venue"),
        col("home_goals").alias("goals_for"),
        col("away_goals").alias("goals_against"),
        when(col("result") == "H", 3)
        .when(col("result") == "D", 1)
        .otherwise(0)
        .alias("points"),
        when(col("result") == "H", 1)
        .otherwise(0)
        .alias("win"),
    )

    away = df.select(
        "season",
        "match_date",
        col("away_team").alias("team"),
        col("home_team").alias("opponent"),
        lit("away").alias("venue"),
        col("away_goals").alias("goals_for"),
        col("home_goals").alias("goals_against"),
        when(col("result") == "A", 3)
        .when(col("result") == "D", 1)
        .otherwise(0)
        .alias("points"),
        when(col("result") == "A", 1)
        .otherwise(0)
        .alias("win"),
    )

    return home.unionByName(away)


def validate_team_match_dates(history):
    duplicates = (
        history
        .groupBy("team", "match_date")
        .agg(count("*").alias("total"))
        .filter(col("total") > 1)
    )

    if duplicates.limit(1).count() > 0:
        raise ValueError(
            "Foram encontradas partidas da mesma equipe "
            "na mesma data. A ordenacao temporal e ambigua."
        )


def build_rolling_features(history):
    # Ultimas 5 partidas, independentemente do mando
    window_last_5 = (
        Window
        .partitionBy("team")
        .orderBy("match_date")
        .rowsBetween(-5, -1)
    )

    # Ultimas 5 partidas no mesmo mando
    window_venue = (
        Window
        .partitionBy("team", "venue")
        .orderBy("match_date")
        .rowsBetween(-5, -1)
    )

    features = (
        history

        # Quantidade de partidas anteriores
        .withColumn(
            "matches_last_5",
            count("points").over(window_last_5),
        )

        # Pontos recentes
        .withColumn(
            "points_last_5",
            spark_sum("points").over(window_last_5),
        )

        # Media de gols marcados
        .withColumn(
            "goals_for_avg_last_5",
            avg("goals_for").over(window_last_5),
        )

        # Media de gols sofridos
        .withColumn(
            "goals_against_avg_last_5",
            avg("goals_against").over(window_last_5),
        )

        # Percentual de vitorias
        .withColumn(
            "win_rate_last_5",
            avg("win").over(window_last_5),
        )

        # Saldo de gols nas ultimas 5 partidas
        .withColumn(
            "goal_difference_last_5",
            spark_sum(
                col("goals_for") - col("goals_against")
            ).over(window_last_5),
        )

        # Quantidade de partidas no mesmo mando
        .withColumn(
            "venue_matches_last_5",
            count("points").over(window_venue),
        )

        # Media de pontos no mesmo mando
        .withColumn(
            "venue_points_avg_last_5",
            avg("points").over(window_venue),
        )
    )

    return features


def build_ml_dataset(matches, features):
    home = (
        features
        .filter(col("venue") == "home")
        .select(
            "season",
            "match_date",
            col("team").alias("home_team"),
            col("opponent").alias("away_team"),
            col("matches_last_5").alias(
                "home_matches_last_5"
            ),
            col("points_last_5").alias(
                "home_points_last_5"
            ),
            col("goals_for_avg_last_5").alias(
                "home_goals_avg_last_5"
            ),
            col("goals_against_avg_last_5").alias(
                "home_conceded_avg_last_5"
            ),
            col("win_rate_last_5").alias(
                "home_win_rate_last_5"
            ),
            col("goal_difference_last_5").alias(
                "home_goal_difference_last_5"
            ),
            col("venue_matches_last_5").alias(
                "home_venue_matches_last_5"
            ),
            col("venue_points_avg_last_5").alias(
                "home_home_points_avg"
            ),
        )
    )

    away = (
        features
        .filter(col("venue") == "away")
        .select(
            "season",
            "match_date",
            col("team").alias("away_team"),
            col("opponent").alias("home_team"),
            col("matches_last_5").alias(
                "away_matches_last_5"
            ),
            col("points_last_5").alias(
                "away_points_last_5"
            ),
            col("goals_for_avg_last_5").alias(
                "away_goals_avg_last_5"
            ),
            col("goals_against_avg_last_5").alias(
                "away_conceded_avg_last_5"
            ),
            col("win_rate_last_5").alias(
                "away_win_rate_last_5"
            ),
            col("goal_difference_last_5").alias(
                "away_goal_difference_last_5"
            ),
            col("venue_matches_last_5").alias(
                "away_venue_matches_last_5"
            ),
            col("venue_points_avg_last_5").alias(
                "away_away_points_avg"
            ),
        )
    )

    keys = [
        "season",
        "match_date",
        "home_team",
        "away_team",
    ]

    dataset = (
        matches
        .select(*keys, "result")
        .join(home, on=keys, how="inner")
        .join(away, on=keys, how="inner")
        .withColumn(
            "points_difference_last_5",
            col("home_points_last_5")
            - col("away_points_last_5"),
        )
    )

    return dataset


def main():
    spark = (
        SparkSession.builder
        .appName("football-match-features")
        .master("local[*]")
        .getOrCreate()
    )

    try:
        print("Iniciando Feature Engineering...")

        # 1. Leitura dos dados processados
        matches = spark.read.parquet(PROCESSED_PATH)

        original_count = matches.count()
        print(f"Partidas carregadas: {original_count}")

        # 2. Historico por equipe
        history = build_team_match_history(matches)

        print("Validando integridade temporal...")
        validate_team_match_dates(history)

        # 3. Calculo das features historicas
        features = build_rolling_features(history)

        # 4. Dataset final de Machine Learning
        ml_dataset = build_ml_dataset(matches, features)

        ml_count = ml_dataset.count()

        if original_count != ml_count:
            raise ValueError(
                "Quantidade de registros do dataset ML "
                "diferente da quantidade de partidas originais."
            )

        print(f"Registros no dataset ML: {ml_count}")

        # 5. Gravacao do historico
        (
            history.write
            .mode("overwrite")
            .partitionBy("season")
            .parquet(FEATURES_PATH)
        )

        # 6. Gravacao do dataset ML
        (
            ml_dataset.write
            .mode("overwrite")
            .partitionBy("season")
            .parquet(ML_DATASET_PATH)
        )

        print("Feature Engineering concluido com sucesso.")
        print(f"Historico: {FEATURES_PATH}")
        print(f"Dataset ML: {ML_DATASET_PATH}")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
