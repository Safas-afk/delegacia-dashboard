import os
import sys

import pytest

# garante que o pacote app seja importavel nos testes
sys.path.insert(0, os.path.dirname(__file__))

from app import db, catalogo  # noqa: E402

# dia simulado em que o delegado abre o sistema (igual seed_demo.py)
HOJE = "2026-03-12"


@pytest.fixture
def banco(tmp_path):
    """Banco cifrado com o cenario Operacao Patagonia (preso, drogas, 3 crimes,
    so a portaria: sem comunicacao ao MP e sem laudo definitivo). Mesmo cenario
    do seed_demo.py, reaproveitado pelos testes de visao e de API.
    """
    con = db.conectar(str(tmp_path / "teste.db"), "senha-forte-123",
                      check_same_thread=False)
    db.inicializa(con)

    caso_id = con.execute(
        "INSERT INTO caso (nome, data_abertura, origem, segredo_justica, resumo) "
        "VALUES (?,?,?,?,?)",
        ("Operacao Patagonia", "2026-02-15", "mandado de busca", 1,
         "Apreensao de drogas e arma.")).lastrowid
    inq_id = con.execute(
        "INSERT INTO inquerito (caso_id, numero_oficial, delegado_responsavel, "
        "data_instauracao, situacao_prisional, lei_prazo, status, conferido) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (caso_id, "2026.0101.000457-3", "Mariana Teixeira",
         "2026-02-15", "preso", "drogas", "em_andamento", 0)).lastrowid
    for cod in ("LD_33", "ED_16", "LD_35"):
        con.execute("INSERT INTO crime (inquerito_id, tipificacao_codigo, descricao) "
                    "VALUES (?,?,?)", (inq_id, cod, catalogo.busca(cod)["descricao"]))
    con.execute("INSERT INTO pessoa (inquerito_id, nome, papel, situacao) "
                "VALUES (?,?,?,?)", (inq_id, "Jose Carlos", "preso", "preso"))
    con.execute("INSERT INTO documento (inquerito_id, caso_id, nome_arquivo, tipo, "
                "status_extracao) VALUES (?,?,?,?,?)",
                (inq_id, caso_id, "ip.pdf", "portaria", "conferido"))
    con.commit()
    yield con
    con.close()
