-- Banco do prototipo bancario do Bootcamp QI Tech 2026 (DAD-15: nasce inteiro).
--
-- Roda quando o volume do banco nasce (database/Dockerfile) e a cada
-- DbUtils.rollback() dos testes. Mudou este arquivo: docker compose down -v.
--
-- Regras de escrita deste arquivo:
-- * so caracteres ASCII, sem acento: o DbUtils le o arquivo no Windows;
-- * nenhum sinal de porcentagem: o DbUtils executa o texto pelo psycopg2;
-- * dinheiro em centavos inteiros, BIGINT (DAD-08);
-- * id interno SERIAL e key publica CHAR(36), UUID v4 (DAD-01, DAD-12).

-- ============================================================
-- Tipos fixos
-- Os ids saem da ordem dos INSERT (o banco nasce vazio). Os indices
-- parciais mais abaixo usam esses ids.
-- ============================================================

CREATE TABLE account_type(
    id                              SERIAL PRIMARY KEY,
    enumerator                      VARCHAR(50) NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(enumerator)
);

INSERT INTO account_type (enumerator) VALUES
('CUSTOMER'),
('PIGGY_BANK'),
('BANK'),
('OUTSIDE_WORLD');

CREATE TABLE account_status(
    id                              SERIAL PRIMARY KEY,
    enumerator                      VARCHAR(50) NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(enumerator)
);

INSERT INTO account_status (enumerator) VALUES
('ACTIVE'),
('BLOCKED'),
('CLOSED');

CREATE TABLE block_reason(
    id                              SERIAL PRIMARY KEY,
    enumerator                      VARCHAR(50) NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(enumerator)
);

INSERT INTO block_reason (enumerator) VALUES
('SUSPICIOUS_ACTIVITY'),
('JUDICIAL_ORDER'),
('CUSTOMER_REQUEST'),
('MANUAL_REVIEW');

CREATE TABLE transaction_type(
    id                              SERIAL PRIMARY KEY,
    enumerator                      VARCHAR(50) NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(enumerator)
);

INSERT INTO transaction_type (enumerator) VALUES
('DEPOSIT'),
('WITHDRAWAL'),
('TRANSFER'),
('SAVE'),
('REDEEM'),
('YIELD');

CREATE TABLE entry_type(
    id                              SERIAL PRIMARY KEY,
    enumerator                      VARCHAR(50) NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(enumerator)
);

INSERT INTO entry_type (enumerator) VALUES
('AMOUNT'),
('FEE'),
('PRIZE'),
('YIELD'),
('IOF'),
('IR');

CREATE TABLE category_status(
    id                              SERIAL PRIMARY KEY,
    enumerator                      VARCHAR(50) NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(enumerator)
);

INSERT INTO category_status (enumerator) VALUES
('ACTIVE'),
('DELETED');

CREATE TABLE piggy_rank(
    id                              SERIAL PRIMARY KEY,
    enumerator                      VARCHAR(50) NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(enumerator)
);

INSERT INTO piggy_rank (enumerator) VALUES
('DEFAULT'),
('BRONZE'),
('SILVER'),
('GOLD'),
('PLATINUM'),
('DIAMOND');

-- ============================================================
-- Quem: cliente
-- ============================================================

CREATE TABLE customer(
    id                              SERIAL PRIMARY KEY,
    customer_key                    CHAR(36) NOT NULL,
    name                            VARCHAR(255) NOT NULL,
    document_number                 CHAR(14) NOT NULL,
    email                           VARCHAR(255) NOT NULL,
    birthdate                       DATE NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(customer_key),
    UNIQUE(document_number),
    UNIQUE(email)
);

-- ============================================================
-- Soltas: relogio do banco e registro de requisicoes
-- ============================================================

-- DIA-01: uma linha so, com o hoje do banco. DIA-04: comeca em 2026-06-01.
CREATE TABLE bank_clock(
    id                              SERIAL PRIMARY KEY,
    bank_clock_key                  CHAR(36) NOT NULL,
    accounting_date                 DATE NOT NULL,
    updated_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(bank_clock_key),
    CHECK (id = 1)
);

