# ⚽ Football Data Engineering

Projeto de Engenharia de Dados desenvolvido como parte dos estudos da Pós-Graduação em Engenharia de Dados.

O objetivo é construir, de forma incremental, uma plataforma de dados utilizando informações históricas de partidas de futebol, aplicando conceitos de **Engenharia de Dados, Cloud Computing, Infrastructure as Code e Machine Learning**.

O projeto utiliza dados históricos da Premier League como base para construção do pipeline.

## 🎯 Objetivo

Construir um pipeline de dados capaz de:

- coletar dados históricos de partidas de futebol;
- armazenar os dados brutos em um Data Lake;
- processar e transformar os dados;
- criar datasets preparados para análise e Machine Learning;
- treinar modelos preditivos utilizando os dados processados;
- aplicar boas práticas de infraestrutura e automação.

Além do resultado final, o projeto tem como objetivo praticar tecnologias e conceitos estudados durante a Pós-Graduação em Engenharia de Dados.

## 🏗️ Arquitetura

A arquitetura será construída de forma incremental.

### Arquitetura atual

```text
Terraform
    │
    ▼
AWS
    │
    ▼
Amazon S3
    │
    └── Data Lake
```

Atualmente, a infraestrutura inicial do Data Lake é provisionada utilizando **Terraform**.

O bucket S3 possui:

- versionamento habilitado;
- bloqueio de acesso público;
- tags para identificação dos recursos;
- infraestrutura gerenciada como código.

### Arquitetura planejada

```text
Fonte de dados
     │
     ▼
Amazon S3
     │
     ├── raw
     │
     ▼
Processamento
Python / PySpark
     │
     ▼
Dados processados
     │
     ▼
Feature Engineering
     │
     ▼
Machine Learning
     │
     ▼
Predições
```

Novos componentes da AWS poderão ser incorporados conforme a evolução do projeto.

## 🛠️ Tecnologias

### Utilizadas atualmente

- **Terraform** — provisionamento da infraestrutura como código (IaC)
- **AWS**
- **Amazon S3** — armazenamento do Data Lake
- **AWS CLI** — interação e autenticação com a AWS
- **Git / GitHub** — versionamento do projeto

### Planejadas

- Python
- Pandas
- PySpark
- Apache Parquet
- Docker
- Amazon EC2
- Scikit-learn
- Amazon CloudWatch

Outros serviços poderão ser adicionados conforme a evolução da arquitetura.

## 📁 Estrutura do projeto

```text
football-data-engineering/
│
├── terraform/
│   ├── providers.tf
│   ├── variables.tf
│   ├── main.tf
│   ├── outputs.tf
│   └── .terraform.lock.hcl
│
├── data/
│   └── raw/
│
├── scripts/
│
├── .gitignore
└── README.md
```

## 🗄️ Data Lake

A organização planejada para o Data Lake utiliza diferentes camadas de dados:

```text
S3
│
├── raw/
│   └── premier_league/
│
├── processed/
│
├── features/
│
├── models/
│
└── predictions/
```

A camada `raw` será responsável por preservar os dados originais obtidos da fonte, sem transformações.

As demais camadas serão implementadas conforme a evolução do pipeline.

## 🚧 Status do projeto

### Concluído

- [x] Estrutura inicial do projeto
- [x] Configuração do Terraform
- [x] Configuração do provider AWS
- [x] Provisionamento do bucket S3
- [x] Versionamento do bucket
- [x] Bloqueio de acesso público

### Próximos passos

- [ ] Implementar ingestão dos dados históricos da Premier League
- [ ] Validar os arquivos recebidos
- [ ] Armazenar os dados na camada `raw` do S3
- [ ] Criar ambiente de processamento
- [ ] Implementar transformações com Python/PySpark
- [ ] Armazenar dados processados em Parquet
- [ ] Construir features para Machine Learning
- [ ] Treinar e avaliar modelos
- [ ] Armazenar e disponibilizar as predições

## 📚 Contexto acadêmico

Este projeto foi criado como laboratório prático durante uma Pós-Graduação em Engenharia de Dados.

A implementação busca relacionar conceitos estudados no curso com um projeto completo, incluindo:

- Infrastructure as Code (IaC);
- Cloud Computing;
- Data Lakes;
- ingestão e processamento de dados;
- processamento distribuído;
- containers;
- Machine Learning;
- automação e monitoramento.

## ⚠️ Custos

A arquitetura é desenvolvida com foco em **baixo custo**, utilizando recursos da AWS de forma controlada e evitando manter recursos computacionais ativos desnecessariamente.

Recursos provisionados para experimentos poderão ser destruídos utilizando Terraform quando não forem mais necessários.

---

> Projeto em desenvolvimento. A arquitetura e a documentação serão atualizadas conforme novas etapas forem implementadas.