# Football Intelligence Platform — Escopo do projeto

Documento de escopo das próximas etapas do projeto da pós-graduação em Engenharia de Dados. A parte 1 (Infraestrutura como Código) está concluída e descrita no [README](../README.md). Este documento define as partes 2 a 5.

> Projeto pessoal. Usa apenas contas pessoais (AWS, GitHub, Kaggle) e dados públicos.

## Visão

Uma única plataforma de dados de futebol que cresce a cada módulo do curso. Cada parte responde a **uma pergunta de um departamento de scouting**: *quem contratar, por quanto e como ele vai render?* Cada pergunta respondida vira uma entrega apresentável, por exemplo um post no LinkedIn com o problema, a arquitetura e o resultado.

| Decisão | Escolha |
|---|---|
| Ligas | Premier League e Brasileirão Série A |
| Público | Clubes e scouting (foco no **jogador**, não só na partida) |
| Corte dos dados | Temporadas encerradas: Premier League até 2025-26, Brasileirão até 2025 |
| Tempo real | Apenas **replay** de dados históricos (sem dados ao vivo) |
| Custo | Mínimo: execução local em Docker; na AWS, apenas serviços de custo próximo de zero |
| Produto final | O app Streamlit da parte 1 evolui para uma ferramenta de scouting |

## Fontes de dados