INSERT INTO bank_clock (bank_clock_key, accounting_date) VALUES
(gen_random_uuid()::text, '2026-06-01');

-- PRD-06, PRD-14: uma linha por requisicao, gravada fora da transacao da
-- regra. Sem chave estrangeira de proposito. Nunca guarda CPF, CNPJ,
-- token nem corpo (PRD-12).
CREATE TABLE request_log(
    id                              SERIAL PRIMARY KEY,
    request_log_key                 CHAR(36) NOT NULL,
    request_id                      VARCHAR(64) NOT NULL,
    method                          VARCHAR NOT NULL,
    path                            VARCHAR NOT NULL,
    status                          INTEGER NOT NULL,
    error_code                      VARCHAR(20),
    client_ip                       VARCHAR(45),
    account_key                     VARCHAR,
    auth_failure                    VARCHAR(20),
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(request_log_key),
    CHECK (auth_failure IN ('INTERNAL', 'ADMIN', 'ACCOUNT'))
);

-- PRD-10: a barreira conta falhas de token por IP e por conta + IP.
CREATE INDEX request_log_client_ip_created_at_idx
    ON request_log (client_ip, created_at);

CREATE INDEX request_log_account_key_client_ip_created_at_idx
    ON request_log (account_key, client_ip, created_at);

-- ============================================================
-- Quem: conta (de cliente, cofrinho, do banco e mundo de fora)
-- ============================================================

-- Conta de cliente: customer_id preenchido, balance e token_hash preenchidos.
-- Cofrinho (COF-14): customer_id e parent_account_id preenchidos, balance
-- preenchido, token_hash nulo.
-- Contas do sistema (DAD-09): customer_id, parent_account_id, balance e
-- token_hash nulos; o saldo delas e a soma dos lancamentos.
-- Gamificacao (DAD-14, GAM-01): valores atuais nas colunas da conta de cliente.
CREATE TABLE account(
    id                              SERIAL PRIMARY KEY,
    account_key                     CHAR(36) NOT NULL,
    account_type_id                 INTEGER NOT NULL REFERENCES account_type(id),
    status_id                       INTEGER NOT NULL REFERENCES account_status(id),
    customer_id                     INTEGER REFERENCES customer(id),
    parent_account_id               INTEGER REFERENCES account(id),
    balance                         BIGINT,
    token_hash                      CHAR(64),
    xp                              BIGINT NOT NULL DEFAULT(0),
    level                           INTEGER NOT NULL DEFAULT(0),
    points_free                     INTEGER NOT NULL DEFAULT(0),
    points_fee                      INTEGER NOT NULL DEFAULT(0),
    points_chance                   INTEGER NOT NULL DEFAULT(0),
    rank_id                         INTEGER REFERENCES piggy_rank(id),
    yield_rank_id                   INTEGER REFERENCES piggy_rank(id),
    piggy_record                    BIGINT NOT NULL DEFAULT(0),
    grace_until                     DATE,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(account_key),
    UNIQUE(parent_account_id),
    CHECK (balance >= 0),
    CHECK (xp >= 0),
    CHECK (level >= 0),
    CHECK (points_free >= 0),
    CHECK (points_fee >= 0),
    CHECK (points_chance >= 0),
    CHECK (piggy_record >= 0)
);

-- CLI-04: uma conta nao encerrada por cliente.
-- account_type CUSTOMER = 1; account_status CLOSED = 3.
CREATE UNIQUE INDEX account_one_open_per_customer_idx
    ON account (customer_id)
    WHERE account_type_id = 1 AND status_id <> 3;

-- DAD-09: a conta do banco e a conta mundo de fora.
INSERT INTO account (account_key, account_type_id, status_id) VALUES
(
    gen_random_uuid()::text,
    (SELECT id FROM account_type WHERE enumerator = 'BANK'),
    (SELECT id FROM account_status WHERE enumerator = 'ACTIVE')
),
(
    gen_random_uuid()::text,
    (SELECT id FROM account_type WHERE enumerator = 'OUTSIDE_WORLD'),
    (SELECT id FROM account_status WHERE enumerator = 'ACTIVE')
);

