
import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    lit,
    sum as spark_sum,
    round as spark_round,
    when,
)


PROCESSED_PATH = os.getenv(
    "PROCESSED_PATH",
    "/data/processed/premier_league"
)

ANALYTICS_PATH = os.getenv(
    "ANALYTICS_PATH",
    "/data/analytics/team_season_stats"
)


def build_team_stats(df):
    """Calcula estatisticas por equipe e temporada."""

    # Uma linha por mandante em cada partida
    home = df.select(
        "season",
        col("home_team").alias("team"),
        lit("home").alias("venue"),
        col("home_goals").alias("goals_for"),
        col("away_goals").alias("goals_against"),
        when(col("result") == "H", 1).otherwise(0).alias("win"),
        when(col("result") == "D", 1).otherwise(0).alias("draw"),
        when(col("result") == "A", 1).otherwise(0).alias("loss"),
    )

    # Uma linha por visitante em cada partida
    away = df.select(
        "season",
        col("away_team").alias("team"),
        lit("away").alias("venue"),
        col("away_goals").alias("goals_for"),
        col("home_goals").alias("goals_against"),
        when(col("result") == "A", 1).otherwise(0).alias("win"),
        when(col("result") == "D", 1).otherwise(0).alias("draw"),
        when(col("result") == "H", 1).otherwise(0).alias("loss"),
    )

    # Cada partida gera dois registros:
    # um para o mandante e outro para o visitante
    team_matches = home.unionByName(away)

    # Consolidar por equipe e temporada
    stats = (
        team_matches
        .groupBy("season", "team")
        .agg(
            spark_sum("win").alias("wins"),
            spark_sum("draw").alias("draws"),
            spark_sum("loss").alias("losses"),
            spark_sum("goals_for").alias("goals_for"),
            spark_sum("goals_against").alias("goals_against"),

            spark_sum(
                when(col("venue") == "home", 1).otherwise(0)
            ).alias("home_matches"),

            spark_sum(
                when(col("venue") == "away", 1).otherwise(0)
            ).alias("away_matches"),

            spark_sum(
                when(col("venue") == "home", col("win"))
                .otherwise(0)
            ).alias("home_wins"),

            spark_sum(
                when(col("venue") == "away", col("win"))
                .otherwise(0)
            ).alias("away_wins"),
        )
        .withColumn(
            "matches",
            col("wins") + col("draws") + col("losses")
        )
        .withColumn(
            "goal_difference",
            col("goals_for") - col("goals_against")
        )
        .withColumn(
            "points",
            col("wins") * 3 + col("draws")
        )
        .withColumn(
            "points_percentage",
            spark_round(
                col("points") / (col("matches") * 3) * 100,
                2
            )
        )
    )

    return stats.select(
        "season",
        "team",
        "matches",
        "wins",
        "draws",
        "losses",
        "goals_for",
        "goals_against",
        "goal_difference",
        "points",
        "points_percentage",
        "home_matches",
        "away_matches",
        "home_wins",
        "away_wins",
    )


def main():
    spark = (
        SparkSession.builder
        .appName("football-team-statistics")
        .master("local[*]")
        .getOrCreate()
    )

    try:
        print("Lendo dados processados...")

        df = spark.read.parquet(PROCESSED_PATH)

        print("Calculando estatisticas por equipe...")

        stats = build_team_stats(df)

        print("\n=== TOTAL DE REGISTROS ===")
        print(stats.count())

        print("\n=== AMOSTRA ===")
        (
            stats.orderBy(
                "season",
                col("points").desc(),
                col("goal_difference").desc(),
            )
            .show(20, truncate=False)
        )

        print("\nGravando camada Analytics...")

        (
            stats.write
            .mode("overwrite")
            .partitionBy("season")
            .parquet(ANALYTICS_PATH)
        )

        print(f"Dados gravados em: {ANALYTICS_PATH}")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
