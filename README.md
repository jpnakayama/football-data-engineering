# Football Data Engineering & ML Platform

Projeto prático de Engenharia de Dados que utiliza partidas históricas da **Premier League** para construir um pipeline reproduzível de ingestão, validação, transformação e disponibilização de dados. A infraestrutura de processamento foi provisionada na AWS com Terraform; a evolução do projeto inclui uma aplicação analítica e previsão de resultados de partidas.

O foco é **resolver um problema de ponta a ponta**, utilizando tecnologias quando elas agregam valor, com atenção à qualidade dos dados, testes, segurança e custos.

## Objetivos

- Obter e preservar dados históricos de partidas da Premier League.
- Armazenar os dados brutos (`raw`) no Amazon S3.
- Validar e transformar os dados com PySpark em ambiente Docker.
- Gerar dados processados em Parquet, particionados por temporada.
- Provisionar e executar o processamento na AWS usando Terraform, EC2, IAM e S3.
- Preparar conjuntos de dados analíticos para dashboards e, futuramente, Machine Learning.
- Evoluir para uma aplicação de consulta de estatísticas e previsão probabilística de resultados.

## Estado atual

| Entrega | Estado |
|---|---|
| Pipeline local de ingestão, validação e processamento | Concluído |
| Infraestrutura AWS provisionada com Terraform | Concluído |
| Processamento Raw → Processed executado na EC2, com S3 | Concluído |
| Data Profiling de quatro temporadas | Concluído |
| Dataset analítico `team_season_stats` | Concluído localmente |
| Testes automatizados | **13 aprovados** |
| Features históricas para ML | Planejado |
| Dashboard e aplicação de previsões | Planejados |

**Resultados atuais:** 1.520 partidas, quatro temporadas completas (2022-23 a 2025-26), 20 equipes por temporada e 80 registros no dataset de estatísticas por equipe/temporada.

> A camada `analytics/` foi gerada e testada **localmente**. Sua execução e publicação no S3 ainda não foram integradas ao pipeline AWS.

## Arquitetura

```text
Football-Data.co.uk
        |
        v
Scripts Python de ingestão
        |
        +--------------------> Amazon S3 / raw/
        |                            |
        v                            |
CSV local                           |
        |                            |
        +------------+---------------+
                     |
                     v
           Docker + PySpark
           (local ou EC2)
                     |
              Data Quality
                     |
                     v
             Parquet / processed/
             (local e Amazon S3)
                     |
                     v
           Data Profiling (local)
                     |
                     v
        Parquet / analytics/ (local)
        team_season_stats
                     |
           +---------+---------+
           |                   |
           v                   v
    Dashboard (futuro)   Features + ML (futuro)
```

O processamento na EC2 utiliza acesso ao S3 via **IAM Role**, sem credenciais estáticas embutidas no container. A camada analítica está sendo desenvolvida localmente antes de sua integração à nuvem.

## Estrutura principal do repositório

```text
football-data-engineering/
├── Dockerfile
├── processing/
│   └── src/
│       ├── process_matches.py
│       ├── profile_matches.py
│       └── build_team_stats.py
├── scripts/
│   ├── download_data.py
│   ├── validate_data.py
│   └── upload_raw_to_s3.py
├── tests/
│   ├── conftest.py
│   ├── test_process_matches.py
│   └── test_build_team_stats.py
├── terraform/                  # Infraestrutura AWS (arquivos .tf)
├── data/                       # Dados locais; não versionar
│   ├── raw/premier_league/
│   ├── processed/premier_league/
│   └── analytics/team_season_stats/
├── .dockerignore
├── .gitignore
├── requirements.txt
└── README.md
```

A listagem apresenta os principais arquivos conhecidos do projeto, não necessariamente todos os arquivos existentes no repositório. **O Dockerfile está na raiz**; sua localização anterior em `processing/` foi descontinuada.

## Fonte dos dados

