
import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    count,
    countDistinct,
    min,
    max,
    sum as spark_sum,
    when,
)


PROCESSED_PATH = os.getenv(
    "PROCESSED_PATH",
    "/data/processed/premier_league"
)


def main():
    spark = (
        SparkSession.builder
        .appName("football-data-profiling")
        .master("local[*]")
        .getOrCreate()
    )

    try:
        df = spark.read.parquet(PROCESSED_PATH)

        print("\n=== SCHEMA ===")
        df.printSchema()

        print("\n=== TOTAL DE PARTIDAS ===")
        print(df.count())

        print("\n=== PARTIDAS POR TEMPORADA ===")
        (
            df.groupBy("season")
            .agg(
                count("*").alias("matches"),
                countDistinct("home_team").alias("home_teams"),
                countDistinct("away_team").alias("away_teams"),
                min("match_date").alias("first_match"),
                max("match_date").alias("last_match"),
            )
            .orderBy("season")
            .show(truncate=False)
        )

        print("\n=== PARTIDAS DUPLICADAS ===")
        duplicates = (
            df.groupBy(
                "season",
                "match_date",
                "home_team",
                "away_team",
            )
            .count()
            .filter(col("count") > 1)
        )

        print("Grupos duplicados:", duplicates.count())

        print("\n=== DISTRIBUICAO DOS RESULTADOS ===")
        (
            df.groupBy("season", "result")
            .count()
            .orderBy("season", "result")
            .show(50, truncate=False)
        )

        # 1. Verificar valores nulos
        print("\n=== VALORES NULOS ===")

        null_counts = [
            spark_sum(
                when(col(c).isNull(), 1).otherwise(0)
            ).alias(c)
            for c in df.columns
        ]

        df.select(null_counts).show(truncate=False)

        # 2. Verificar gols negativos
        print("\n=== GOLS NEGATIVOS ===")

        negative_goals = df.filter(
            (col("home_goals") < 0) |
            (col("away_goals") < 0)
        )

        print("Partidas com gols negativos:", negative_goals.count())

        # 3. Conferir resultado e placar
        print("\n=== RESULTADOS INCONSISTENTES ===")

        inconsistent_results = df.filter(
            (
                (col("home_goals") > col("away_goals")) &
                (col("result") != "H")
            ) |
            (
                (col("home_goals") == col("away_goals")) &
                (col("result") != "D")
            ) |
            (
                (col("home_goals") < col("away_goals")) &
                (col("result") != "A")
            )
        )

        print(
            "Partidas com resultado inconsistente:",
            inconsistent_results.count()
        )

        # 4. Verificar quantidade de jogos por equipe
        print("\n=== JOGOS POR EQUIPE E TEMPORADA ===")

        home_matches = (
            df.groupBy(
                "season",
                col("home_team").alias("team")
            )
            .agg(count("*").alias("home_matches"))
        )

        away_matches = (
            df.groupBy(
                "season",
                col("away_team").alias("team")
            )
            .agg(count("*").alias("away_matches"))
        )

        team_matches = (
            home_matches.join(
                away_matches,
                ["season", "team"],
                "full"
            )
            .fillna(0, subset=["home_matches", "away_matches"])
            .withColumn(
                "total_matches",
                col("home_matches") + col("away_matches")
            )
        )

        invalid_team_matches = team_matches.filter(
            (col("home_matches") != 19) |
            (col("away_matches") != 19) |
            (col("total_matches") != 38)
        )

        print(
            "Equipes com quantidade incorreta de jogos:",
            invalid_team_matches.count()
        )

        invalid_team_matches.show(100, truncate=False)

        # 5. Verificar equipes distintas
        print("\n=== EQUIPES POR TEMPORADA ===")

        (
            team_matches.groupBy("season")
            .agg(countDistinct("team").alias("teams"))
            .orderBy("season")
            .show(truncate=False)
        )

        # 6. Verificar partidas com o mesmo time
        print("\n=== MANDANTE IGUAL AO VISITANTE ===")

        same_team = df.filter(
            col("home_team") == col("away_team")
        )

        print("Partidas inválidas:", same_team.count())

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
