"""Profiling das fontes da parte 2 (cinco grandes ligas e Brasileirão, avaliado e descartado).

Reproduz os números de docs/parte-2/profiling-fontes.md.
Pré-requisito: python ingestion/download_warehouse_sources.py
Uso: python warehouse/profiling/profile_sources.py
"""

from pathlib import Path

import pandas as pd

TM = Path("data/raw/transfermarkt")
BRA_CSV = Path("data/raw/brasileirao/BRA.csv")
PL_CSV = Path("data/raw/premier_league/2025-26.csv")
# Cinco grandes ligas da Europa, mais o Brasileirão (avaliado e descartado).
LEAGUES = ["GB1", "ES1", "L1", "IT1", "FR1", "BRA1"]


def read_tm(table: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(TM / f"{table}.csv.gz", **kwargs)


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> None:
    games = read_tm("games")
    games = games[games.competition_id.isin(LEAGUES)].copy()
    games["date"] = pd.to_datetime(games.date)

    section("Partidas por liga e rótulo de temporada (Transfermarkt)")
    print(
        games.groupby(["competition_id", "season"])
        .agg(partidas=("game_id", "size"), primeira=("date", "min"),
             ultima=("date", "max"), rodadas=("round", "nunique"))
        .to_string()
    )

    section("Atuações (appearances) por liga e temporada")
    apps = read_tm("appearances")
    apps = apps[apps.competition_id.isin(LEAGUES)].merge(
        games[["game_id", "season"]], on="game_id", how="left"
    )
    print(
        apps.groupby(["competition_id", "season"])
        .agg(linhas=("appearance_id", "size"), jogadores=("player_id", "nunique"),
             minutos_nulos=("minutes_played", lambda s: s.isna().sum()),
             minutos_max=("minutes_played", "max"))
        .to_string()
    )
    print("Atuações do Brasileirão:", (apps.competition_id == "BRA1").sum())
    big5 = apps[apps.competition_id != "BRA1"]
    leagues_per_player = big5.groupby("player_id").competition_id.nunique()
    multi = leagues_per_player[leagues_per_player >= 2].index
    with_pl = big5[big5.player_id.isin(multi) & (big5.competition_id == "GB1")].player_id.nunique()
    print("Jogadores com atuações em 2 ou mais das cinco ligas:", len(multi),
          "| desses, com passagem pela Premier League:", with_pl)

    section("Eventos de jogo por liga e temporada")
    events = read_tm("game_events").merge(
        games[["game_id", "season", "competition_id"]], on="game_id"
    )
    print(events.groupby(["competition_id", "season", "type"]).size()
          .unstack(fill_value=0).to_string())

    section("Transferências entre as ligas")
    clubs = read_tm("clubs").set_index("club_id").domestic_competition_id
    transfers = read_tm("transfers")
    transfers["from_comp"] = transfers.from_club_id.map(clubs)
    transfers["to_comp"] = transfers.to_club_id.map(clubs)
    print("Total:", len(transfers), "| sem valor de transferência:",
          transfers.transfer_fee.isna().sum())
    bra_to_pl = transfers[(transfers.from_comp == "BRA1") & (transfers.to_comp == "GB1")]
    pl_to_bra = transfers[(transfers.from_comp == "GB1") & (transfers.to_comp == "BRA1")]
    print("Brasileirão -> Premier League:", len(bra_to_pl),
          "| Premier League -> Brasileirão:", len(pl_to_bra))
    print(bra_to_pl.transfer_season.value_counts().sort_index().to_dict())

    section("Avaliações de mercado de jogadores em clubes do Brasileirão")
    vals = read_tm("player_valuations")
    vals["date"] = pd.to_datetime(vals.date)
    bra_vals = vals[vals.player_club_domestic_competition_id == "BRA1"]
    print("Total de avaliações:", len(vals), "| no Brasileirão:", len(bra_vals))
    print(bra_vals.date.dt.year.value_counts().sort_index().to_dict())

    section("Jogadores")
    players = read_tm("players")
    print("Total:", len(players), "| cidadania brasileira:",
          (players.country_of_citizenship == "Brazil").sum(),
          "| sem data de nascimento:", players.date_of_birth.isna().sum())

    section("Football-Data.co.uk: partidas do Brasileirão por temporada")
    bra = pd.read_csv(BRA_CSV)
    print(bra.groupby("Season").size().to_dict())

    section("Nomes de clubes: Football-Data.co.uk x Transfermarkt")
    print("Brasileirão (FD):", sorted(set(bra[bra.Season >= 2025].Home)))
    print("Brasileirão (TM):",
          sorted(set(games[games.competition_id == "BRA1"].home_club_name.dropna())))
    if PL_CSV.exists():
        pl = pd.read_csv(PL_CSV)
        print("Premier League (FD):", sorted(set(pl.HomeTeam)))
    print("Premier League (TM):", sorted(set(
        games[(games.competition_id == "GB1") & (games.season == 2025)].home_club_name
    )))


if __name__ == "__main__":
    main()
