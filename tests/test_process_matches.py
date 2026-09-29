import pytest
from pyspark.sql import SparkSession

from src.process_matches import (
    validate_required_columns,
    validate_data,
    transform_data,
)


@pytest.fixture(scope="session")
def spark():
    spark_session = (
        SparkSession.builder
        .master("local[1]")
        .appName("football-data-tests")
        .getOrCreate()
    )

    yield spark_session

    spark_session.stop()


@pytest.fixture
def valid_df(spark):
    data = [
        ("16/08/2025", "Liverpool", "Bournemouth", 4, 2, "H"),
        ("17/08/2025", "Chelsea", "Crystal Palace", 0, 0, "D"),
        ("18/08/2025", "Leeds", "Everton", 0, 1, "A"),
    ]

    columns = [
        "Date",
        "HomeTeam",
        "AwayTeam",
        "FTHG",
        "FTAG",
        "FTR",
    ]

    return spark.createDataFrame(data, columns)


def test_required_columns_valid(valid_df):
    validate_required_columns(valid_df)


def test_missing_required_column(valid_df):
    df_without_goals = valid_df.drop("FTHG")

    with pytest.raises(
        ValueError,
        match="Colunas obrigatórias ausentes"
    ):
        validate_required_columns(df_without_goals)


def test_valid_data(valid_df):
    validate_data(valid_df)


def test_invalid_date(spark):
    data = [
        ("data_invalida", "Arsenal", "Chelsea", 2, 1, "H")
    ]

    columns = [
        "Date",
        "HomeTeam",
        "AwayTeam",
        "FTHG",
        "FTAG",
        "FTR",
    ]

    df = spark.createDataFrame(data, columns)

    with pytest.raises(
        ValueError,
        match="data inválida"
    ):
        validate_data(df)


def test_null_goals(spark):
    data = [
        ("16/08/2025", "Arsenal", "Chelsea", None, 1, "A")
    ]

    schema = """
        Date string,
        HomeTeam string,
        AwayTeam string,
        FTHG integer,
        FTAG integer,
        FTR string
    """

    df = spark.createDataFrame(data, schema)

    with pytest.raises(
        ValueError,
        match="gols nulos"
    ):
        validate_data(df)


def test_invalid_result(spark):
    data = [
        ("16/08/2025", "Arsenal", "Chelsea", 2, 1, "X")
    ]

    columns = [
        "Date",
        "HomeTeam",
        "AwayTeam",
        "FTHG",
        "FTAG",
        "FTR",
    ]

    df = spark.createDataFrame(data, columns)

    with pytest.raises(
        ValueError,
        match="resultado inválido"
    ):
        validate_data(df)


def test_transformation(valid_df):
    df_processed = transform_data(valid_df)

    expected_columns = [
        "season",
        "match_date",
        "home_team",
        "away_team",
        "home_goals",
        "away_goals",
        "result",
    ]

    assert df_processed.columns == expected_columns

    assert df_processed.count() == 3