from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    input_file_name,
    regexp_extract,
    to_date,
    try_to_timestamp,
    lit,
)


RAW_PATH = "/data/raw/premier_league/*.csv"
PROCESSED_PATH = "/data/processed/premier_league"

REQUIRED_COLUMNS = {
    "Date",
    "HomeTeam",
    "AwayTeam",
    "FTHG",
    "FTAG",
    "FTR",
}

VALID_RESULTS = ["H", "D", "A"]


def create_spark_session():
    return (
        SparkSession.builder
        .appName("football-data-processing")
        .master("local[*]")
        .getOrCreate()
    )


def validate_required_columns(df):
    """Verifica se todas as colunas necessárias existem."""

    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Colunas obrigatórias ausentes: {sorted(missing_columns)}"
        )


def validate_data(df):
    """Valida a qualidade dos dados antes do processamento."""

    # Data convertida apenas para validação
    validation_df = df.withColumn(
        "_parsed_date",
        try_to_timestamp(
            col("Date"),
            lit("dd/MM/yyyy")
        ).cast("date")
    )

    invalid_dates = validation_df.filter(
        col("_parsed_date").isNull()
    ).count()

    null_goals = validation_df.filter(
        col("FTHG").isNull() |
        col("FTAG").isNull()
    ).count()

    invalid_results = validation_df.filter(
        col("FTR").isNull() |
        (~col("FTR").isin(VALID_RESULTS))
    ).count()

    errors = []

    if invalid_dates > 0:
        errors.append(
            f"{invalid_dates} registro(s) com data inválida"
        )

    if null_goals > 0:
        errors.append(
            f"{null_goals} registro(s) com gols nulos"
        )

    if invalid_results > 0:
        errors.append(
            f"{invalid_results} registro(s) com resultado inválido"
        )

    if errors:
        raise ValueError(
            "Falha na validação dos dados:\n- "
            + "\n- ".join(errors)
        )


def transform_data(df):
    """Transforma os dados Raw para o formato Processed."""

    df = df.withColumn(
        "source_file",
        input_file_name()
    )

    df = df.withColumn(
        "season",
        regexp_extract(
            col("source_file"),
            r"(\d{4}-\d{2})\.csv",
            1
        )
    )

    return df.select(
        "season",
        to_date(col("Date"), "dd/MM/yyyy").alias("match_date"),
        col("HomeTeam").alias("home_team"),
        col("AwayTeam").alias("away_team"),
        col("FTHG").cast("integer").alias("home_goals"),
        col("FTAG").cast("integer").alias("away_goals"),
        col("FTR").alias("result"),
    )


def main():
    spark = create_spark_session()

    try:
        print("Iniciando processamento da Premier League...")

        df_raw = (
            spark.read
            .option("header", True)
            .option("inferSchema", True)
            .csv(RAW_PATH)
        )

        print(f"Quantidade de registros raw: {df_raw.count()}")

        # 1. Validação estrutural
        validate_required_columns(df_raw)

        # 2. Validação dos dados
        validate_data(df_raw)

        print("Validação concluída com sucesso.")

        # 3. Transformação
        df_processed = transform_data(df_raw)

        print("Schema processado:")
        df_processed.printSchema()

        print("Amostra dos dados:")
        df_processed.show(10, truncate=False)

        # 4. Escrita
        (
            df_processed.write
            .mode("overwrite")
            .partitionBy("season")
            .parquet(PROCESSED_PATH)
        )

        print(
            f"Dados processados gravados em {PROCESSED_PATH}"
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()