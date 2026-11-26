# Football Intelligence Platform

Plataforma de dados de futebol construída ao longo de uma pós-graduação em Engenharia de Dados. Cada módulo do curso acrescenta uma camada à mesma plataforma, e cada camada responde a uma pergunta de um departamento de **scouting**: *quem contratar, por quanto e como ele vai render?*

Os dados cobrem as cinco grandes ligas da Europa (Premier League, La Liga, Bundesliga, Serie A e Ligue 1), temporadas 2012-13 a 2025-26. O escopo completo está em [docs/escopo-projeto.md](docs/escopo-projeto.md).

> Projeto pessoal e acadêmico, com dados públicos. Não há dados ao vivo nem uso para apostas.

## Partes do projeto

| Parte | Módulo | Pergunta | Situação |
|---|---|---|---|
| 1 | Infraestrutura como Código (Terraform, AWS) | Dá para prever o resultado de uma partida? | ✅ Concluída · [documentação](docs/parte-1.md) · tag [`parte-1`](https://github.com/jpnakayama/football-data-engineering/tree/parte-1) |
| 2 | Data Warehouse: modelagem, implementação e governança | Quanto vale a produção de um jogador de outra liga na Premier League? | 🚧 Em andamento · [profiling das fontes](docs/parte-2/profiling-fontes.md) |
| 3 | ELT com Airbyte, dbt e SQL | Como ter uma shortlist atualizada a cada rodada? | Planejada |
| 4 | Data Lake e Lakehouse | Qual é o estilo de jogo desse atleta? | Planejada |
| 5 | PySpark e Kafka: batch e streaming | O scout acompanhando o jogo em tempo real (replay) | Planejada |

Uma **trilha de IA** atravessa as partes 2 a 5: um agente de scouting exposto por um servidor MCP, com ferramentas somente leitura sobre dados governados.

## Estrutura do repositório

O código é organizado por componente da plataforma; a documentação, por parte do projeto.

```text
football-data-engineering/
├── infra/terraform/   # Infraestrutura AWS como código
├── ingestion/         # Download, validação e envio dos dados brutos
├── processing/        # Pipeline PySpark em Docker (parte 1) e testes
├── warehouse/         # Data Warehouse PostgreSQL (parte 2)
├── ml/                # Treinamento do modelo
├── app/               # Aplicação Streamlit
├── docs/              # Escopo, documentação de cada parte e decisões
├── data/              # Dados locais (não versionados)
└── models/            # Modelos treinados (não versionados)
```

## Como começar

- **Parte 1 (pipeline PySpark, modelo e Streamlit):** ver [docs/parte-1.md](docs/parte-1.md#como-executar-localmente).
- **Parte 2 (Data Warehouse):**

  ```powershell
  python ingestion/download_warehouse_sources.py
  Copy-Item warehouse/.env.example warehouse/.env   # e defina uma senha local
  docker compose -f warehouse/docker-compose.yml --env-file warehouse/.env up -d
  ```

## Fontes de dados

- [Football-Data.co.uk](https://www.football-data.co.uk/): partidas, estatísticas e odds.
- [Transfermarkt datasets](https://github.com/dcaribou/transfermarkt-datasets) (licença CC0): jogadores, atuações, valor de mercado e transferências.
- [StatsBomb Open Data](https://github.com/statsbomb/open-data): eventos lance a lance (a partir da parte 4), com a devida atribuição à StatsBomb.

## Tecnologias

| Área | Tecnologias |
|---|---|
| Infraestrutura | Terraform, AWS (S3, EC2, IAM, Systems Manager) |
| Processamento | Python, PySpark, Docker |
| Data Warehouse | PostgreSQL |
| Machine Learning | scikit-learn |
| Visualização | Streamlit |
| Próximas partes | Airbyte, dbt, Apache Iceberg, AWS Glue e Athena, Apache Kafka, MCP |

## Contexto acadêmico

Projeto desenvolvido como prática de uma **pós-graduação em Engenharia de Dados**. A prioridade é uma plataforma reproduzível, documentada e com custo mínimo: o processamento roda localmente em Docker e a AWS é usada apenas onde o custo é próximo de zero.
