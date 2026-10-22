"""Motor de pendencias/alertas automaticos.
Transforma regras legais em "o que falta" e alertas de risco por inquerito.
Base legal (pesquisada):
  - Portaria PCBA 494/2023, art. 2: comunicar a instauracao ao MP em ate 48h.
  - Portaria PCBA 494/2023, art. 4: autos nao podem passar 90 dias na unidade sem
    manifestacao do juizo/MP -> risco de infracao disciplinar do delegado.
  - Lei de Drogas 11.343/2006, art. 50: materialidade do trafico exige laudo DEFINITIVO.
  - Prazo do IP (ver prazos.py): vencendo/vencido vira alerta.
"""
from datetime import date, datetime, timedelta

from . import prazos
from . import catalogo


def _parse(d):
    return datetime.strptime(d, "%Y-%m-%d").date() if isinstance(d, str) else d


def _tem_doc(documentos, tipo):
    return any(d.get("tipo") == tipo for d in documentos)


def _eh_droga(crimes):
    for c in crimes:
        info = catalogo.busca(c.get("tipificacao_codigo", ""))
        if info and info["lei_prazo"] == "drogas" and info["artigo"] in (
                "art. 33", "art. 28", "art. 34", "art. 35", "art. 36"):
            return True
    return False


def avalia_inquerito(inq, crimes, documentos, hoje=None):
    """Retorna lista de pendencias: [{descricao, categoria, severidade}]."""
    hoje = _parse(hoje) if hoje else date.today()
    pend = []
    inst = _parse(inq["data_instauracao"])
    dias_desde = (hoje - inst).days
    ativo = inq.get("status", "em_andamento") == "em_andamento"

    # --- Prazo do IP (Lei de Drogas / CPP) ---
    p = prazos.calcula_prazo(inq["lei_prazo"], inq["situacao_prisional"],
                             inq["data_instauracao"], bool(inq.get("prorrogado")),
                             hoje=hoje.isoformat())
    if ativo and p["vencido"]:
        pend.append({"descricao": f"Prazo do IP VENCIDO ha {-p['dias_restantes']} dias "
                                  f"(limite {p['data_limite']})",
                     "categoria": "prazo", "severidade": "critica"})
    elif ativo and p["cor"] == "vermelho":
        pend.append({"descricao": f"Prazo do IP vence em {p['dias_restantes']} dias "
                                  f"({p['data_limite']})",
                     "categoria": "prazo", "severidade": "alta"})

    # --- 48h para comunicar o MP (Portaria 494, art. 2) ---
    if ativo and not _tem_doc(documentos, "comunicacao_mp"):
        horas = (hoje - inst).days * 24
        if horas >= 48:
            pend.append({"descricao": "Comunicacao da instauracao ao MP NAO consta "
                                      "(prazo de 48h, Portaria PCBA 494/2023 art. 2)",
                         "categoria": "comunicacao", "severidade": "alta"})
        else:
            pend.append({"descricao": "Comunicar instauracao ao MP em ate 48h "
                                      "(Portaria PCBA 494/2023 art. 2)",
                         "categoria": "comunicacao", "severidade": "media"})

    # --- 90 dias na unidade sem manifestacao (Portaria 494, art. 4) = risco disciplinar ---
    if ativo and dias_desde > 90:
        pend.append({"descricao": f"IP ha {dias_desde} dias na unidade sem manifestacao "
                                  f"do juizo/MP - RISCO DISCIPLINAR (Portaria PCBA 494/2023 art. 4)",
                     "categoria": "disciplinar", "severidade": "critica"})

    # --- Laudo definitivo do trafico (Lei de Drogas art. 50) ---
    if ativo and _eh_droga(crimes) and not _tem_doc(documentos, "laudo_definitivo"):
        pend.append({"descricao": "Falta laudo toxicologico DEFINITIVO "
                                  "(materialidade do trafico - Lei 11.343/2006 art. 50)",
                     "categoria": "laudo", "severidade": "alta"})

    return pend
