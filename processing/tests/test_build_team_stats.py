
import pytest

from pyspark.sql.functions import sum as spark_sum

from src.build_team_stats import build_team_stats


@pytest.fixture
def matches_df(spark):
    data = [
        ("2025-26", "Arsenal", "Chelsea", 2, 1, "H"),
        ("2025-26", "Chelsea", "Liverpool", 1, 1, "D"),
        ("2025-26", "Liverpool", "Arsenal", 3, 0, "H"),
    ]

    columns = [
        "season",
        "home_team",
        "away_team",
        "home_goals",
        "away_goals",
        "result",
    ]

    return spark.createDataFrame(data, columns)


@pytest.fixture
def stats_df(matches_df):
    return build_team_stats(matches_df)


def test_total_teams(stats_df):
    assert stats_df.count() == 3


def test_matches_per_team(stats_df):
    rows = stats_df.collect()

    for row in rows:
        assert row.matches == 2
        assert row.wins + row.draws + row.losses == row.matches


def test_points_calculation(stats_df):
    teams = {
        row.team: row
        for row in stats_df.collect()
    }

    assert teams["Arsenal"].points == 3
    assert teams["Chelsea"].points == 1
    assert teams["Liverpool"].points == 4


def test_goal_difference(stats_df):
    teams = {
        row.team: row
        for row in stats_df.collect()
    }

    assert teams["Arsenal"].goal_difference == -2
    assert teams["Chelsea"].goal_difference == -1
    assert teams["Liverpool"].goal_difference == 3


def test_total_goals_balance(stats_df):
    totals = stats_df.agg(
        spark_sum("goals_for").alias("goals_for"),
        spark_sum("goals_against").alias("goals_against"),
    ).first()

    assert totals.goals_for == totals.goals_against


def test_home_away_matches(stats_df):
    teams = {
        row.team: row
        for row in stats_df.collect()
    }

    assert teams["Arsenal"].home_matches == 1
    assert teams["Arsenal"].away_matches == 1

    assert teams["Chelsea"].home_matches == 1
    assert teams["Chelsea"].away_matches == 1

    assert teams["Liverpool"].home_matches == 1
    assert teams["Liverpool"].away_matches == 1
