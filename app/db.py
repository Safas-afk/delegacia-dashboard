"""Conexao com o banco SQLite (arquivo local) e criacao do esquema.

Decisao do delegado (2026-10-23): sem senha e sem cifra. O PC fica em sala com
camera e so liga com o login dele; o modelo de ameaca assumido e "sem acesso
fisico de terceiros". Arquivo SQLite comum.
"""
import os
import sqlite3

SCHEMA = os.path.join(os.path.dirname(__file__), "schema.sql")


def conectar(caminho, check_same_thread=True):
    """Abre (ou cria) o banco.
    check_same_thread=False so nos testes (conexao compartilhada entre threads
    pelo TestClient); em producao e uma conexao por requisicao, na propria thread.
    """
    con = sqlite3.connect(caminho, check_same_thread=check_same_thread)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def inicializa(con):
    """Cria as tabelas (idempotente)."""
    with open(SCHEMA, encoding="utf-8") as f:
        con.executescript(f.read())
    con.commit()


def registra_auditoria(con, usuario, acao, detalhe=""):
    con.execute("INSERT INTO auditoria (usuario, acao, detalhe) VALUES (?,?,?)",
                (usuario, acao, detalhe))
    con.commit()
