from datetime import date, timedelta
from app import prazos


def test_drogas_preso_30_dias():
    r = prazos.calcula_prazo("drogas", "preso", "2026-02-01", hoje="2026-02-01")
    assert r["dias_total"] == 30
    assert r["data_limite"] == "2026-03-03"   # 01/02 + 30 dias
    assert r["dias_restantes"] == 30
    assert not r["vencido"]


def test_drogas_solto_90_dias():
    r = prazos.calcula_prazo("drogas", "solto", "2026-02-01", hoje="2026-02-01")
    assert r["dias_total"] == 90


def test_drogas_preso_prorrogado_dobra_para_60():
    r = prazos.calcula_prazo("drogas", "preso", "2026-02-01", prorrogado=True,
                             hoje="2026-02-01")
    assert r["dias_total"] == 60


def test_drogas_solto_prorrogado_dobra_para_180():
    r = prazos.calcula_prazo("drogas", "solto", "2026-02-01", prorrogado=True,
                             hoje="2026-02-01")
    assert r["dias_total"] == 180


def test_cpp_preso_10_solto_30():
    assert prazos.calcula_prazo("cpp", "preso", "2026-02-01",
                                hoje="2026-02-01")["dias_total"] == 10
    assert prazos.calcula_prazo("cpp", "solto", "2026-02-01",
                                hoje="2026-02-01")["dias_total"] == 30


def test_semaforo_vencido():
    r = prazos.calcula_prazo("drogas", "preso", "2026-02-01", hoje="2026-04-01")
    assert r["vencido"]
    assert r["cor"] == "vermelho"
    assert r["dias_restantes"] < 0


def test_semaforo_vermelho_amarelo_verde():
    # preso drogas = 30 dias a partir de 01/02 -> limite 03/03
    assert prazos.calcula_prazo("drogas", "preso", "2026-02-01",
                                hoje="2026-03-01")["cor"] == "vermelho"  # 2 dias
    assert prazos.calcula_prazo("drogas", "preso", "2026-02-01",
                                hoje="2026-02-20")["cor"] == "amarelo"   # 11 dias
    assert prazos.calcula_prazo("drogas", "preso", "2026-02-01",
                                hoje="2026-02-05")["cor"] == "verde"     # 26 dias


def test_combinacao_invalida():
    import pytest
    with pytest.raises(ValueError):
        prazos.calcula_prazo("inexistente", "preso", "2026-02-01")
