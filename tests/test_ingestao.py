import pytest
from app import db, ingestao

# JSON como o Qwen devolveria para o PDF ficticio (sem rodar o modelo)
EXTRACAO = {
    "numero_ip": "2026.0101.000457-3",
    "nome_operacao": "Operacao Patagonia",
    "delegado_responsavel": "Mariana Teixeira de Almeida",
    "segredo_de_justica": True,
    "data_do_fato": "2026-02-14",
    "data_instauracao": "2026-02-15",
    "situacao_prisional": "preso",
    "resumo": "Apreensao de drogas e arma.",
    "tipificacoes": ["art. 33 da Lei n. 11.343/2006",
                     "art. 16 da Lei n. 10.826/2003",
                     "art. 35 da Lei n. 11.343/2006"],
    "pessoas": [
        {"nome": "Jose Carlos dos Santos Pereira", "papel": "preso", "situacao": "preso"},
        {"nome": "Maria Eduarda Lima Souza", "papel": "investigado", "situacao": "foragido"},
    ],
}


@pytest.fixture
def con(tmp_path):
    c = db.conectar(str(tmp_path / "t.db"), "chave")
    db.inicializa(c)
    yield c
    c.close()


def test_mapeia_tipificacoes():
    cods = ingestao.mapeia_tipificacoes(EXTRACAO["tipificacoes"])
    assert cods == ["LD_33", "ED_16", "LD_35"]


def test_mapeia_desambigua_pela_lei():
    # art. 12 existe no Estatuto (ED_12); nao deve casar com nada da Lei de Drogas
    assert ingestao.mapeia_tipificacoes(["art. 12 da Lei 10.826/2003"]) == ["ED_12"]


def test_grava_cria_tudo_como_proposta(con):
    r = ingestao.grava(con, EXTRACAO, nome_arquivo="doc.pdf")
    assert r["novo"] is True

    inq = con.execute("SELECT * FROM inquerito WHERE id=?", (r["inquerito_id"],)).fetchone()
    assert inq["numero_oficial"] == "2026.0101.000457-3"
    assert inq["situacao_prisional"] == "preso"
    assert inq["lei_prazo"] == "drogas"        # tem droga -> prazo da Lei de Drogas
    assert inq["conferido"] == 0               # nada vira fato

    crimes = con.execute("SELECT tipificacao_codigo, conferido FROM crime WHERE inquerito_id=?",
                         (r["inquerito_id"],)).fetchall()
    assert {c["tipificacao_codigo"] for c in crimes} == {"LD_33", "ED_16", "LD_35"}
    assert all(c["conferido"] == 0 for c in crimes)

    pessoas = con.execute("SELECT nome FROM pessoa WHERE inquerito_id=?",
                          (r["inquerito_id"],)).fetchall()
    assert len(pessoas) == 2

    doc = con.execute("SELECT * FROM documento WHERE inquerito_id=?",
                      (r["inquerito_id"],)).fetchone()
    assert doc["extracao_json"] is not None     # extracao crua guardada p/ conferencia


def test_segundo_pdf_mesmo_ip_nao_duplica(con):
    r1 = ingestao.grava(con, EXTRACAO, nome_arquivo="doc1.pdf")
    r2 = ingestao.grava(con, EXTRACAO, nome_arquivo="doc2.pdf")
    assert r2["novo"] is False
    assert r2["inquerito_id"] == r1["inquerito_id"]

    assert con.execute("SELECT count(*) c FROM inquerito").fetchone()["c"] == 1
    assert con.execute("SELECT count(*) c FROM caso").fetchone()["c"] == 1
    assert con.execute("SELECT count(*) c FROM crime").fetchone()["c"] == 3   # sem duplicar
    assert con.execute("SELECT count(*) c FROM pessoa").fetchone()["c"] == 2
    assert con.execute("SELECT count(*) c FROM documento").fetchone()["c"] == 2  # 2 PDFs


def test_nao_sobrescreve_inquerito_conferido(con):
    r = ingestao.grava(con, EXTRACAO, nome_arquivo="doc.pdf")
    # delegado confere e corrige a situacao
    con.execute("UPDATE inquerito SET conferido=1, situacao_prisional='solto' WHERE id=?",
                (r["inquerito_id"],))
    con.commit()
    # novo PDF do mesmo IP nao pode reverter o campo conferido
    ingestao.grava(con, EXTRACAO, nome_arquivo="doc2.pdf")
    inq = con.execute("SELECT situacao_prisional FROM inquerito WHERE id=?",
                      (r["inquerito_id"],)).fetchone()
    assert inq["situacao_prisional"] == "solto"


def test_completa_campo_vazio_se_nao_conferido(con):
    parcial = dict(EXTRACAO, delegado_responsavel=None)
    r = ingestao.grava(con, parcial, nome_arquivo="doc1.pdf")
    # segundo doc traz o delegado -> preenche o campo que estava vazio
    ingestao.grava(con, EXTRACAO, nome_arquivo="doc2.pdf")
    inq = con.execute("SELECT delegado_responsavel FROM inquerito WHERE id=?",
                      (r["inquerito_id"],)).fetchone()
    assert inq["delegado_responsavel"] == "Mariana Teixeira de Almeida"