| Fonte | Cobertura | Uso | Observações |
|---|---|---|---|
| [Football-Data.co.uk](https://www.football-data.co.uk/) | PL: resultados, odds e estatísticas de jogo. Brasileirão: apenas resultados e odds de fechamento (2012 em diante) | Partidas e resultados | Já usado na parte 1. O arquivo do Brasil continua sendo atualizado |
| [Transfermarkt datasets](https://github.com/dcaribou/transfermarkt-datasets) (Kaggle) | Inclui Premier League (`GB1`) e Brasileirão (`BRA1`). Tabelas: players, clubs, games, appearances, game_events, game_lineups, transfers, player_valuations, competitions | Base principal de jogadores, valor de mercado e transferências | Licença CC0. **Atualizações pausadas em 6/7/2026**: cobre as temporadas encerradas, mas não serve como fonte contínua |
| [StatsBomb Open Data](https://github.com/statsbomb/open-data) | Eventos lance a lance. Premier League apenas 2003/04 e 2015/16. **Nenhuma competição brasileira** | Perfis de estilo de jogo (parte 4) e replay (parte 5) | Exige citar a StatsBomb como fonte e usar o logo nas publicações. Confirmar os termos do LICENSE antes de publicar |
| API de futebol com plano gratuito (candidata: football-data.org) | A confirmar | Demonstração opcional de ingestão de API na parte 3 | Verificar cobertura e limites do plano gratuito |

**Limitação conhecida:** o nível de detalhe é diferente entre as ligas. A Premier League tem estatísticas de jogo e eventos lance a lance; o Brasileirão tem resultados, odds e eventos básicos (gols, cartões, substituições) do Transfermarkt. O projeto deixa explícito o que pode e o que não pode ser afirmado com cada fonte.

## Partes do projeto

### Parte 1 — Infraestrutura como Código (concluída)

*"Dá para prever o resultado de uma partida?"*

Terraform, AWS (S3, EC2, IAM, SSM), PySpark em Docker, features pré-partida, modelo de classificação e Streamlit. Detalhes no [README](../README.md).

### Parte 2 — Data Warehouse: modelagem, implementação e governança

*"Quem está subvalorizado no Brasileirão?"*

- **Modelo dimensional centrado no jogador**:
  - Fatos: atuações (minutos, gols, assistências, cartões por jogo), valor de mercado ao longo do tempo, transferências, partidas.
  - Dimensões: jogador (SCD tipo 2 para clube e posição), clube, competição, temporada, data.
- **Desafio de modelagem:** a Premier League joga de agosto a maio ("2024-25") e o Brasileirão no ano-calendário ("2024"). Uma dimensão de temporada compartilhada permite comparar as duas ligas.
- **Métricas de scouting:** participação em gols a cada 90 minutos, minutos jogados por idade, valor de mercado por produção.
- **Análise principal:** brasileiros que foram para a Premier League jogaram de fato? Minutos antes e depois da transferência, valor pago e retorno em campo.
- **Governança:** dicionário de dados, perfis de acesso, segurança por linha, mascaramento e discussão de LGPD e GDPR (os dados são de pessoas, ainda que públicos), regras de qualidade.

**Ferramentas:** PostgreSQL em Docker (o DW), SQL.

### Parte 3 — ELT com Airbyte, dbt e SQL

*"Como ter uma shortlist atualizada a cada rodada?"*

- **Carga histórica completa**, seguida de **replay rodada a rodada**: uma fonte simulada libera os dados de cada rodada em ordem cronológica e o Airbyte sincroniza de forma incremental.
- **dbt** reconstrói o DW da parte 2 em camadas (staging, intermediate, marts), com testes, documentação e snapshots (SCD tipo 2).
- **Tabelas de consumo:** forma recente do jogador (últimos 5 jogos) e shortlist por posição, idade e faixa de valor.
- **Problema real de scouting:** casar o mesmo jogador em fontes diferentes (grafias e IDs distintos). Tabela de correspondência e testes no dbt.
- **Opcional:** ingestão do Brasileirão 2026, ainda em andamento, pelo CSV do Football-Data.co.uk ou por uma API gratuita.

**Ferramentas:** Airbyte (local, Docker), dbt Core com adaptador Postgres.

### Parte 4 — Data Lake e Data Lakehouse

*"Qual é o estilo de jogo desse atleta?"*

- **Camadas bronze, silver e gold** no S3 em tabelas Apache Iceberg (time travel, evolução de schema, MERGE).
- **Eventos lance a lance** da StatsBomb para a Premier League 2015/16 (temporada do Leicester campeão): passes progressivos, desarmes, pressões, conduções por jogador.
- **Busca por similaridade:** "quem joga parecido com o Kanté de 2015/16?"
- **Brasileirão:** eventos básicos do Transfermarkt, com a diferença de detalhe documentada.
- **Governança do lake:** catálogo e permissões por camada.

**Ferramentas:** S3, Apache Iceberg, AWS Glue Data Catalog, Amazon Athena, AWS Lake Formation, PySpark em Docker (local).

### Parte 5 — PySpark e Apache Kafka: batch e streaming

*"O scout assistindo ao jogo em tempo real"*

- **Replay** de uma partida da Premier League: um produtor publica os eventos da StatsBomb no Kafka respeitando a ordem e o tempo do jogo (acelerado).
- **Spark Structured Streaming** atualiza, a cada evento, as estatísticas do jogador observado e a probabilidade de vitória (modelo da parte 1, retreinado com as duas ligas).
- **Alertas**, por exemplo: "o jogador X já tem 5 desarmes, acima da média dele".
- Resultados gravados em tabelas Iceberg e exibidos no Streamlit.
- Na apresentação, o Amazon MSK aparece como o caminho de produção; no projeto, Kafka roda localmente para manter o custo zero.

**Ferramentas:** Apache Kafka (Docker, modo KRaft, um broker), Spark Structured Streaming, Streamlit.

## Arquitetura e custo

| Onde | O quê |
|---|---|
| **Local (Docker)** | PostgreSQL (DW), Airbyte, dbt, Spark, Kafka, Streamlit |
| **AWS** | S3, Glue Data Catalog, Athena, Lake Formation, IAM e AWS Budgets, tudo provisionado com Terraform |
| **GitHub** | Código e CI com GitHub Actions (terraform validate, pytest, dbt build) |

Princípios de custo:

- Criar um **AWS Budgets** com alerta antes de qualquer recurso novo.
- Nada de recurso cobrado por hora ligado continuamente: sem Redshift, MSK, MWAA, EMR ou NAT Gateway.
- A EC2 da parte 1 só é ligada quando necessário, e destruída com `terraform destroy` quando não for mais usada.
- Meta: **poucos dólares por mês**, no máximo.

## Riscos e pontos a confirmar

- **Recursos da máquina local:** o Airbyte local pede cerca de 8 GB de RAM livres. Verificar antes da parte 3.
- **Licença da StatsBomb:** confirmar os termos de uso antes de publicar análises.
- **API gratuita:** confirmar cobertura do Brasileirão e limites do plano.
- **Casamento de jogadores entre fontes:** pode exigir correção manual para parte dos casos.
- **Diferença de detalhe entre as ligas:** limita comparações diretas em métricas de evento.

## Entregáveis por parte

Cada parte termina com:

1. Código e documentação no repositório.
2. Seção no README com arquitetura, decisões e resultados.
3. Uma pergunta de scouting respondida com dados.
4. Material para apresentação (diagrama de arquitetura e principais achados).
