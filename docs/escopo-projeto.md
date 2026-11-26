# Football Intelligence Platform — Escopo do projeto

Documento de escopo das próximas etapas do projeto da pós-graduação em Engenharia de Dados. A parte 1 (Infraestrutura como Código) está concluída e descrita no [README](../README.md). Este documento define as partes 2 a 5.

> Projeto pessoal. Usa apenas contas pessoais (AWS, GitHub, Kaggle) e dados públicos.

## Visão

Uma única plataforma de dados de futebol que cresce a cada módulo do curso. Cada parte responde a **uma pergunta de um departamento de scouting**: *quem contratar, por quanto e como ele vai render?* Cada pergunta respondida vira uma entrega apresentável, por exemplo um post no LinkedIn com o problema, a arquitetura e o resultado.

| Decisão | Escolha |
|---|---|
| Ligas | Referência: as cinco grandes ligas da Europa (Premier League, La Liga, Bundesliga, Serie A e Ligue 1), com a Premier League como destino das análises. Também entram as outras 9 ligas europeias com cobertura completa (Holanda, Portugal, Bélgica, Turquia, Escócia, Grécia, Rússia, Ucrânia, Dinamarca), copas e torneios da UEFA, como mercados de origem e de saída. O Brasileirão foi avaliado como liga principal e descartado por falta de dados por jogador (ver [profiling](parte-2/profiling-fontes.md)) |
| Público | Clubes e scouting (foco no **jogador**, não só na partida) |
| Corte dos dados | Temporadas encerradas: 2012-13 a 2025-26 |
| Tempo real | Apenas **replay** de dados históricos (sem dados ao vivo) |
| Custo | Mínimo: execução local em Docker; na AWS, apenas serviços de custo próximo de zero |
| Produto final | O app Streamlit da parte 1 evolui para uma ferramenta de scouting, e um agente de scouting via MCP consulta a plataforma (ver [Trilha de IA](#trilha-de-ia-agente-de-scouting-via-mcp)) |
| Análises | Simples, mas gerando **produtos de dados** que não existem em nenhuma fonte isolada. O foco continua sendo arquitetura e engenharia |

## Fontes de dados

| Fonte | Cobertura | Uso | Observações |
|---|---|---|---|
| [Football-Data.co.uk](https://www.football-data.co.uk/) | As cinco ligas com resultados, estatísticas de jogo (chutes, chutes no alvo, escanteios, faltas, cartões) e odds | Partidas, estatísticas e odds | Já usado na parte 1. Mesmas colunas nas cinco ligas |
| [Transfermarkt datasets](https://github.com/dcaribou/transfermarkt-datasets) (Kaggle) | 14 ligas europeias (incluindo as cinco grandes), copas e torneios da UEFA de 2012-13 a 2025-26, com partidas e atuações (minutos, gols, assistências, cartões) em todos os jogos; outras 17 ligas só com partidas de 2024-25 e 2025-26; transferências e valor de mercado de 50 mil jogadores. Tabelas: players, clubs, games, appearances, game_events, transfers, player_valuations, competitions | Base principal de jogadores, atuações, valor de mercado e transferências | Licença CC0. **Atualizações pausadas em 6/7/2026**: cobre as temporadas encerradas, mas não serve como fonte contínua |
| [StatsBomb Open Data](https://github.com/statsbomb/open-data) | Eventos lance a lance. Temporada 2015/16 das cinco ligas, além de outras competições | Perfis de estilo de jogo (parte 4) e replay (parte 5) | Exige citar a StatsBomb como fonte e usar o logo nas publicações. Confirmar os termos do LICENSE antes de publicar |
| API de futebol com plano gratuito (candidata: football-data.org) | A confirmar | Demonstração opcional de ingestão de API na parte 3 | Verificar cobertura e limites do plano gratuito |

**Particularidades conhecidas:**

- A Bundesliga tem 18 clubes (306 partidas por temporada) e a Ligue 1 também, desde 2023-24.
- A Ligue 1 2019-20 foi encerrada mais cedo por causa da Covid (279 partidas).
- Os nomes de clubes e jogadores diferem entre as fontes e precisam de tabelas de correspondência.

## Partes do projeto

### Parte 1 — Infraestrutura como Código (concluída)

*"Dá para prever o resultado de uma partida?"*

Terraform, AWS (S3, EC2, IAM, SSM), PySpark em Docker, features pré-partida, modelo de classificação e Streamlit. Detalhes no [README](../README.md).

### Parte 2 — Data Warehouse: modelagem, implementação e governança

*"Quanto vale a produção de um jogador de outra liga se ele for para a Premier League?"*

- **Modelo dimensional centrado no jogador**:
  - Fatos: atuações (minutos, gols, assistências, cartões por jogo), valor de mercado ao longo do tempo, transferências, partidas (com estatísticas e odds).
  - Dimensões: jogador (SCD tipo 2 para clube e posição), clube, competição, temporada, data.
- **Desafios de modelagem:**
  - Dimensões compartilhadas entre cinco ligas com números de clubes e de partidas diferentes.
  - Temporada interrompida (Ligue 1 2019-20), tratada como dado real e não como falha.
  - Mesmo clube com nomes diferentes nas duas fontes, exigindo tabela de correspondência.
- **Métricas de scouting:** participação em gols a cada 90 minutos, minutos jogados por idade, valor de mercado por produção.
- **Produtos de dados** (cruzam fontes e geram informação que nenhuma tabela traz sozinha):
  1. **Carreira reconstruída do jogador:** clubes, valor de mercado e minutos ao longo do tempo, juntando transferências, avaliações e atuações.
  2. **Fator de conversão entre ligas:** a partir dos jogadores que atuaram em mais de uma liga, estimar quanto vale uma participação em gol em cada liga, inclusive Eredivisie, Liga Portugal e liga belga, em termos de Premier League.
  3. **Valor de mercado esperado contra o real:** um modelo simples (idade, posição, produção, liga, minutos) estima o valor esperado; a diferença para o valor real gera a lista de subvalorizados, com critério explícito.
- **Análise principal:** contratações vindas das outras quatro ligas para a Premier League deram certo? Minutos antes e depois da transferência, valor pago e retorno em campo.
- **Trajetórias de carreira:** desempenho dos jogadores antes, durante e depois de passar pelas cinco ligas, em quatro cenários: fora → dentro (764 jogadores), dentro → fora (879), fora → dentro → fora (324) e dentro → fora → dentro (158). Detalhes e cuidados de interpretação na [modelagem](parte-2/modelagem.md#71-trajetórias-de-carreira).
- **Recorte para o público brasileiro:** os brasileiros nas cinco grandes ligas, com trajetória, minutos e valor de mercado.
- **Limite da análise:** o Transfermarkt traz gols, assistências, minutos e cartões. Isso é suficiente para atacantes e meias, mas fraco para defensores; métricas de estilo de jogo ficam para a parte 4.
- **Extras opcionais:**
  - **Sucesso de transferência:** marcar cada transferência como bem-sucedida ou não pela participação em minutos na primeira temporada no novo clube.
  - **Eficiência do mercado de apostas por liga:** comparar as probabilidades implícitas nas odds com os resultados reais.
- **Governança:** dicionário de dados, perfis de acesso, segurança por linha, mascaramento e discussão de LGPD e GDPR (os dados são de pessoas, ainda que públicos), regras de qualidade.

**Ferramentas:** PostgreSQL em Docker (o DW), SQL.

### Parte 3 — ELT com Airbyte, dbt e SQL

*"Como ter uma shortlist atualizada a cada rodada?"*

- **Carga histórica completa**, seguida de **replay rodada a rodada**: uma fonte simulada libera os dados de cada rodada em ordem cronológica e o Airbyte sincroniza de forma incremental.
- **dbt** reconstrói o DW da parte 2 em camadas (staging, intermediate, marts), com testes, documentação e snapshots (SCD tipo 2).
- **Tabelas de consumo:** forma recente do jogador (últimos 5 jogos) e shortlist por posição, idade e faixa de valor.
- **Problema real de scouting:** casar o mesmo jogador em fontes diferentes (grafias e IDs distintos). Tabela de correspondência e testes no dbt.
- **Opcional:** ingestão de uma API de futebol gratuita, como demonstração de conector de API.

**Ferramentas:** Airbyte (local, Docker), dbt Core com adaptador Postgres.

### Parte 4 — Data Lake e Data Lakehouse

*"Qual é o estilo de jogo desse atleta?"*

- **Camadas bronze, silver e gold** no S3 em tabelas Apache Iceberg (time travel, evolução de schema, MERGE).
- **Eventos lance a lance** da StatsBomb para a temporada 2015/16 das cinco ligas (incluindo o Leicester campeão): passes progressivos, desarmes, pressões, conduções por jogador.
- **Busca por similaridade entre ligas:** "quem, na Serie A ou na Bundesliga, joga parecido com o Kanté de 2015/16?"
- **Governança do lake:** catálogo e permissões por camada.

**Ferramentas:** S3, Apache Iceberg, AWS Glue Data Catalog, Amazon Athena, AWS Lake Formation, PySpark em Docker (local).

### Parte 5 — PySpark e Apache Kafka: batch e streaming

*"O scout assistindo ao jogo em tempo real"*

- **Replay** de uma partida da Premier League: um produtor publica os eventos da StatsBomb no Kafka respeitando a ordem e o tempo do jogo (acelerado).
- **Spark Structured Streaming** atualiza, a cada evento, as estatísticas do jogador observado e a probabilidade de vitória (modelo da parte 1, retreinado com as cinco ligas).
- **Alertas**, por exemplo: "o jogador X já tem 5 desarmes, acima da média dele".
- Resultados gravados em tabelas Iceberg e exibidos no Streamlit.
- Na apresentação, o Amazon MSK aparece como o caminho de produção; no projeto, Kafka roda localmente para manter o custo zero.

**Ferramentas:** Apache Kafka (Docker, modo KRaft, um broker), Spark Structured Streaming, Streamlit.

## Trilha de IA: agente de scouting via MCP

O uso de IA entra como uma trilha que atravessa as partes 2 a 5, e não como uma parte separada. O agente é o **consumidor** da plataforma: ele só é confiável porque roda sobre dados modelados, documentados e governados. Como não é um módulo do curso, a trilha é leve e não tira o foco da engenharia.

**Componente central:** um servidor MCP em Python, rodando localmente, que expõe a plataforma como **ferramentas com escopo definido**, e não como acesso livre a SQL. Cliente: Claude Desktop ou Claude Code, sem custo de API nem de AWS.

Exemplos de ferramentas:

- `buscar_jogadores(posição, idade, liga, faixa_de_valor)`
- `comparar_jogadores(a, b)`
- `trajetoria(jogador)`
- `explicar_metrica(nome)`: responde com a definição, a origem e a data de corte dos dados, a partir do dicionário de dados.

| Parte | O que a trilha de IA ganha |
|---|---|
| **2. DW** | Primeira versão do servidor MCP sobre os marts e o dicionário de dados. Acesso com **perfil somente leitura e mascaramento** (o agente vê a idade, não a data de nascimento). Toda consulta do agente fica registrada numa tabela de auditoria |
| **3. Airbyte + dbt** | As **definições de métricas** passam a vir do dbt: o agente usa a mesma definição que o dashboard. A IA também entra na engenharia: **casamento de jogadores entre fontes** com regras e similaridade de nomes primeiro, e um LLM só para os casos ambíguos, com revisão humana e taxa de acerto medida |
| **4. Lakehouse** | Ferramenta `jogadores_similares(jogador)` sobre os perfis de estilo de jogo |
| **5. Streaming** | Ferramenta que lê o estado da partida em replay: "como está o jogador X neste jogo?" |

**Princípios da trilha:**

- O agente nunca acessa dados brutos nem dados pessoais sem mascaramento.
- Ferramentas somente leitura, com limite de linhas por resposta.
- Toda resposta indica a fonte e a data de corte dos dados.
- Toda consulta é auditada.

**Entregável final:** um post de fechamento mostrando a plataforma completa e o agente de scouting que só responde com dados governados.

## Arquitetura e custo

| Onde | O quê |
|---|---|
| **Local (Docker)** | PostgreSQL (DW), Airbyte, dbt, Spark, Kafka, Streamlit, servidor MCP |
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
- **API gratuita:** confirmar cobertura e limites do plano.
- **Casamento de jogadores entre fontes:** pode exigir correção manual para parte dos casos.
- **Fator de conversão entre ligas:** a amostra por par de ligas e por posição pode ficar pequena; nesses casos o resultado será apresentado como indicativo.
- **Viés de seleção nas transferências:** só jogadores considerados bons o bastante mudam de liga, o que precisa ser declarado ao interpretar o fator de conversão.
- **Trilha de IA tomando o foco:** cada parte entrega primeiro a engenharia do módulo; as ferramentas do agente vêm depois.
- **Custo de LLM no casamento de jogadores:** usar o modelo só nos casos ambíguos, depois das regras determinísticas.

## Entregáveis por parte

Cada parte termina com:

1. Código e documentação no repositório.
2. Seção no README com arquitetura, decisões e resultados.
3. Uma pergunta de scouting respondida com dados.
4. Novas ferramentas do agente de scouting, quando a parte prevê.
5. Material para apresentação (diagrama de arquitetura e principais achados).
