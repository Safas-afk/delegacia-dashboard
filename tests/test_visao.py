from app import visao, prazos
from conftest import HOJE


def test_inquerito_view_junta_tudo(banco):
    inq = banco.execute("SELECT * FROM inquerito").fetchone()
    v = visao.inquerito_view(banco, inq, hoje=HOJE)

    # prazo calculado bate com o motor
    esperado = prazos.calcula_prazo("drogas", "preso", "2026-02-15", False, hoje=HOJE)
    assert v["prazo"] == esperado

    # crimes carregam o catalogo
    assert len(v["crimes"]) == 3
    trafico = next(c for c in v["crimes"] if c["tipificacao_codigo"] == "LD_33")
    assert trafico["catalogo"]["artigo"] == "art. 33"

    assert len(v["pessoas"]) == 1
    assert len(v["documentos"]) == 1
    # documento leve nao traz os campos pesados
    assert "texto_extraido" not in v["documentos"][0]


def test_pendencias_ordenadas_por_severidade(banco):
    inq = banco.execute("SELECT * FROM inquerito").fetchone()
    v = visao.inquerito_view(banco, inq, hoje=HOJE)
    cats = {p["categoria"] for p in v["pendencias"]}
    # sem comunicacao ao MP e sem laudo definitivo (so a portaria consta)
    assert "comunicacao" in cats
    assert "laudo" in cats
    sev = [p["severidade"] for p in v["pendencias"]]
    assert sev == sorted(sev, key=lambda s: visao.SEV_ORDEM[s])


def test_detalhe_caso(banco):
    caso = visao.detalhe_caso(banco, 1, hoje=HOJE)
    assert caso["nome"] == "Operacao Patagonia"
    assert len(caso["inqueritos"]) == 1
    assert caso["inqueritos"][0]["prazo"]["cor"] in ("verde", "amarelo", "vermelho")


def test_detalhe_caso_inexistente(banco):
    assert visao.detalhe_caso(banco, 999, hoje=HOJE) is None


def test_lista_casos(banco):
    lst = visao.lista_casos(banco, hoje=HOJE)
    assert len(lst) == 1
    c = lst[0]
    assert c["nome"] == "Operacao Patagonia"
    assert c["qtd_inqueritos"] == 1
    assert c["prazo"] is not None
    assert c["qtd_pendencias"] >= 2


def test_painel(banco):
    p = visao.painel(banco, hoje=HOJE)
    assert p["contadores"]["casos"] == 1
    assert p["contadores"]["inqueritos"] == 1
    assert p["contadores"]["nao_conferidos"] == 1
    assert sum(p["semaforo"].values()) == 1
    # alertas so trazem critica/alta
    assert all(a["severidade"] in ("critica", "alta") for a in p["alertas"])
    assert any(a["categoria"] == "laudo" for a in p["alertas"])


def test_itens_conferencia(banco):
    c = visao.itens_conferencia(banco)
    # inquerito foi inserido com conferido=0
    assert len(c["inqueritos"]) == 1


def test_busca(banco):
    assert len(visao.busca(banco, "Patagonia")["casos"]) == 1
    assert len(visao.busca(banco, "000457")["inqueritos"]) == 1
    assert len(visao.busca(banco, "Jose")["pessoas"]) == 1
    assert visao.busca(banco, "naoexiste")["casos"] == []
