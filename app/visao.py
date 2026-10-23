"""Monta a visao que o dashboard mostra, a partir do banco.

Junta o que esta solto no banco (inquerito, crimes, pessoas, documentos) com o
que e CALCULADO (prazo do IP via prazos.py, pendencias via pendencias.py) e com
o catalogo de tipificacoes. Logica pura e testavel: recebe uma conexao aberta e
devolve dicts/listas prontos para virar JSON. As rotas HTTP (api.py) so chamam
estas funcoes.

O padrao aqui e o mesmo do seed_demo.py, agora reaproveitavel.
"""
from datetime import date

from . import prazos, pendencias, catalogo

SEV_ORDEM = {"critica": 0, "alta": 1, "media": 2, "baixa": 3}


def _hoje_iso(hoje=None):
    return hoje if hoje else date.today().isoformat()


def _crimes(con, inq_id):
    linhas = con.execute(
        "SELECT * FROM crime WHERE inquerito_id = ? ORDER BY id", (inq_id,))
    saida = []
    for r in linhas:
        c = dict(r)
        info = catalogo.busca(c.get("tipificacao_codigo"))
        c["catalogo"] = info
        saida.append(c)
    return saida


def _pessoas(con, inq_id):
    return [dict(r) for r in con.execute(
        "SELECT * FROM pessoa WHERE inquerito_id = ? ORDER BY id", (inq_id,))]


def _documentos(con, inq_id):
    # texto_extraido e extracao_json sao pesados; ficam de fora da listagem.
    return [dict(r) for r in con.execute(
        "SELECT id, inquerito_id, caso_id, nome_arquivo, caminho, tipo, data, "
        "hash, status_extracao, criado_em FROM documento "
        "WHERE inquerito_id = ? ORDER BY id", (inq_id,))]


def inquerito_view(con, inq, hoje=None):
    """Um inquerito + prazo calculado + pendencias + crimes/pessoas/docs.
    `inq` e uma Row (ou dict) da tabela inquerito.
    """
    inq = dict(inq)
    hoje = _hoje_iso(hoje)
    crimes = _crimes(con, inq["id"])
    docs_leves = _documentos(con, inq["id"])
    # pendencias precisa do tipo de cada documento; usa a listagem leve
    prazo = prazos.calcula_prazo(
        inq["lei_prazo"], inq["situacao_prisional"], inq["data_instauracao"],
        bool(inq.get("prorrogado")), hoje=hoje)
    pend = pendencias.avalia_inquerito(inq, crimes, docs_leves, hoje=hoje)
    pend = sorted(pend, key=lambda p: SEV_ORDEM[p["severidade"]])
    return {
        "inquerito": inq,
        "prazo": prazo,
        "crimes": crimes,
        "pessoas": _pessoas(con, inq["id"]),
        "documentos": docs_leves,
        "pendencias": pend,
    }


def _inqueritos_do_caso(con, caso_id):
    return con.execute(
        "SELECT * FROM inquerito WHERE caso_id = ? ORDER BY id", (caso_id,))


def detalhe_caso(con, caso_id, hoje=None):
    """Tela 3: o caso com todos os seus inqueritos ja montados."""
    row = con.execute("SELECT * FROM caso WHERE id = ?", (caso_id,)).fetchone()
    if row is None:
        return None
    caso = dict(row)
    caso["inqueritos"] = [inquerito_view(con, inq, hoje)
                          for inq in _inqueritos_do_caso(con, caso_id)]
    return caso


def lista_casos(con, hoje=None):
    """Tela 2: um resumo por caso (prazo mais urgente dos seus inqueritos).
    Ordenado do mais urgente (menos dias restantes) para o menos.
    """
    hoje = _hoje_iso(hoje)
    saida = []
    for caso_row in con.execute("SELECT * FROM caso ORDER BY id"):
        caso = dict(caso_row)
        inqs = [inquerito_view(con, inq, hoje)
                for inq in _inqueritos_do_caso(con, caso["id"])]
        # prazo mais urgente entre os inqueritos ativos
        ativos = [i for i in inqs
                  if i["inquerito"].get("status") == "em_andamento"]
        if ativos:
            mais_urgente = min(ativos, key=lambda i: i["prazo"]["dias_restantes"])
            prazo = mais_urgente["prazo"]
        else:
            prazo = None
        n_pend = sum(len(i["pendencias"]) for i in inqs)
        saida.append({
            "id": caso["id"],
            "nome": caso["nome"],
            "status": caso["status"],
            "segredo_justica": caso["segredo_justica"],
            "qtd_inqueritos": len(inqs),
            "prazo": prazo,
            "qtd_pendencias": n_pend,
        })
    # mais urgente primeiro; casos sem prazo (sem inquerito ativo) por ultimo
    saida.sort(key=lambda c: (c["prazo"] is None,
                              c["prazo"]["dias_restantes"] if c["prazo"] else 0))
    return saida


