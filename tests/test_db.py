from app import db


def test_cria_e_le_banco(tmp_path):
    caminho = str(tmp_path / "teste.db")
    con = db.conectar(caminho)
    db.inicializa(con)
    con.execute("INSERT INTO caso (nome, data_abertura) VALUES (?,?)",
                ("Operacao Teste", "2026-02-01"))
    con.commit()
    con.close()

    # reabre: le de volta
    con2 = db.conectar(caminho)
    nome = con2.execute("SELECT nome FROM caso").fetchone()["nome"]
    assert nome == "Operacao Teste"
    con2.close()


def test_foreign_keys_ligado(tmp_path):
    con = db.conectar(str(tmp_path / "teste.db"))
    assert con.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    con.close()
