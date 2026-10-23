"""Conexao com o banco SQLCipher (cifrado em repouso) e criacao do esquema.
A chave vem da senha do delegado; sem ela o arquivo e ilegivel.
"""
import os
from sqlcipher3 import dbapi2 as sqlcipher

SCHEMA = os.path.join(os.path.dirname(__file__), "schema.sql")


def conectar(caminho, senha, check_same_thread=True):
    """Abre (ou cria) o banco cifrado. PRAGMA key tem que vir antes de tudo.
    check_same_thread=False so nos testes (conexao compartilhada entre threads
    pelo TestClient); em producao e uma conexao por requisicao, na propria thread.
    """
    con = sqlcipher.connect(caminho, check_same_thread=check_same_thread)
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
