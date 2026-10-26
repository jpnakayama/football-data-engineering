
import pandas as pd


def get_team_features(history, team, venue):
    """Calcula estatísticas anteriores para uma equipe."""

    team_history = (
        history[history["team"] == team]
        .sort_values("match_date")
    )

    venue_history = team_history[
        team_history["venue"] == venue
    ]

    if len(team_history) < 5 or len(venue_history) < 5:
        raise ValueError(
            f"Histórico insuficiente para {team}."
        )

    last_5 = team_history.tail(5)
    last_5_venue = venue_history.tail(5)

    points = last_5["points"].sum()
    goals_for = last_5["goals_for"].mean()
    goals_against = last_5["goals_against"].mean()

    return {
        "points_last_5": points,
        "goals_avg_last_5": goals_for,
        "conceded_avg_last_5": goals_against,
        "win_rate_last_5": (
            last_5["points"].eq(3).mean()
        ),
        "goal_difference_last_5": (
            last_5["goals_for"]
            - last_5["goals_against"]
        ).sum(),
        "venue_points_avg": (
            last_5_venue["points"].mean()
        ),
    }


def predict_match(history, artifact, home_team, away_team):
    """Retorna probabilidades de resultado da partida."""

    if home_team == away_team:
        raise ValueError(
            "Selecione duas equipes diferentes."
        )

    home = get_team_features(
        history, home_team, "home"
    )

    away = get_team_features(
        history, away_team, "away"
    )

    features = {
        "home_points_last_5": home["points_last_5"],
        "home_goals_avg_last_5": home["goals_avg_last_5"],
        "home_conceded_avg_last_5": home["conceded_avg_last_5"],
        "home_win_rate_last_5": home["win_rate_last_5"],
        "home_goal_difference_last_5": (
            home["goal_difference_last_5"]
        ),
        "home_home_points_avg": (
            home["venue_points_avg"]
        ),
        "away_points_last_5": away["points_last_5"],
        "away_goals_avg_last_5": away["goals_avg_last_5"],
        "away_conceded_avg_last_5": away["conceded_avg_last_5"],
        "away_win_rate_last_5": away["win_rate_last_5"],
        "away_goal_difference_last_5": (
            away["goal_difference_last_5"]
        ),
        "away_away_points_avg": (
            away["venue_points_avg"]
        ),
        "points_difference_last_5": (
            home["points_last_5"]
            - away["points_last_5"]
        ),
    }

    model = artifact["model"]

    input_df = pd.DataFrame(
        [features],
        columns=artifact["features"],
    )

    probabilities = model.predict_proba(input_df)[0]

    result = dict(
        zip(model.classes_, probabilities)
    )

    return {
        "home_win": float(result["H"]),
        "draw": float(result["D"]),
        "away_win": float(result["A"]),
    }