-- CLI-05, CLI-08, R4: historico do estado da conta.
-- block_reason_id so no bloqueio; source: MANUAL (rota interna) ou
-- AUTOMATIC (bloqueio automatico).
CREATE TABLE account_status_event(
    id                              SERIAL PRIMARY KEY,
    account_id                      INTEGER NOT NULL REFERENCES account(id),
    status_id                       INTEGER NOT NULL REFERENCES account_status(id),
    block_reason_id                 INTEGER REFERENCES block_reason(id),
    source                          VARCHAR(20),
    event_datetime                  TIMESTAMP NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(clock_timestamp()),
    CHECK (source IN ('MANUAL', 'AUTOMATIC'))
);

-- ============================================================
-- Dinheiro: operacao, deposito e lancamento
-- ============================================================

-- DAD-06, DAD-17, MOV-12, MOV-19: uma linha por pedido.
-- request_control_key e request_hash nulos so no rendimento (YIELD).
CREATE TABLE transaction(
    id                              SERIAL PRIMARY KEY,
    transaction_key                 CHAR(36) NOT NULL,
    transaction_type_id             INTEGER NOT NULL REFERENCES transaction_type(id),
    request_control_key             CHAR(36),
    request_hash                    CHAR(64),
    accounting_date                 DATE NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(clock_timestamp()),
    UNIQUE(transaction_key),
    UNIQUE(request_control_key)
);

-- MOV-15, MOV-16: quem depositou. CPF (14) ou CNPJ (18) formatado.
CREATE TABLE deposits(
    id                              SERIAL PRIMARY KEY,
    deposit_key                     CHAR(36) NOT NULL,
    transaction_id                  INTEGER NOT NULL REFERENCES transaction(id),
    depositor_name                  VARCHAR(255) NOT NULL,
    depositor_document              VARCHAR(18) NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(deposit_key),
    UNIQUE(transaction_id)
);

-- ============================================================
-- Cofrinho: categorias
-- ============================================================

-- COF-03, COF-14: account_id e o cofrinho. is_default marca economias.
CREATE TABLE category(
    id                              SERIAL PRIMARY KEY,
    category_key                    CHAR(36) NOT NULL,
    account_id                      INTEGER NOT NULL REFERENCES account(id),
    status_id                       INTEGER NOT NULL REFERENCES category_status(id),
    name                            VARCHAR(255) NOT NULL,
    is_default                      BOOLEAN NOT NULL DEFAULT(FALSE),
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(category_key)
);

-- COF-18: nome unico entre as categorias ativas do cofrinho.
-- category_status ACTIVE = 1.
CREATE UNIQUE INDEX category_active_name_idx
    ON category (account_id, name)
    WHERE status_id = 1;

-- COF-03: uma categoria padrao por cofrinho.
CREATE UNIQUE INDEX category_one_default_idx
    ON category (account_id)
    WHERE is_default;

-- API-15, R4: historico do estado da categoria.
CREATE TABLE category_status_event(
    id                              SERIAL PRIMARY KEY,
    category_id                     INTEGER NOT NULL REFERENCES category(id),
    status_id                       INTEGER NOT NULL REFERENCES category_status(id),
    event_datetime                  TIMESTAMP NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW())
);

-- DAD-05, DAD-16, MOV-19: uma linha por conta afetada; a soma da operacao
-- e zero. category_id so nos lancamentos do cofrinho. balance_after nulo
-- nas contas do sistema.
CREATE TABLE entry(
    id                              SERIAL PRIMARY KEY,
    entry_key                       CHAR(36) NOT NULL,
    transaction_id                  INTEGER NOT NULL REFERENCES transaction(id),
    account_id                      INTEGER NOT NULL REFERENCES account(id),
    entry_type_id                   INTEGER NOT NULL REFERENCES entry_type(id),
    category_id                     INTEGER REFERENCES category(id),
    amount                          BIGINT NOT NULL,
    balance_after                   BIGINT,
    created_at                      TIMESTAMP NOT NULL DEFAULT(clock_timestamp()),
    UNIQUE(entry_key),
    CHECK (amount <> 0),
    CHECK (balance_after >= 0)
);

