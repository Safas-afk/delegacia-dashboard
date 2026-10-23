import pytest
from app import conferencia


def _inq(banco):
    return banco.execute("SELECT * FROM inquerito").fetchone()


def test_aprovar_marca_conferido(banco):
    inq = _inq(banco)
    assert inq["conferido"] == 0
    ok = conferencia.salvar(banco, "inquerito", inq["id"], {})
    assert ok is True
    assert _inq(banco)["conferido"] == 1


def test_corrigir_muda_campo(banco):
    inq = _inq(banco)
    conferencia.salvar(banco, "inquerito", inq["id"],
                       {"situacao_prisional": "solto"})
    novo = _inq(banco)
    assert novo["situacao_prisional"] == "solto"
    assert novo["conferido"] == 1


def test_whitelist_ignora_coluna_fora(banco):
    inq = _inq(banco)
    caso_antes = inq["caso_id"]
    # caso_id nao esta na whitelist: deve ser ignorado
    conferencia.salvar(banco, "inquerito", inq["id"], {"caso_id": 999})
    assert _inq(banco)["caso_id"] == caso_antes


def test_crime_tipificacao_puxa_descricao(banco):
    crime = banco.execute("SELECT * FROM crime ORDER BY id").fetchone()
    conferencia.salvar(banco, "crime", crime["id"],
                       {"tipificacao_codigo": "LD_28"})
    novo = banco.execute("SELECT * FROM crime WHERE id=?", (crime["id"],)).fetchone()
    assert novo["tipificacao_codigo"] == "LD_28"
    assert novo["descricao"] == "Porte de droga para consumo pessoal"
    assert novo["conferido"] == 1


def test_rejeitar_apaga(banco):
    p = banco.execute("SELECT * FROM pessoa").fetchone()
    ok = conferencia.rejeitar(banco, "pessoa", p["id"])
    assert ok is True
    assert banco.execute("SELECT count(*) AS n FROM pessoa").fetchone()["n"] == 0


def test_item_inexistente(banco):
    assert conferencia.salvar(banco, "inquerito", 999, {}) is False
    assert conferencia.rejeitar(banco, "crime", 999) is False


def test_tipo_invalido(banco):
    with pytest.raises(ValueError):
        conferencia.salvar(banco, "documento", 1, {})
    with pytest.raises(ValueError):
        conferencia.rejeitar(banco, "caso", 1)


def test_auditoria_registrada(banco):
    inq = _inq(banco)
    conferencia.salvar(banco, "inquerito", inq["id"], {})
    acao = banco.execute(
        "SELECT acao FROM auditoria ORDER BY id DESC LIMIT 1").fetchone()["acao"]
    assert acao == "conferir_inquerito"
