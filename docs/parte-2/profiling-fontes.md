# Parte 2 — Profiling das fontes

Levantamento feito antes da modelagem para confirmar ou derrubar as hipóteses do [escopo](../escopo-projeto.md). Os números são reproduzidos por [`warehouse/profiling/profile_sources.py`](../../warehouse/profiling/profile_sources.py).

Fontes analisadas:

- Transfermarkt datasets: arquivos de 5/9/2026, com dados até julho de 2026.
- Football-Data.co.uk: histórico do Brasileirão (`BRA.csv`) e Premier League 2025-26.

## Resumo

| Hipótese | Resultado |
|---|---|
| O Transfermarkt rotula temporadas de ano-calendário pelo ano anterior | **Confirmada.** O Brasileirão 2025 aparece como `season = 2024` |
| Os nomes de clubes diferem entre as fontes | **Confirmada** nas duas ligas |
| O histórico de clubes do jogador vem das transferências | **Confirmada.** A tabela de jogadores só traz o clube atual |
| O Transfermarkt cobre o Brasileirão como cobre a Premier League | **Derrubada.** Ver achado 1 |

**Resultado:** o Brasileirão foi substituído pelas cinco grandes ligas da Europa (ver [Decisão](#decisão)).

## Achado 1: cobertura do Brasileirão é muito menor

| | Premier League (`GB1`) | Brasileirão (`BRA1`) |
|---|---|---|
| Partidas | 14 temporadas completas (2012-13 a 2025-26), 380 por temporada | Brasileirão 2025 completo (380) e Brasileirão 2026 até a 18ª rodada (177) |
| Atuações (minutos, gols, assistências por jogador e jogo) | ~10 a 11,5 mil linhas por temporada, sem minutos nulos | **Nenhuma** |
| Eventos de jogo (gols, cartões, substituições, com jogador) | Todas as temporadas | Só as duas temporadas acima |
| Avaliações de mercado de jogadores | Todo o período | 2004 a 2026, com volume relevante a partir de 2015 |

Consequência: **não há minutos jogados por atleta no Brasileirão.** Gols e cartões existem pelos eventos, mas sem minutos não dá para calcular produção por 90 minutos.

A única forma de reconstruir os minutos com essa fonte é combinar as **escalações** (`game_lineups`, 126 MB, ainda não baixado) com as substituições dos eventos. Isso só vale para 2025 e o primeiro turno de 2026, e precisa ser verificado.

## Achado 2: rótulo de temporada

O Transfermarkt usa o ano de início da temporada. Para ligas de ano-calendário isso desloca um ano:

| Liga | `season` no Transfermarkt | Temporada real | Período |
|---|---|---|---|
| Premier League | 2025 | 2025-26 | ago/2025 a mai/2026 |
| Brasileirão | 2024 | 2025 | mar/2025 a dez/2025 |
| Brasileirão | 2025 | 2026 (parcial) | jan/2026 a jun/2026 |

A `dim_season` precisa de um rótulo de exibição por liga ("2025-26", "2025") separado do código da fonte.

## Achado 3: nomes de clubes

| Football-Data.co.uk | Transfermarkt |
|---|---|
| Man United | Manchester United |
| Nott'm Forest | Nottingham Forest |
| Wolves | Wolverhampton Wanderers |
| Flamengo RJ | Clube de Regatas do Flamengo |
| Botafogo RJ | S. A. F. Botafogo |
| Sao Paulo | São Paulo Futebol Clube |

Os nomes não batem em nenhum dos 20 clubes da Premier League nem dos 24 do Brasileirão analisados. É necessária uma **tabela de correspondência de clubes** mantida à mão e testada.

## Achado 4: transferências entre as ligas

- 175 mil transferências no total; **61 mil sem valor** (empréstimos, transferências livres ou valor não divulgado).
- **57 transferências de clubes do Brasileirão para a Premier League** e 42 no sentido contrário, concentradas a partir de 2022-23.
- Limitação: a liga do clube é a **atual**. Um clube rebaixado pode ser classificado na liga errada no momento da transferência.

## Achado 5: outros pontos de qualidade

- `minutes_played` na Premier League vai até 90: os acréscimos não são contados.
- 49 jogadores sem data de nascimento, em 50 mil.
- O Football-Data.co.uk tem o Brasileirão completo de 2012 a 2025 (380 partidas por temporada) e 359 partidas de 2026 até 20/11/2026. Só resultados e odds.
- Acentos estão corretos nos arquivos (UTF-8). Erros de exibição no terminal do Windows são só do console.

## Impacto no escopo da parte 2

| Item do escopo | Situação |
|---|---|
| Modelo dimensional com as duas ligas, `dim_season` compartilhada | **Mantido.** Partidas, resultados, odds, valor de mercado e transferências existem para as duas ligas |
| SCD tipo 2 do jogador | **Mantido** |
| Brasileiros e jogadores do Brasileirão na Premier League | **Mantido e fortalecido.** Usa transferências, valor de mercado e atuações na Premier League, todos com boa cobertura |
| "Quem está subvalorizado no Brasileirão?" | **Enfraquecido.** Sem minutos, só existe produção bruta de uma temporada e meia |
| Fator de conversão entre ligas | **Inviável como planejado.** Nenhum jogador tem atuações registradas nas duas ligas |
| Valor de mercado esperado contra o real | **Viável na Premier League**, com 14 temporadas de atuações |

## Alternativa avaliada: as cinco grandes ligas da Europa

| Liga (código Transfermarkt) | Partidas por temporada, 2012-13 a 2025-26 | Partidas com atuações |
|---|---|---|
| Premier League (`GB1`) | 380 | Todas |
| La Liga (`ES1`) | 380 | Todas |
| Serie A (`IT1`) | 380 | Todas, menos 1 em 2012-13 |
| Bundesliga (`L1`) | 306 (18 clubes) | Todas |
| Ligue 1 (`FR1`) | 380; 279 em 2019-20 (encerrada pela Covid); 306 desde 2023-24 (18 clubes) | Todas, menos 1 em 2025-26 |

- Nenhum minuto jogado nulo.
- **1.948 jogadores** têm atuações em mais de uma das cinco ligas; 1.045 deles passaram pela Premier League. Isso viabiliza o fator de conversão entre ligas.
- No Football-Data.co.uk, as cinco ligas têm as mesmas colunas de estatísticas (chutes, chutes no alvo, escanteios, faltas, cartões) e de odds.
- Na StatsBomb, a temporada 2015/16 tem eventos lance a lance para as cinco ligas.

## Decisão

**O Brasileirão foi substituído pelas cinco grandes ligas da Europa.** A falta de minutos por jogador no Brasileirão inviabilizava as principais análises por atleta, enquanto as cinco ligas têm cobertura completa e homogênea nas três fontes. O público brasileiro continua contemplado por um recorte dos brasileiros que atuam nessas ligas. O [escopo](../escopo-projeto.md) foi atualizado.
