import pytest
from fastapi.testclient import TestClient

from app import api
from conftest import HOJE


@pytest.fixture
def cliente(banco):
    # injeta a conexao de teste no lugar da conexao via env var
    api.app.dependency_overrides[api.get_con] = lambda: banco
    yield TestClient(api.app)
    api.app.dependency_overrides.clear()


def test_painel(cliente):
    r = cliente.get("/api/painel", params={"hoje": HOJE})
    assert r.status_code == 200
    assert r.json()["contadores"]["casos"] == 1


def test_casos(cliente):
    r = cliente.get("/api/casos", params={"hoje": HOJE})
    assert r.status_code == 200
    assert r.json()[0]["nome"] == "Operacao Patagonia"


def test_detalhe(cliente):
    r = cliente.get("/api/casos/1", params={"hoje": HOJE})
    assert r.status_code == 200
    assert len(r.json()["inqueritos"]) == 1


def test_detalhe_404(cliente):
    assert cliente.get("/api/casos/999", params={"hoje": HOJE}).status_code == 404


def test_conferencia(cliente):
    r = cliente.get("/api/conferencia")
    assert r.status_code == 200
    assert len(r.json()["inqueritos"]) == 1


def test_busca(cliente):
    r = cliente.get("/api/busca", params={"q": "Patagonia"})
    assert r.status_code == 200
    assert len(r.json()["casos"]) == 1