Os arquivos CSV são obtidos de [Football-Data.co.uk](https://www.football-data.co.uk/), para as temporadas:

- 2022-23
- 2023-24
- 2024-25
- 2025-26

Cada temporada contém 380 partidas, totalizando **1.520**. Os arquivos de origem são preservados na camada `raw`.

## Data Lake e infraestrutura AWS

Bucket de desenvolvimento: `s3://football-data-engineering-dev/`.

```text
s3://football-data-engineering-dev/
├── raw/
│   └── premier_league/
│       ├── season=2022-23/matches.csv
│       ├── season=2023-24/matches.csv
│       ├── season=2024-25/matches.csv
│       └── season=2025-26/matches.csv
└── processed/
    └── premier_league/
        └── season=.../part-*.snappy.parquet
```

O bucket possui bloqueio de acesso público e versionamento habilitado. A infraestrutura é gerenciada com Terraform e inclui:

- Amazon S3 para armazenamento.
- Instância EC2 Ubuntu para execução do container.
- IAM Role e Instance Profile para acesso aos recursos necessários.
- Security Group para controle de rede.
- AWS Systems Manager Session Manager para acesso à instância.

O processamento **Raw → Processed foi executado e validado na AWS**. Os arquivos Parquet foram gravados no S3, com compressão Snappy e particionamento por temporada. A EC2 foi desligada após a execução para reduzir custos de computação; armazenamento S3/EBS e outros recursos podem continuar gerando cobranças.

Comandos usuais do Terraform, executados no diretório correspondente à configuração:

```bash
terraform init
terraform validate
terraform plan
terraform apply
```

**Atenção:** revisar o plano e os custos antes de executar `terraform apply`. Arquivos de estado, segredos e configurações locais sensíveis não devem ser versionados.

## Processamento Raw → Processed

O script `processing/src/process_matches.py`:

1. Lê os CSVs da camada Raw (local ou `s3a://`, conforme as variáveis de ambiente).
2. Verifica colunas obrigatórias, datas, gols nulos e resultados permitidos (`H`, `D`, `A`).
3. Extrai a temporada do caminho do arquivo.
4. Padroniza nomes e tipos.
5. Escreve Parquet particionado por `season`.

Schema de saída:

| Campo | Significado |
|---|---|
| `season` | Temporada |
| `match_date` | Data da partida |
| `home_team` | Mandante |
| `away_team` | Visitante |
| `home_goals` | Gols do mandante |
| `away_goals` | Gols do visitante |
| `result` | `H` (mandante), `D` (empate), `A` (visitante) |

As validações de consistência mais amplas foram realizadas no Data Profiling. Nem todas elas estão ainda incorporadas à função de validação do pipeline Raw → Processed.

## Data Profiling

O script `processing/src/profile_matches.py` lê os arquivos da camada Processed **sem alterá-los** e verifica:

- Schema e total de registros.
- Quantidade de partidas, equipes e intervalo de datas por temporada.
- Distribuição dos resultados.
- Partidas duplicadas.
- Valores nulos e gols negativos.
- Coerência entre resultado e placar.
- Quantidade de jogos por equipe (38, sendo 19 em casa e 19 fora).
- Partidas em que mandante e visitante são a mesma equipe.

**Resultado da inspeção:** 1.520 partidas, 380 por temporada, 20 equipes por temporada e **nenhuma inconsistência identificada nas regras verificadas**. Isso não substitui uma comparação integral com fontes oficiais.

## Camada Analytics

O script `processing/src/build_team_stats.py` lê os Parquets processados e constrói o dataset **`team_season_stats`**, com uma linha por equipe e temporada.

Para cada partida, cria duas perspectivas (mandante e visitante) com `unionByName()`; depois consolida os registros por equipe e temporada.

Campos gerados:

| Campo | Descrição |
|---|---|
| `season`, `team` | Temporada e equipe |
| `matches` | Jogos disputados |
| `wins`, `draws`, `losses` | Vitórias, empates e derrotas |
| `goals_for`, `goals_against` | Gols marcados e sofridos |
| `goal_difference` | Saldo de gols |
| `points` | Pontos: 3 por vitória, 1 por empate |
| `points_percentage` | Pontos obtidos / pontos possíveis × 100 |
| `home_matches`, `away_matches` | Jogos em casa e fora |
| `home_wins`, `away_wins` | Vitórias em casa e fora |

**Saída local:** `data/analytics/team_season_stats/`, em Parquet particionado por temporada, com **80 registros**.

A pontuação é calculada a partir dos resultados das partidas, sem incorporar eventuais punições administrativas. Essa tabela consolida a **temporada completa**: serve para análises retrospectivas, mas **não deve ser usada diretamente para prever partidas da própria temporada**, pois isso causaria vazamento de informação (*data leakage*).

## Testes automatizados

Os testes usam Pytest e pequenos DataFrames PySpark criados em memória, sem depender dos arquivos históricos.

**13 testes aprovados:**

- **7 testes** de processamento: colunas obrigatórias, ausência de colunas, dados válidos, data inválida, gols nulos, resultado inválido e schema transformado.
- **6 testes** analíticos: quantidade de equipes, jogos por equipe, cálculo de pontos, saldo de gols, equilíbrio global entre gols marcados e sofridos e contagem de jogos em casa/fora.

A fixture de sessão Spark é compartilhada em `tests/conftest.py`.

## Execução local com Docker

Os comandos abaixo foram preparados para **PowerShell**, a partir da **raiz do repositório**, com Docker Desktop disponível. O Dockerfile instala Python 3.12, Java 21, PySpark 4.0.1 e Pytest 8.4.2.

### 1. Construir a imagem

```powershell
docker build -t football-data-pipeline .
```

### 2. Executar os testes

```powershell
docker run --rm football-data-pipeline python -m pytest tests/ -v
```

Resultado mais recente: `13 passed`.

### 3. Processar CSVs para Parquet

```powershell
docker run --rm -v "${PWD}/data:/data" football-data-pipeline
```

> O processamento utiliza `mode("overwrite")`: essa execução regrava a saída Processed. Confirme os arquivos de origem antes de executá-la.

### 4. Inspecionar os dados processados

```powershell
docker run --rm -v "${PWD}/data:/data" football-data-pipeline python /app/src/profile_matches.py
```

### 5. Construir o dataset analítico

```powershell
docker run --rm -v "${PWD}/data:/data" football-data-pipeline python /app/src/build_team_stats.py
```

A saída será gravada em `data/analytics/team_season_stats/`. Essa etapa também usa `overwrite` em sua própria saída.

### 6. Conferir containers ativos

```powershell
docker ps
```

Os containers executados com `--rm` são removidos automaticamente ao término. A pasta `data/` é montada como volume; os dados permanecem no computador após a execução.

## Tecnologias utilizadas

| Área | Tecnologias |
|---|---|
| Linguagem e processamento | Python, PySpark |
| Formato de armazenamento | CSV, Parquet (Snappy) |
| Infraestrutura | Terraform, AWS EC2, S3, IAM, Systems Manager |
| Ambiente | Docker |
| Qualidade e testes | Validações de dados, Data Profiling, Pytest |
| Versionamento | Git, GitHub |

Machine Learning, interface web e ferramentas de visualização ainda fazem parte do **planejamento**, não da implementação concluída.

## Próximas etapas

1. **Feature Engineering:** gerar indicadores anteriores a cada partida (forma recente, gols, desempenho como mandante/visitante), sem utilizar dados futuros.
2. **Avaliação preditiva:** separar treino e teste cronologicamente, estabelecer uma baseline e comparar modelos de classificação probabilística de vitória/empate/derrota.
3. **Dashboard:** explorar desempenho por equipe, temporada e local da partida.
4. **Aplicação web:** integrar análises e previsões em uma interface.
5. **Operacionalização:** integrar a camada Analytics ao fluxo AWS e automatizar atualizações quando houver necessidade concreta, com monitoramento e controle de custos.

A evolução da infraestrutura será guiada pelas necessidades do produto, sem adicionar serviços apenas para ampliar a lista de tecnologias.

## Contexto

Projeto desenvolvido como prática de uma **Pós-Graduação em Engenharia de Dados**, com foco em aprendizagem incremental, infraestrutura reproduzível, separação de responsabilidades, qualidade, segurança e uso responsável de recursos em nuvem.
