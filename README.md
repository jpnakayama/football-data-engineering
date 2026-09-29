# Football Data Engineering & ML Platform

Projeto de Engenharia de Dados desenvolvido com o objetivo de aplicar, na prática, conceitos de infraestrutura como código, cloud computing, ingestão, processamento, qualidade e transformação de dados.

O projeto utiliza dados históricos da Premier League e será evoluído gradualmente até a construção de uma plataforma de dados com processamento em cloud e aplicação de Machine Learning.

## Objetivo

Construir um pipeline de dados reproduzível capaz de:

1. Coletar dados históricos de partidas da Premier League;
2. Armazenar os dados brutos em um Data Lake no Amazon S3;
3. Validar a qualidade dos dados antes do processamento;
4. Processar e transformar os dados utilizando PySpark;
5. Armazenar os dados processados em formato Parquet;
6. Executar o processamento de forma reproduzível utilizando Docker;
7. Provisionar a infraestrutura AWS utilizando Terraform;
8. Evoluir posteriormente para Feature Engineering e Machine Learning.

---

## Arquitetura atual

```text
Football-Data.co.uk
        │
        ▼
Python - Ingestão
        │
        ├──────────────────────────────► Amazon S3
        │                                  │
        │                                  └── raw/
        │
        ▼
CSV Raw local
        │
        ▼
Docker
        │
        ▼
PySpark
        │
        ├── Data Quality
        │   ├── colunas obrigatórias
        │   ├── datas válidas
        │   ├── gols não nulos
        │   └── resultados H / D / A
        │
        ▼
Transformação
        │
        ▼
Parquet
        │
        ▼
Particionamento por temporada
        │
        ▼
Processed local

pytest
  │
  └── 7 testes automatizados
```

Atualmente, a camada Raw já está armazenada no Amazon S3. O processamento PySpark ainda é executado localmente dentro de um container Docker.

A próxima etapa será levar esse mesmo ambiente de processamento para uma instância EC2.

---

## Estrutura do projeto

```text
football-data-engineering/
│
├── data/
│   ├── raw/
│   │   └── premier_league/
│   │       ├── 2022-23.csv
│   │       ├── 2023-24.csv
│   │       ├── 2024-25.csv
│   │       └── 2025-26.csv
│   │
│   └── processed/
│       └── premier_league/
│
├── processing/
│   ├── Dockerfile
│   └── src/
│       └── process_matches.py
│
├── scripts/
│   ├── download_data.py
│   ├── validate_data.py
│   └── upload_raw_to_s3.py
│
├── tests/
│   └── test_process_matches.py
│
├── terraform/
│   ├── main.tf
│   ├── outputs.tf
│   ├── providers.tf
│   ├── variables.tf
│   └── .terraform.lock.hcl
│
├── .dockerignore
├── .gitignore
├── requirements.txt
└── README.md
```

Os diretórios locais de dados e arquivos de estado do Terraform não são versionados no Git.

---

## Fonte dos dados

Os dados utilizados são disponibilizados pelo Football-Data.co.uk e correspondem a partidas da Premier League.

Temporadas utilizadas inicialmente:

- 2022/23
- 2023/24
- 2024/25
- 2025/26

Os arquivos são obtidos em formato CSV e mantidos sem transformação na camada Raw.

---

## Data Lake

O Data Lake inicial foi provisionado no Amazon S3 utilizando Terraform.

Estrutura da camada Raw:

```text
s3://football-data-engineering-dev/
└── raw/
    └── premier_league/
        ├── season=2022-23/
        │   └── matches.csv
        ├── season=2023-24/
        │   └── matches.csv
        ├── season=2024-25/
        │   └── matches.csv
        └── season=2025-26/
            └── matches.csv
```

O bucket possui:

- bloqueio de acesso público;
- versionamento habilitado;
- gerenciamento por Terraform.

A camada Raw preserva os dados recebidos da fonte. Limpeza, tipagem e transformação são realizadas somente durante a geração da camada Processed.

---

## Ingestão

A ingestão é dividida em três etapas:

```text
download_data.py
       │
       ▼
Download dos CSVs
       │
       ▼
validate_data.py
       │
       ▼
Validação inicial
       │
       ▼
upload_raw_to_s3.py
       │
       ▼
Amazon S3 / Raw
```

Essa separação mantém responsabilidades distintas para aquisição, validação e armazenamento dos dados.

---

## Processamento com PySpark

O processamento é realizado utilizando PySpark dentro de um container Docker.

O pipeline:

1. Lê os arquivos CSV da camada Raw;
2. Valida a estrutura e a qualidade dos dados;
3. Identifica a temporada de cada partida;
4. Seleciona os campos relevantes;
5. Padroniza os nomes das colunas;
6. Converte os tipos de dados;
7. Grava o resultado em formato Parquet;
8. Particiona os dados por temporada.

O schema processado contém inicialmente:

```text
season
match_date
home_team
away_team
home_goals
away_goals
result
```

O resultado é armazenado localmente em:

```text
data/processed/premier_league/
├── season=2022-23/
├── season=2023-24/
├── season=2024-25/
└── season=2025-26/
```

---

## Data Quality

Antes de gerar a camada Processed, o pipeline executa validações de qualidade.

São verificadas:

- presença das colunas obrigatórias;
- validade das datas;
- existência de gols nulos;
- validade do resultado da partida.

