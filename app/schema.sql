-- Esquema do banco (SQLCipher). Modelo: caso -> inquerito -> crimes/pessoas/documentos/pendencias.
-- Datas em texto ISO (YYYY-MM-DD). Prazos sao CALCULADOS a partir dos campos, nao digitados.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS caso (
    id              INTEGER PRIMARY KEY,
    nome            TEXT NOT NULL,              -- apelido da operacao/ocorrencia
    data_abertura   TEXT,                       -- YYYY-MM-DD
    origem          TEXT,                       -- denuncia, flagrante, mandado...
    status          TEXT DEFAULT 'em_andamento',
    resumo          TEXT,
    segredo_justica INTEGER DEFAULT 0,          -- 0/1
    criado_em       TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS inquerito (
    id                  INTEGER PRIMARY KEY,
    caso_id             INTEGER NOT NULL REFERENCES caso(id) ON DELETE CASCADE,
    numero_oficial      TEXT,                   -- numero do IP
    delegado_responsavel TEXT,
    data_instauracao    TEXT,                   -- YYYY-MM-DD (dispara o prazo)
    situacao_prisional  TEXT DEFAULT 'solto',   -- 'preso' | 'solto'
    lei_prazo           TEXT DEFAULT 'drogas',  -- 'drogas' (11.343) | 'cpp'
    prorrogado          INTEGER DEFAULT 0,      -- 0/1 (juiz autorizou duplicar)
    data_prorrogacao    TEXT,
    status              TEXT DEFAULT 'em_andamento', -- em_andamento|relatado|arquivado|na_justica
    criado_em           TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS crime (
    id                 INTEGER PRIMARY KEY,
    inquerito_id       INTEGER NOT NULL REFERENCES inquerito(id) ON DELETE CASCADE,
    tipificacao_codigo TEXT,                    -- FK logica para o catalogo (catalogo.py)
    descricao          TEXT,
    data_fato          TEXT
);

CREATE TABLE IF NOT EXISTS pessoa (
    id           INTEGER PRIMARY KEY,
    inquerito_id INTEGER NOT NULL REFERENCES inquerito(id) ON DELETE CASCADE,
    nome         TEXT NOT NULL,
    papel        TEXT,                           -- investigado|preso|testemunha|vitima|condutor
    situacao     TEXT                            -- preso|foragido|solto...
);

CREATE TABLE IF NOT EXISTS documento (
    id             INTEGER PRIMARY KEY,
    inquerito_id   INTEGER REFERENCES inquerito(id) ON DELETE CASCADE,
    caso_id        INTEGER REFERENCES caso(id) ON DELETE CASCADE,
    nome_arquivo   TEXT NOT NULL,
    caminho        TEXT,                          -- caminho na pasta vigiada
    tipo           TEXT,                          -- auto_prisao|laudo_constatacao|laudo_definitivo|comunicacao_mp|portaria|oficio...
    data           TEXT,
    hash           TEXT,                          -- detecta alteracao
    texto_extraido TEXT,                          -- markdown (fica no banco cifrado)
    status_extracao TEXT DEFAULT 'pendente',      -- pendente|processado|conferido
    criado_em      TEXT DEFAULT (datetime('now'))
);

-- Prazos avulsos (laudo, resposta de oficio etc). O prazo PRINCIPAL do IP e calculado.
CREATE TABLE IF NOT EXISTS prazo (
    id           INTEGER PRIMARY KEY,
    inquerito_id INTEGER NOT NULL REFERENCES inquerito(id) ON DELETE CASCADE,
    tipo         TEXT,
    data_limite  TEXT,
    observacao   TEXT
);

CREATE TABLE IF NOT EXISTS pendencia (
    id           INTEGER PRIMARY KEY,
    inquerito_id INTEGER NOT NULL REFERENCES inquerito(id) ON DELETE CASCADE,
    descricao    TEXT NOT NULL,
    categoria    TEXT,                           -- prazo|laudo|comunicacao|disciplinar...
    severidade   TEXT DEFAULT 'media',           -- baixa|media|alta|critica
    origem       TEXT DEFAULT 'regra',           -- regra|manual
    aberta       INTEGER DEFAULT 1,
    criado_em    TEXT DEFAULT (datetime('now')),
    resolvido_em TEXT
);

-- Trilha de auditoria (LGPD/boas praticas: quem fez o que e quando).
CREATE TABLE IF NOT EXISTS auditoria (
    id       INTEGER PRIMARY KEY,
    quando   TEXT DEFAULT (datetime('now')),
    usuario  TEXT,
    acao     TEXT,
    detalhe  TEXT
);

CREATE INDEX IF NOT EXISTS idx_inq_caso ON inquerito(caso_id);
CREATE INDEX IF NOT EXISTS idx_crime_inq ON crime(inquerito_id);
CREATE INDEX IF NOT EXISTS idx_doc_inq ON documento(inquerito_id);
CREATE INDEX IF NOT EXISTS idx_pend_inq ON pendencia(inquerito_id);
