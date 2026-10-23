"""Escrita da conferencia: o delegado aprova, corrige ou rejeita o que a IA
sugeriu (linhas com conferido=0).

Aprovar e corrigir sao a MESMA acao: salvar. Aprovar = salvar sem mudar campo
(so marca conferido=1); corrigir = salvar com os campos editados. Rejeitar =
apagar a linha (sugestao errada da IA).

Seguranca: so tabelas e colunas da whitelist sao tocadas (os nomes entram em
SQL por f-string, entao tem que vir de conjunto fixo, nunca do cliente).
"""
from . import db, catalogo

TABELAS = {"inquerito", "crime", "pessoa"}

EDITAVEIS = {
    "inquerito": {"numero_oficial", "delegado_responsavel", "data_instauracao",
                  "situacao_prisional", "lei_prazo", "status", "prorrogado",
                  "data_prorrogacao"},
    "crime": {"tipificacao_codigo", "descricao", "data_fato"},
    "pessoa": {"nome", "papel", "situacao"},
}


def _existe(con, tipo, item_id):
    return con.execute(
        f"SELECT 1 FROM {tipo} WHERE id = ?", (item_id,)).fetchone() is not None


def salvar(con, tipo, item_id, campos, usuario="delegado"):
    """Aplica os campos editados (so os da whitelist) e marca conferido=1.
    Retorna False se o item nao existe. Levanta ValueError se o tipo e invalido.
    """
    if tipo not in TABELAS:
        raise ValueError(f"tipo invalido: {tipo}")
    if not _existe(con, tipo, item_id):
        return False

    permitido = EDITAVEIS[tipo]
    sets = {k: v for k, v in (campos or {}).items() if k in permitido}
    # crime: a descricao segue o catalogo da tipificacao escolhida
    if tipo == "crime" and "tipificacao_codigo" in sets:
        info = catalogo.busca(sets["tipificacao_codigo"])
        if info:
            sets["descricao"] = info["descricao"]
    sets["conferido"] = 1

    colunas = ", ".join(f"{k} = ?" for k in sets)
    con.execute(f"UPDATE {tipo} SET {colunas} WHERE id = ?",
                (*sets.values(), item_id))
    db.registra_auditoria(con, usuario, f"conferir_{tipo}",
                          f"id={item_id} campos={sorted(sets)}")
    con.commit()
    return True


def rejeitar(con, tipo, item_id, usuario="delegado"):
    """Apaga a sugestao. Retorna False se nao existe; ValueError se tipo invalido."""
    if tipo not in TABELAS:
        raise ValueError(f"tipo invalido: {tipo}")
    if not _existe(con, tipo, item_id):
        return False
    con.execute(f"DELETE FROM {tipo} WHERE id = ?", (item_id,))
    db.registra_auditoria(con, usuario, f"rejeitar_{tipo}", f"id={item_id}")
    con.commit()
    return True
