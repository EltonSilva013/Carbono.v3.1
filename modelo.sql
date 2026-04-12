-- Tabela de usuários
CREATE TABLE usuarios (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tipos de atividades de carbono
CREATE TABLE atividades (
    id_atividade INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    fator_emissao REAL NOT NULL
);

-- Registros de consumo de carbono
CREATE TABLE registros_carbono (
    id_registro INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL,
    id_atividade INTEGER NOT NULL,
    quantidade REAL NOT NULL,
    emissao_total REAL,
    data_registro DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
    FOREIGN KEY (id_atividade) REFERENCES atividades(id_atividade)
);
