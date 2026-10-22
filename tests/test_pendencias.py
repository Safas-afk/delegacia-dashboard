from app import pendencias

# inquerito de trafico, preso, recem instaurado
INQ_NOVO = {"data_instauracao": "2026-02-01", "situacao_prisional": "preso",
            "lei_prazo": "drogas", "prorrogado": 0, "status": "em_andamento"}
CRIMES_DROGA = [{"tipificacao_codigo": "LD_33"}, {"tipificacao_codigo": "ED_16"}]


def _categorias(pend):
    return {p["categoria"] for p in pend}


def test_recem_instaurado_pede_comunicacao_mp_e_laudo():
    # 1 dia depois: ainda dentro das 48h, sem docs
    pend = pendencias.avalia_inquerito(INQ_NOVO, CRIMES_DROGA, [], hoje="2026-02-02")
    cats = _categorias(pend)
    assert "comunicacao" in cats          # lembrar de comunicar MP
    assert "laudo" in cats                # falta laudo definitivo
    com = [p for p in pend if p["categoria"] == "comunicacao"][0]
    assert com["severidade"] == "media"   # ainda dentro do prazo de 48h


def test_passou_48h_sem_comunicar_mp_vira_alta():
    pend = pendencias.avalia_inquerito(INQ_NOVO, CRIMES_DROGA, [], hoje="2026-02-05")
    com = [p for p in pend if p["categoria"] == "comunicacao"][0]
    assert com["severidade"] == "alta"


def test_comunicacao_some_quando_ha_documento():
    docs = [{"tipo": "comunicacao_mp"}]
    pend = pendencias.avalia_inquerito(INQ_NOVO, CRIMES_DROGA, docs, hoje="2026-02-05")
    assert "comunicacao" not in _categorias(pend)


def test_laudo_some_com_laudo_definitivo():
    docs = [{"tipo": "laudo_definitivo"}]
    pend = pendencias.avalia_inquerito(INQ_NOVO, CRIMES_DROGA, docs, hoje="2026-02-05")
    assert "laudo" not in _categorias(pend)


def test_prazo_vencido_e_risco_disciplinar_apos_90_dias():
    # 100 dias depois: prazo (30d preso) vencido + 90 dias disciplinar
    pend = pendencias.avalia_inquerito(INQ_NOVO, CRIMES_DROGA, [], hoje="2026-05-12")
    cats = _categorias(pend)
    assert "prazo" in cats
    assert "disciplinar" in cats
    disc = [p for p in pend if p["categoria"] == "disciplinar"][0]
    assert disc["severidade"] == "critica"


def test_inquerito_arquivado_nao_gera_pendencia():
    inq = dict(INQ_NOVO, status="arquivado")
    pend = pendencias.avalia_inquerito(inq, CRIMES_DROGA, [], hoje="2026-05-12")
    assert pend == []


def test_crime_sem_droga_nao_pede_laudo():
    crimes = [{"tipificacao_codigo": "ED_16"}]   # so arma
    pend = pendencias.avalia_inquerito(INQ_NOVO, crimes, [], hoje="2026-02-05")
    assert "laudo" not in _categorias(pend)