def painel(con, hoje=None):
    """Tela 1: contadores, casos por semaforo e alertas criticos na abertura."""
    hoje = _hoje_iso(hoje)
    casos = lista_casos(con, hoje)
    semaforo = {"vermelho": 0, "amarelo": 0, "verde": 0}
    for c in casos:
        if c["prazo"]:
            semaforo[c["prazo"]["cor"]] += 1

    # alertas criticos: pendencias criticas/altas de todos os inqueritos ativos
    alertas = []
    for caso_row in con.execute("SELECT * FROM caso ORDER BY id"):
        caso = dict(caso_row)
        for inq in _inqueritos_do_caso(con, caso["id"]):
            view = inquerito_view(con, inq, hoje)
            if view["inquerito"].get("status") != "em_andamento":
                continue
            for p in view["pendencias"]:
                if p["severidade"] in ("critica", "alta"):
                    alertas.append({
                        "caso_id": caso["id"],
                        "caso_nome": caso["nome"],
                        "numero_ip": view["inquerito"].get("numero_oficial"),
                        **p,
                    })
    alertas.sort(key=lambda a: SEV_ORDEM[a["severidade"]])

    total_inq = con.execute("SELECT count(*) AS n FROM inquerito").fetchone()["n"]
    return {
        "hoje": hoje,
        "contadores": {
            "casos": len(casos),
            "inqueritos": total_inq,
            "nao_conferidos": con.execute(
                "SELECT count(*) AS n FROM inquerito WHERE conferido = 0"
            ).fetchone()["n"],
        },
        "semaforo": semaforo,
        "alertas": alertas,
    }


def itens_conferencia(con):
    """Tela 4: o que a IA sugeriu e ainda aguarda conferencia (conferido=0)."""
    inqs = [dict(r) for r in con.execute(
        "SELECT * FROM inquerito WHERE conferido = 0 ORDER BY id")]
    crimes = [dict(r) for r in con.execute(
        "SELECT * FROM crime WHERE conferido = 0 ORDER BY id")]
    pessoas = [dict(r) for r in con.execute(
        "SELECT * FROM pessoa WHERE conferido = 0 ORDER BY id")]
    docs = [dict(r) for r in con.execute(
        "SELECT id, inquerito_id, nome_arquivo, tipo, extracao_json, status_extracao "
        "FROM documento WHERE status_extracao = 'processado' ORDER BY id")]
    return {"inqueritos": inqs, "crimes": crimes,
            "pessoas": pessoas, "documentos": docs}


def busca(con, q):
    """Tela 5: busca em caso (nome/resumo), inquerito (nº IP) e pessoa (nome)."""
    termo = f"%{(q or '').strip()}%"
    casos = [dict(r) for r in con.execute(
        "SELECT id, nome, status FROM caso "
        "WHERE nome LIKE ? OR resumo LIKE ? ORDER BY id", (termo, termo))]
    inqueritos = [dict(r) for r in con.execute(
        "SELECT id, caso_id, numero_oficial, delegado_responsavel FROM inquerito "
        "WHERE numero_oficial LIKE ? ORDER BY id", (termo,))]
    pessoas = [dict(r) for r in con.execute(
        "SELECT p.id, p.inquerito_id, i.caso_id, p.nome, p.papel FROM pessoa p "
        "JOIN inquerito i ON i.id = p.inquerito_id "
        "WHERE p.nome LIKE ? ORDER BY p.id", (termo,))]
    return {"casos": casos, "inqueritos": inqueritos, "pessoas": pessoas}
