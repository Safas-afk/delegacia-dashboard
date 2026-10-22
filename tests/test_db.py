import pytest
from app import db


def test_cria_e_le_banco_cifrado(tmp_path):
    caminho = str(tmp_path / "teste.db")
    con = db.conectar(caminho, "senha-forte-123")
    db.inicializa(con)
    con.execute("INSERT INTO caso (nome, data_abertura) VALUES (?,?)",
                ("Operacao Teste", "2026-02-01"))
    con.commit()
    con.close()

    # reabre com a senha certa: le de volta
    con2 = db.conectar(caminho, "senha-forte-123")
    nome = con2.execute("SELECT nome FROM caso").fetchone()["nome"]
    assert nome == "Operacao Teste"
    con2.close()


def test_senha_errada_falha(tmp_path):
    caminho = str(tmp_path / "teste.db")
    con = db.conectar(caminho, "senha-certa")
    db.inicializa(con)
    con.close()

    with pytest.raises(Exception):
        db.conectar(caminho, "senha-errada")


def test_arquivo_nao_e_texto_plano(tmp_path):
    # o arquivo no disco nao pode conter o conteudo legivel (esta cifrado)
    caminho = str(tmp_path / "teste.db")
    con = db.conectar(caminho, "chave")
    db.inicializa(con)
    con.execute("INSERT INTO caso (nome) VALUES ('SEGREDO_VISIVEL')")
    con.commit()
    con.close()

    with open(caminho, "rb") as f:
        bruto = f.read()
    assert b"SEGREDO_VISIVEL" not in bruto
    assert b"SQLite format 3" not in bruto[:16]   # cabecalho tambem cifrado
