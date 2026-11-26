-- Camadas do Data Warehouse.
CREATE SCHEMA IF NOT EXISTS staging;  -- dados brutos carregados das fontes
CREATE SCHEMA IF NOT EXISTS dw;       -- dimensões e fatos
CREATE SCHEMA IF NOT EXISTS mart;     -- visões prontas para análise e para o agente
CREATE SCHEMA IF NOT EXISTS audit;    -- auditoria de cargas e consultas

COMMENT ON SCHEMA staging IS 'Dados brutos carregados das fontes, sem transformação.';
COMMENT ON SCHEMA dw IS 'Modelo dimensional: dimensões e fatos.';
COMMENT ON SCHEMA mart IS 'Visões de consumo para análise, Streamlit e agente de scouting.';
COMMENT ON SCHEMA audit IS 'Registros de auditoria de cargas e consultas.';
