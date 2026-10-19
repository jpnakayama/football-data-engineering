
import pytest

from datetime import date

from src.build_match_features import (
    build_team_match_history,
    build_rolling_features,
    validate_team_match_dates,
    build_ml_dataset
)


@pytest.fixture
def matches_df(spark):
    data = [
        ("2025-26", date(2025, 8, 1), "Arsenal", "Chelsea", 2, 1, "H"),
        ("2025-26", date(2025, 8, 8), "Liverpool", "Arsenal", 3, 0, "H"),
        ("2025-26", date(2025, 8, 15), "Arsenal", "Everton", 1, 1, "D"),
    ]

    columns = [
        "season",
        "match_date",
        "home_team",
        "away_team",
        "home_goals",
        "away_goals",
        "result",
    ]

    return spark.createDataFrame(data, columns)


@pytest.fixture
def ml_dataset(matches_df, features_df):
    return build_ml_dataset(matches_df, features_df)


def test_ml_dataset_preserves_matches(matches_df, ml_dataset):
    assert ml_dataset.count() == matches_df.count()


def test_ml_dataset_has_unique_matches(ml_dataset):
    keys = [
        "season",
        "match_date",
        "home_team",
        "away_team",
    ]

    assert ml_dataset.select(*keys).distinct().count() == ml_dataset.count()


def test_ml_dataset_preserves_target(ml_dataset):
    arsenal_chelsea = (
        ml_dataset
        .filter(
            (ml_dataset.home_team == "Arsenal")
            & (ml_dataset.away_team == "Chelsea")
        )
        .first()
    )

    assert arsenal_chelsea.result == "H"


def test_ml_dataset_uses_previous_matches_only(ml_dataset):
    arsenal_everton = (
        ml_dataset
        .filter(
            (ml_dataset.home_team == "Arsenal")
            & (ml_dataset.away_team == "Everton")
        )
        .first()
    )

    assert arsenal_everton.home_matches_last_5 == 2
    assert arsenal_everton.home_points_last_5 == 3
    assert arsenal_everton.home_goals_avg_last_5 == 1.0
    assert arsenal_everton.home_conceded_avg_last_5 == 2.0


@pytest.fixture
def features_df(matches_df):
    history = build_team_match_history(matches_df)
    return build_rolling_features(history)


def test_two_records_per_match(matches_df):
    history = build_team_match_history(matches_df)

    assert history.count() == matches_df.count() * 2


def test_first_match_has_no_history(features_df):
    first_match = (
        features_df
        .filter("team = 'Arsenal'")
        .orderBy("match_date")
        .first()
    )

    assert first_match.matches_last_5 == 0
    assert first_match.points_last_5 is None
    assert first_match.goals_for_avg_last_5 is None


def test_rolling_points_excludes_current_match(features_df):
    arsenal = (
        features_df
        .filter("team = 'Arsenal'")
        .orderBy("match_date")
        .collect()
    )

    assert arsenal[0].points_last_5 is None
    assert arsenal[1].points_last_5 == 3
    assert arsenal[2].points_last_5 == 3


def test_rolling_goals(features_df):
    arsenal = (
        features_df
        .filter("team = 'Arsenal'")
        .orderBy("match_date")
        .collect()
    )

    assert arsenal[1].goals_for_avg_last_5 == 2.0
    assert arsenal[2].goals_for_avg_last_5 == 1.0

    assert arsenal[2].goals_against_avg_last_5 == 2.0


def test_home_away_perspective(matches_df):
    history = build_team_match_history(matches_df)

    chelsea = history.filter("team = 'Chelsea'").first()

    assert chelsea.venue == "away"
    assert chelsea.goals_for == 1
    assert chelsea.goals_against == 2
    assert chelsea.points == 0


def test_valid_team_match_dates(matches_df):
    history = build_team_match_history(matches_df)

    validate_team_match_dates(history)


def test_duplicate_team_match_date(spark):
    data = [
        ("2025-26", date(2025, 8, 1), "Arsenal", "Chelsea", 2, 1, "H"),
        ("2025-26", date(2025, 8, 1), "Arsenal", "Everton", 1, 0, "H"),
    ]

    columns = [
        "season",
        "match_date",
        "home_team",
        "away_team",
        "home_goals",
        "away_goals",
        "result",
    ]

    matches = spark.createDataFrame(data, columns)
    history = build_team_match_history(matches)

    with pytest.raises(
        ValueError,
        match="ordenacao temporal e ambigua"
    ):
        validate_team_match_dates(history)
