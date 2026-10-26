
import pandas as pd
import streamlit as st

from data_loader import (
    load_team_stats,
    load_team_history,
    load_model,
)
from prediction import predict_match


# Configuração da aplicação
st.set_page_config(
    page_title="Premier League Analytics",
    page_icon="⚽",
    layout="wide",
)


# Carregamento dos dados e do modelo
@st.cache_data
def get_team_stats():
    return load_team_stats()


@st.cache_data
def get_team_history():
    return load_team_history()


@st.cache_resource
def get_model():
    return load_model()


# Cabeçalho
st.title("⚽ Premier League Analytics")
st.caption(
    "Análise histórica e previsão de resultados | "
    "Football Data Engineering"
)


# Navegação
tab_dashboard, tab_prediction = st.tabs([
    "📊 Dashboard histórico",
    "⚽ Previsão de partidas",
])


# ============================================================
# ABA 1 — DASHBOARD HISTÓRICO
# ============================================================

with tab_dashboard:

    df = get_team_stats()

    st.header("Dashboard histórico")

    # Filtros
    col_season, col_teams = st.columns([1, 3])

    with col_season:
        seasons = sorted(
            df["season"].unique(),
            reverse=True,
        )

        selected_season = st.selectbox(
            "Temporada",
            seasons,
        )

    season_df = df[
        df["season"] == selected_season
    ].copy()

    with col_teams:
        teams = sorted(
            season_df["team"].unique()
        )

        selected_teams = st.multiselect(
            "Equipes",
            teams,
            default=teams,
        )

    filtered_df = season_df[
        season_df["team"].isin(selected_teams)
    ].copy()

    st.subheader(f"Temporada {selected_season}")

    if filtered_df.empty:
        st.warning("Selecione pelo menos uma equipe.")

    else:
        # Indicadores gerais da temporada
        total_matches = (
            season_df["matches"].sum() // 2
        )

        total_goals = season_df["goals_for"].sum()

        avg_goals = (
            total_goals / total_matches
            if total_matches > 0
            else 0
        )

        total_teams = len(season_df)

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Partidas", total_matches)
        col2.metric("Gols", total_goals)
        col3.metric(
            "Média de gols",
            f"{avg_goals:.2f}",
        )
        col4.metric("Equipes", total_teams)

        st.divider()

        # Classificação
        st.subheader("Classificação por pontos")

        standings = filtered_df.sort_values(
            [
                "points",
                "goal_difference",
                "goals_for",
            ],
            ascending=[False, False, False],
        ).copy()

        standings = standings[
            [
                "team",
                "matches",
                "wins",
                "draws",
                "losses",
                "goals_for",
                "goals_against",
                "goal_difference",
                "points",
            ]
        ]

        standings.columns = [
            "Equipe",
            "Jogos",
            "Vitórias",
            "Empates",
            "Derrotas",
            "Gols pró",
            "Gols contra",
            "Saldo",
            "Pontos",
        ]

        st.dataframe(
            standings,
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        # Gráficos comparativos
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("Pontos por equipe")

            chart_df = filtered_df.sort_values(
                "points",
                ascending=False,
            )

            st.bar_chart(
                chart_df.set_index("team")["points"],
                x_label="Equipe",
                y_label="Pontos",
            )

        with col_right:
            st.subheader("Saldo de gols")

            chart_df = filtered_df.sort_values(
                "goal_difference",
                ascending=False,
            )

            st.bar_chart(
                chart_df.set_index("team")[
                    "goal_difference"
                ],
                x_label="Equipe",
                y_label="Saldo de gols",
            )

        st.divider()

        st.subheader("Desempenho das equipes")

        performance = filtered_df[
            ["team", "wins", "draws", "losses"]
        ].set_index("team")

        performance.columns = [
            "Vitórias",
            "Empates",
            "Derrotas",
        ]

        st.bar_chart(
            performance,
            x_label="Equipe",
            y_label="Partidas",
        )

        st.caption(
            "Fonte: dados históricos da Premier League "
            "processados com PySpark."
        )


# ============================================================
# ABA 2 — PREVISÃO DE PARTIDAS
# ============================================================

with tab_prediction:

    st.header("Previsão de partidas")

    st.write(
        "Selecione duas equipes para estimar as "
        "probabilidades de vitória do mandante, "
        "empate ou vitória do visitante."
    )

    history = get_team_history()
    artifact = get_model()

    teams = sorted(
        history["team"].unique()
    )

    col_home, col_away = st.columns(2)

    with col_home:
        home_team = st.selectbox(
            "Mandante",
            teams,
            index=0,
        )

    with col_away:
        away_team = st.selectbox(
            "Visitante",
            teams,
            index=1,
        )

    if st.button(
        "Calcular probabilidades",
        type="primary",
    ):

        try:
            prediction = predict_match(
                history,
                artifact,
                home_team,
                away_team,
            )

            st.subheader(
                f"{home_team} × {away_team}"
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                f"Vitória — {home_team}",
                f"{prediction['home_win']:.1%}",
            )

            col2.metric(
                "Empate",
                f"{prediction['draw']:.1%}",
            )

            col3.metric(
                f"Vitória — {away_team}",
                f"{prediction['away_win']:.1%}",
            )

            st.divider()

            # Visualização das probabilidades
            chart_df = pd.DataFrame({
                "Resultado": [
                    f"Vitória — {home_team}",
                    "Empate",
                    f"Vitória — {away_team}",
                ],
                "Probabilidade (%)": [
                    prediction["home_win"] * 100,
                    prediction["draw"] * 100,
                    prediction["away_win"] * 100,
                ],
            })

            st.subheader(
                "Distribuição das probabilidades"
            )

            st.bar_chart(
                chart_df.set_index("Resultado"),
                y_label="Probabilidade (%)",
            )

            st.caption(
                f"Modelo: {artifact['model_name']}. "
                "Estimativas calculadas com base "
                "no histórico disponível das equipes. "
                "As probabilidades não representam "
                "garantia de resultado."
            )

        except ValueError as error:
            st.warning(str(error))


# Rodapé
st.divider()

st.caption(
    "Football Data Engineering | "
    "AWS • Terraform • Docker • PySpark • "
    "Scikit-learn • Streamlit"
)