-- MOV-14: extrato da conta, mais recente primeiro, desempate por id.
CREATE INDEX entry_account_created_at_id_idx
    ON entry (account_id, created_at DESC, id DESC);

-- ============================================================
-- Cofrinho: lotes
-- ============================================================

-- COF-06, COF-13, COF-15, COF-23: um lote por guardar.
-- residue: fracao de centavo do rendimento, 8 casas.
CREATE TABLE lot(
    id                              SERIAL PRIMARY KEY,
    lot_key                         CHAR(36) NOT NULL,
    category_id                     INTEGER NOT NULL REFERENCES category(id),
    transaction_id                  INTEGER NOT NULL REFERENCES transaction(id),
    accounting_date                 DATE NOT NULL,
    principal_remaining             BIGINT NOT NULL,
    yield_remaining                 BIGINT NOT NULL DEFAULT(0),
    residue                         NUMERIC(9, 8) NOT NULL DEFAULT(0),
    created_at                      TIMESTAMP NOT NULL DEFAULT(clock_timestamp()),
    UNIQUE(lot_key),
    CHECK (principal_remaining >= 0),
    CHECK (yield_remaining >= 0),
    CHECK (residue >= 0 AND residue < 1)
);

-- ============================================================
-- Gamificacao: eventos (DAD-14)
-- ============================================================

-- GAM-04, GAM-16, GAM-17, GAM-19: transaction_id nulo no XP da virada.
CREATE TABLE xp_event(
    id                              SERIAL PRIMARY KEY,
    xp_event_key                    CHAR(36) NOT NULL,
    account_id                      INTEGER NOT NULL REFERENCES account(id),
    transaction_id                  INTEGER REFERENCES transaction(id),
    source                          VARCHAR(20) NOT NULL,
    xp                              BIGINT NOT NULL,
    accounting_date                 DATE NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(xp_event_key),
    CHECK (source IN ('TRANSFER_SENT', 'TRANSFER_RECEIVED', 'PIGGY_RECORD')),
    CHECK (xp >= 0)
);

-- GAM-05, GAM-06, GAM-15: nivel alcancado (cada um vale 1 ponto livre).
CREATE TABLE level_event(
    id                              SERIAL PRIMARY KEY,
    level_event_key                 CHAR(36) NOT NULL,
    account_id                      INTEGER NOT NULL REFERENCES account(id),
    level                           INTEGER NOT NULL,
    accounting_date                 DATE NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(level_event_key),
    CHECK (level >= 1)
);

-- GAM-12, GAM-14, GAM-19: subiu, abriu carencia, saiu da carencia, caiu.
CREATE TABLE rank_event(
    id                              SERIAL PRIMARY KEY,
    rank_event_key                  CHAR(36) NOT NULL,
    account_id                      INTEGER NOT NULL REFERENCES account(id),
    rank_id                         INTEGER NOT NULL REFERENCES piggy_rank(id),
    kind                            VARCHAR(20) NOT NULL,
    accounting_date                 DATE NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(rank_event_key),
    CHECK (kind IN ('UP', 'GRACE_START', 'GRACE_END', 'DOWN'))
);

-- GAM-07, GAM-21: aplicar +Y pontos num beneficio, ou zerar tudo.
-- benefit nulo no RESET.
CREATE TABLE points_event(
    id                              SERIAL PRIMARY KEY,
    points_event_key                CHAR(36) NOT NULL,
    account_id                      INTEGER NOT NULL REFERENCES account(id),
    action                          VARCHAR(10) NOT NULL,
    benefit                         VARCHAR(10),
    points                          INTEGER NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(points_event_key),
    CHECK (action IN ('APPLY', 'RESET')),
    CHECK (benefit IN ('FEE', 'CHANCE')),
    CHECK ((action = 'APPLY' AND benefit IS NOT NULL) OR (action = 'RESET' AND benefit IS NULL)),
    CHECK (points >= 0)
);
