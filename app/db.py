"""Conexao com o banco SQLCipher (cifrado em repouso) e criacao do esquema.
A chave vem da senha do delegado; sem ela o arquivo e ilegivel.
"""
import os
from sqlcipher3 import dbapi2 as sqlcipher

SCHEMA = os.path.join(os.path.dirname(__file__), "schema.sql")


def conectar(caminho, senha):
    """Abre (ou cria) o banco cifrado. PRAGMA key tem que vir antes de tudo."""
    con = sqlcipher.connect(caminho)
    con.row_factory = sqlcipher.Row
    # escapa aspas simples na senha antes de passar pro PRAGMA
    senha_sql = senha.replace("'", "''")
    con.execute(f"PRAGMA key = '{senha_sql}'")
    con.execute("PRAGMA foreign_keys = ON")
    # valida a senha: se errada, esta leitura falha
    con.execute("SELECT count(*) FROM sqlite_master")
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