Os resultados aceitos são:

```text
H = vitória do time mandante
D = empate
A = vitória do time visitante
```

Caso alguma regra seja violada, o processamento é interrompido antes da escrita da camada Processed.

Dessa forma, dados que não atendam aos requisitos mínimos de qualidade não são propagados para as etapas seguintes do pipeline.

---

## Docker

Docker é utilizado para tornar o ambiente de processamento reproduzível e independente da máquina hospedeira.

A imagem contém:

```text
Python 3.12
+
Java 21
+
PySpark 4.0.1
+
Código de processamento
```

Isso permite utilizar essencialmente o mesmo ambiente durante o desenvolvimento local e, futuramente, na instância EC2.

Os dados não são incorporados à imagem Docker. Durante a execução local, o diretório `data/` é disponibilizado ao container através de um volume.

---

## Testes automatizados

As regras de qualidade e transformação são testadas utilizando Pytest.

Atualmente existem 7 testes automatizados:

1. Dataset contendo todas as colunas obrigatórias;
2. Detecção de coluna obrigatória ausente;
3. Dataset válido;
4. Detecção de data inválida;
5. Detecção de gols nulos;
6. Detecção de resultado diferente de `H`, `D` ou `A`;
7. Validação da estrutura resultante da transformação.

Os testes utilizam pequenos DataFrames PySpark criados especificamente para cada cenário, sem depender dos arquivos reais da Premier League.

---

## Execução local

### Criar a imagem Docker

Na raiz do projeto:

```bash
docker build -t football-pyspark -f processing/Dockerfile .
```

### Executar os testes

```bash
docker run --rm football-pyspark pytest -v
```

Resultado esperado:

```text
7 passed
```

### Executar o processamento

PowerShell:

```powershell
docker run --rm `
  -v "${PWD}/data:/data" `
  football-pyspark
```

Ao final da execução, os arquivos Parquet são disponibilizados em:

```text
data/processed/premier_league/
```

### Verificar containers em execução

```bash
docker ps
```

Os containers utilizados pelo projeto são executados com `--rm`, portanto são removidos automaticamente após o término do processamento.

---

## Infraestrutura como Código

A infraestrutura AWS é gerenciada utilizando Terraform.

Atualmente o Terraform provisiona:

```text
Terraform
   │
   ▼
Amazon S3
   │
   └── Data Lake
```

Principais comandos:

```bash
terraform init
terraform validate
terraform plan
terraform apply
```

Os arquivos de estado (`*.tfstate`) e configurações locais não são enviados para o Git.

---

## Tecnologias utilizadas

### Engenharia de Dados

- Python
- PySpark
- Pandas
- Parquet

### Qualidade e testes

- Pytest
- Validações de Data Quality

### Cloud

- AWS
- Amazon S3
- AWS CLI

### Infraestrutura e ambiente

- Terraform
- Docker
- Git
- GitHub

---

## Status do projeto

- [x] Estrutura inicial do projeto
- [x] Infraestrutura inicial com Terraform
- [x] Data Lake Raw no Amazon S3
- [x] Download dos dados da Premier League
- [x] Validação inicial da ingestão
- [x] Upload da camada Raw para S3
- [x] Ambiente reproduzível com Docker
- [x] Processamento com PySpark
- [x] Validações de Data Quality
- [x] Conversão para Parquet
- [x] Particionamento por temporada
- [x] Testes automatizados com Pytest
- [ ] Provisionamento de EC2 com Terraform
- [ ] IAM Role e Instance Profile para EC2
- [ ] Configuração de Security Group
- [ ] Execução do container Docker na EC2
- [ ] Leitura direta da camada Raw no S3
- [ ] Escrita da camada Processed no S3
- [ ] Feature Engineering
- [ ] Modelo de Machine Learning
- [ ] Armazenamento das predições
- [ ] Monitoramento do pipeline

---

## Próxima etapa: processamento na AWS

A próxima evolução do projeto será migrar a execução do processamento para AWS sem reescrever a lógica já validada localmente.

Arquitetura planejada:

```text
                    AWS
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
      Amazon S3                EC2
          │                     │
       Raw Data              Docker
          │                     │
          └────────────────► PySpark
                                │
                                ▼
                           Amazon S3
                                │
                           Processed
```

A infraestrutura será provisionada com Terraform e deverá incluir:

```text
Terraform
├── S3
├── EC2
├── IAM Role
├── Instance Profile
└── Security Group
```

A EC2 receberá acesso ao S3 através de uma IAM Role, evitando o armazenamento de Access Keys dentro da instância ou do container.

O objetivo será executar:

```text
S3 Raw
   ↓
EC2
   ↓
Docker
   ↓
PySpark
   ↓
Data Quality
   ↓
Transformação
   ↓
Parquet
   ↓
S3 Processed
```

Após essa etapa, o projeto avançará para Feature Engineering e Machine Learning.

---

## Contexto

Este projeto faz parte dos estudos de uma Pós-Graduação em Engenharia de Dados e tem como objetivo consolidar conhecimentos através da construção incremental de uma solução completa.

O projeto prioriza:

- aplicação prática dos conceitos estudados;
- infraestrutura reproduzível;
- separação de responsabilidades;
- qualidade de dados;
- testes automatizados;
- segurança no acesso aos recursos AWS;
- controle de custos em cloud;
- evolução incremental da arquitetura.