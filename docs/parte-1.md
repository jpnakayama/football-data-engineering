# Parte 1 — Infraestrutura como Código com Terraform e AWS

> Este documento descreve a parte 1 da [Football Intelligence Platform](../README.md). O código exatamente como foi entregue nesta parte está na tag [`parte-1`](https://github.com/jpnakayama/football-data-engineering/tree/parte-1). Depois dela, o repositório foi reorganizado por componente; os caminhos abaixo já refletem a estrutura atual.

Projeto prático de **Engenharia de Dados** desenvolvido durante uma pós-graduação, utilizando dados históricos da **Premier League** para demonstrar um fluxo de ponta a ponta: ingestão, armazenamento, validação, processamento, preparação analítica, Machine Learning e consumo dos dados em uma aplicação web.

O foco principal é a **infraestrutura reproduzível com Terraform e AWS** e o processamento de dados com **Docker e PySpark**. O dashboard e as previsões são uma demonstração do uso dos dados produzidos pelo pipeline, sem a pretensão de constituir uma plataforma esportiva em produção.

## Objetivos

- Ingerir e preservar dados históricos de partidas da Premier League.
- Provisionar infraestrutura AWS utilizando Terraform.
- Armazenar dados brutos e processados no Amazon S3.
- Validar, padronizar e transformar dados com PySpark em containers Docker.
- Produzir datasets analíticos e features históricas em Parquet.
- Treinar e avaliar modelos de classificação de resultados de partidas.
- Disponibilizar estatísticas e probabilidades em uma aplicação Streamlit local.
- Priorizar simplicidade, segurança, rastreabilidade e controle de custos.

## Estado final do projeto

| Entrega | Situação |
|---|---|
| Ingestão e validação de arquivos CSV | Concluída |
| Infraestrutura AWS provisionada com Terraform | Concluída |
| Processamento Raw → Processed na EC2 com S3 | Executado e validado |
| Data Profiling das partidas | Concluído |
| Dataset analítico `team_season_stats` | Concluído localmente |
| Histórico por equipe e features pré-partida | Concluídos localmente |
| Treinamento e avaliação de modelos de ML | Concluídos localmente |
| Modelo Random Forest salvo em Joblib | Concluído |
| Dashboard histórico e previsão de partidas no Streamlit | Concluídos localmente |
| Implantação do Streamlit na AWS | Fora do escopo |

**Volume utilizado:** quatro temporadas identificadas como 2022-23, 2023-24, 2024-25 e 2025-26, totalizando **1.520 partidas** no dataset utilizado, com 380 partidas por temporada.

> **Escopo de execução:** o processamento Raw → Processed foi executado e validado na AWS. As etapas de Analytics, Feature Engineering, treinamento de ML e aplicação Streamlit foram desenvolvidas e executadas localmente. Não há alegação de que toda a aplicação esteja implantada na AWS.

## Arquitetura

```text
Football-Data.co.uk (CSV)
          |
          v
Scripts Python de ingestão e validação
          |
          +-----------------------> Amazon S3 / raw/
          |                                  |
          v                                  |
     Dados Raw locais                        |
          |                                  |
          +---------------+------------------+
                          |
                          v
                 Docker + PySpark
                 (local ou EC2)
                          |
                          v
                  Data Quality
                          |
                          v
                 Parquet / processed/
                  (local e S3)
                          |
             +------------+-------------+
             |                          |
             v                          v
      Data Profiling              Preparação analítica
             |                    (PySpark local)
             |                          |
             |                +---------+----------+
             |                |                    |
             |                v                    v
             |         team_season_stats    team_match_history
             |                |                    |
             |                |                    v
             |                |              match_features
             |                |                    |
             |                |                    v
             |                |              Treinamento ML
             |                |                    |
             |                |                    v
             |                |           football_model.joblib
             |                |                    |
             +----------------+--------------------+
                              |
                              v
                       Streamlit local
                  Dashboard + previsões
```

Na AWS, o acesso da EC2 ao S3 utiliza **IAM Role / Instance Profile**, evitando credenciais estáticas no container. O **AWS Systems Manager Session Manager** foi utilizado para acessar a instância.

## Arquivos da parte 1 no repositório

```text
football-data-engineering/
├── infra/terraform/            # Infraestrutura AWS (.tf) e script de setup da EC2
├── ingestion/
│   ├── download_premier_league.py
│   ├── validate_premier_league.py
│   └── upload_raw_to_s3.py
├── processing/
│   ├── Dockerfile              # Imagem PySpark (contexto de build: raiz do repositório)
│   ├── src/
│   │   ├── process_matches.py
│   │   ├── profile_matches.py
│   │   ├── build_team_stats.py
│   │   └── build_match_features.py
│   └── tests/
├── ml/
│   └── train_model.py
├── app/
│   ├── data_loader.py
│   ├── prediction.py
│   └── streamlit_app.py
├── data/                       # Dados locais; não versionados
└── models/                     # Modelo treinado; não versionado
```

Os diretórios `data/` e `models/` guardam artefatos gerados localmente e ficam fora do Git. O modelo é gerado de novo por `ml/train_model.py`.

## Fonte dos dados

Os arquivos CSV de partidas foram obtidos de [Football-Data.co.uk](https://www.football-data.co.uk/) e preservados na camada `raw`.

| Temporada | Partidas no dataset |
|---|---:|
| 2022-23 | 380 |
| 2023-24 | 380 |
| 2024-25 | 380 |
| 2025-26 | 380 |
| **Total** | **1.520** |

O projeto utiliza os dados históricos disponíveis nos arquivos processados; **não possui atualização automática nem previsão baseada em dados ao vivo**.

## Infraestrutura AWS e Data Lake

Bucket de desenvolvimento: `s3://football-data-engineering-dev/`.

```text
s3://football-data-engineering-dev/
├── raw/
│   └── premier_league/
│       └── season=.../matches.csv
└── processed/
    └── premier_league/
        └── season=.../part-*.snappy.parquet
```

A infraestrutura provisionada com Terraform inclui:

- **Amazon S3:** armazenamento dos dados brutos e processados, com bloqueio de acesso público e versionamento habilitado.
- **Amazon EC2 (Ubuntu):** execução do processamento em container.
- **IAM Role e Instance Profile:** permissões de acesso necessárias à instância.
- **Security Group:** configuração de rede.
- **AWS Systems Manager:** acesso à instância via Session Manager.

O processamento **Raw → Processed** foi executado e validado na EC2, gravando Parquet particionado por temporada no S3. A instância foi desligada após o uso para reduzir custos.

> **Custos:** uma EC2 desligada deixa de cobrar pelo processamento da instância, mas recursos como S3 e volumes EBS podem continuar gerando custos. Antes de reprovisionar, revisar o plano Terraform e os recursos ativos na conta.

### Comandos Terraform

Executar em `infra/terraform/`:

```bash
terraform init
terraform validate
terraform plan
terraform apply
```

Não versionar arquivos de estado, credenciais, chaves ou configurações locais sensíveis.

## Processamento e qualidade dos dados

### Raw → Processed

O script `processing/src/process_matches.py`:

1. Lê arquivos CSV da camada Raw.
2. Valida colunas obrigatórias, datas, gols e resultados permitidos (`H`, `D`, `A`).
3. Padroniza nomes e tipos de dados.
4. Identifica a temporada a partir da origem do arquivo.
5. Grava Parquet com compressão Snappy, particionado por `season`.

**Schema principal de saída:**

| Campo | Descrição |
|---|---|
| `season` | Temporada |
| `match_date` | Data da partida |
| `home_team`, `away_team` | Equipes mandante e visitante |
| `home_goals`, `away_goals` | Gols de cada equipe |
| `result` | `H`: vitória do mandante; `D`: empate; `A`: vitória do visitante |

### Data Profiling

O script `processing/src/profile_matches.py` inspeciona os dados processados sem modificá-los. Entre as verificações estão schema, volume por temporada, nulos, duplicidades, gols negativos, coerência entre placar e resultado, partidas por equipe e confronto de uma equipe contra si mesma.

Na inspeção realizada, foram identificadas **1.520 partidas**, com **380 por temporada**, e nenhuma inconsistência nas regras verificadas. Essas validações não equivalem a uma auditoria integral contra fontes oficiais.

## Preparação analítica dos dados

### Estatísticas por equipe e temporada

O script `processing/src/build_team_stats.py` gera `data/analytics/team_season_stats/`, com **80 registros** (20 equipes × 4 temporadas).

Indicadores disponíveis:

- Partidas, vitórias, empates e derrotas.
- Gols marcados, gols sofridos e saldo de gols.
- Pontos e percentual dos pontos possíveis.
- Jogos e vitórias em casa e fora.

A pontuação deriva dos resultados das partidas e não considera possíveis punições administrativas. Como são estatísticas consolidadas da temporada, **não são utilizadas diretamente para prever partidas daquela mesma temporada**, evitando vazamento de informação.

### Histórico e features de Machine Learning

O script `processing/src/build_match_features.py` produz dois datasets:

| Dataset | Granularidade | Registros |
|---|---|---:|
| `team_match_history` | Uma linha por equipe em cada partida | 3.040 |
| `match_features` | Uma linha por partida | 1.520 |

As features incluem forma recente das equipes nas **cinco partidas anteriores**, como pontos, média de gols marcados e sofridos, taxa de vitórias, saldo de gols e desempenho específico em casa/fora. Também é calculada a diferença de pontos recentes entre as equipes.

O cálculo das features históricas exclui a própria partida analisada, de modo a evitar utilizar informações do resultado que se deseja prever.

## Machine Learning — treinamento e avaliação

O script `ml/train_model.py` utiliza o dataset `match_features` para classificar o resultado em três classes:

- `H`: vitória do mandante.
- `D`: empate.
- `A`: vitória do visitante.

Foram comparados **Logistic Regression**, **Random Forest** e **HistGradientBoosting**. A divisão dos dados foi cronológica, com conjuntos separados de treino, validação e teste.

### Resultados na validação

| Modelo | Accuracy | F1 macro | Log Loss |
|---|---:|---:|---:|
| Random Forest | 0,5300 | 0,3778 | **0,9932** |
| Logistic Regression | **0,5668** | **0,4360** | 0,9976 |
| HistGradientBoosting | 0,4101 | 0,3477 | 1,1664 |

O **Random Forest** foi selecionado pelo **menor Log Loss na validação**, critério definido para priorizar a qualidade das probabilidades estimadas, apesar de a Logistic Regression ter obtido maior accuracy e F1 macro.

### Avaliação final no teste

| Métrica | Random Forest |
|---|---:|
| Partidas no teste | 202 |
| Accuracy | 0,4109 |
| F1 macro | 0,3156 |
| Log Loss | 1,1299 |

O modelo foi salvo em `models/football_model.joblib`, com **13 features** e metadados de treinamento. O desempenho no teste foi inferior ao observado na validação, o que limita a confiança nas previsões. **O modelo é demonstrativo e não deve ser interpretado como ferramenta confiável para decisões financeiras ou apostas.**

## Aplicação Streamlit

A aplicação é executada **localmente** e contém duas abas:

### Dashboard histórico

- Filtro por temporada e seleção de equipes.
- Indicadores de partidas, gols, média de gols e quantidade de equipes.
- Classificação simplificada por pontos, saldo e gols marcados.
- Gráficos de pontos, saldo de gols e vitórias/empates/derrotas.

Os indicadores superiores representam a temporada selecionada; a tabela e os gráficos também respondem ao filtro de equipes.

### Previsão de partidas

- Seleção de mandante e visitante.
- Construção das 13 features a partir do histórico disponível de cada equipe.
- Inferência com o Random Forest salvo.
- Exibição das probabilidades de vitória do mandante, empate e vitória do visitante.

A previsão utiliza os **últimos jogos disponíveis no dataset**, não resultados ao vivo. Equipes que participaram de temporadas diferentes podem aparecer na seleção. É necessário histórico suficiente para calcular as médias das últimas cinco partidas e das últimas cinco partidas no mando correspondente.

## Como executar localmente

Os comandos a seguir consideram **Windows PowerShell**, a partir da raiz do repositório.

### Pré-requisitos

- Python 3.12 e ambiente virtual (`.venv`).
- Docker Desktop para processamento PySpark.
- Dependências Python instaladas para o Streamlit e a inferência.
- Datasets locais nas pastas `data/` e modelo treinado em `models/`.

### 1. Ativar o ambiente virtual

```powershell
.\.venv\Scripts\Activate.ps1
```

Para instalar as dependências da aplicação, caso ainda não estejam presentes:

```powershell
python -m pip install streamlit pandas pyarrow joblib scikit-learn==1.7.2
```

A versão `1.7.2` do scikit-learn corresponde à utilizada para salvar o modelo neste projeto.

### 2. Construir a imagem de processamento

```powershell
docker build -f processing/Dockerfile -t football-data-pipeline .
```

### 3. Executar os testes

```powershell
docker run --rm football-data-pipeline python -m pytest tests/ -v
```

### 4. Processar os CSVs em Parquet

```powershell
docker run --rm -v "${PWD}/data:/data" football-data-pipeline
```

> A transformação pode sobrescrever a saída Processed existente. Verifique os dados de origem antes de reexecutá-la.

### 5. Executar o Data Profiling

```powershell
docker run --rm -v "${PWD}/data:/data" football-data-pipeline python /app/src/profile_matches.py
```

### 6. Gerar a camada analítica

```powershell
docker run --rm -v "${PWD}/data:/data" football-data-pipeline python /app/src/build_team_stats.py
```

### 7. Gerar o histórico e as features

```powershell
docker run --rm -v "${PWD}/data:/data" football-data-pipeline python /app/src/build_match_features.py
```

Esses comandos pressupõem a imagem Docker e os caminhos de dados configurados conforme o projeto. As saídas são gravadas em volumes locais.

### 8. Treinar o modelo

```powershell
docker run --rm -v "${PWD}/data:/data" -v "${PWD}/models:/app/models" football-data-pipeline python /app/src/train_model.py
```

### 9. Iniciar o Streamlit

Com os datasets e o modelo já gerados, execute no ambiente virtual local:

```powershell
python -m streamlit run app/streamlit_app.py
```

Acesse **http://localhost:8501** no navegador. Para encerrar o servidor, pressione `Ctrl + C` no terminal.

> **Observação:** o Streamlit não roda dentro do Docker neste projeto. Docker é utilizado para o processamento PySpark; a aplicação e a inferência são executadas no ambiente virtual Python local.

## Testes e verificações realizadas

Foram implementados testes automatizados com **Pytest** para o processamento e a preparação analítica, além de verificações de geração de features. Os testes utilizam pequenos DataFrames PySpark em memória.

Também foram validados manualmente:

- Leitura dos datasets locais: **1.520 partidas**, **80 registros analíticos**, **1.520 registros de features** e **3.040 registros de histórico**.
- Carregamento do artefato Random Forest com scikit-learn **1.7.2**.
- Classes do modelo `['A', 'D', 'H']` e conjunto de **13 features**.
- Execução da inferência, com probabilidades que somam **1,0**.
- Abertura e funcionamento das duas abas da aplicação Streamlit.

A quantidade exata de testes aprovados deve ser conferida na saída da execução atual do Pytest antes de ser informada como resultado final.

## Tecnologias

| Área | Tecnologias |
|---|---|
| Linguagem | Python |
| Infraestrutura como código | Terraform |
| Nuvem | AWS EC2, S3, IAM, Systems Manager |
| Processamento | Apache Spark / PySpark |
| Containerização | Docker |
| Armazenamento | CSV, Parquet com Snappy |
| Qualidade e testes | Data Quality, Data Profiling, Pytest |
| Machine Learning | scikit-learn, pandas, Joblib |
| Visualização | Streamlit |
| Versionamento | Git e GitHub |

## Limitações e decisões de escopo

- A infraestrutura AWS foi utilizada para o processamento Raw → Processed; a camada analítica, o treinamento e a aplicação são locais.
- Os dados não são atualizados automaticamente.
- A classificação histórica é simplificada e não contempla todos os critérios oficiais de desempate ou punições administrativas.
- O modelo preditivo apresenta desempenho limitado no conjunto de teste e utiliza apenas as features históricas disponíveis.
- O projeto não inclui hospedagem pública do Streamlit, API de previsão, monitoramento contínuo ou novos serviços em nuvem.
- Novas fontes de dados e análises mais detalhadas poderão ser consideradas em trabalhos futuros, sem ampliar o escopo desta entrega.

## Contexto acadêmico

Este projeto foi desenvolvido como prática de uma **pós-graduação em Engenharia de Dados**, com ênfase em infraestrutura como código, serviços AWS, processamento distribuído, organização de camadas de dados, validação e consumo de informações.

A aplicação Streamlit e o modelo de Machine Learning complementam a entrega, demonstrando um uso concreto dos dados preparados pelo pipeline. A prioridade foi construir uma solução **reproduzível, compreensível e com custos controlados**, evitando complexidade sem justificativa.
