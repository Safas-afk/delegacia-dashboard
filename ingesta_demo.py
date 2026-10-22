"""Demonstra a INTEGRACAO completa: PDF real -> Qwen -> banco cifrado -> dashboard.
Roda o modelo de verdade (lento, ~2min). Prova a ponte pipeline->banco.
"""
import os
from app import db, ingestao, prazos, pendencias, catalogo

CAMINHO = "ingesta_demo.db"
SENHA = "senha-demo"
PDF = "prototipo/pdfs/inquerito_ficticio.pdf"
HOJE = "2026-03-12"


def main():
    if os.path.exists(CAMINHO):
        os.remove(CAMINHO)
    con = db.conectar(CAMINHO, SENHA)
    db.inicializa(con)

    print(">> ingerindo PDF real (PDF->markdown->Qwen->banco)...")
    r = ingestao.ingesta(con, PDF)
    print(f"   {'NOVO' if r['novo'] else 'ANEXADO'} inquerito id={r['inquerito_id']} "
          f"| tipificacoes {r['tipificacoes']}")

    inq = dict(con.execute("SELECT * FROM inquerito WHERE id=?", (r["inquerito_id"],)).fetchone())
    crimes = [dict(x) for x in con.execute(
        "SELECT * FROM crime WHERE inquerito_id=?", (r["inquerito_id"],))]
    pessoas = [dict(x) for x in con.execute(
        "SELECT * FROM pessoa WHERE inquerito_id=?", (r["inquerito_id"],))]
    docs = [dict(x) for x in con.execute(
        "SELECT * FROM documento WHERE inquerito_id=?", (r["inquerito_id"],))]

    p = prazos.calcula_prazo(inq["lei_prazo"], inq["situacao_prisional"],
                             inq["data_instauracao"], bool(inq["prorrogado"]), hoje=HOJE)
    pend = pendencias.avalia_inquerito(inq, crimes, docs, hoje=HOJE)

    print("\n" + "=" * 64)
    print(f"  IP {inq['numero_oficial']} | {inq['situacao_prisional'].upper()} | "
          f"conferido={inq['conferido']}")
    print(f"  Delegado: {inq['delegado_responsavel']}")
    print("  Crimes (IA, nao conferidos):")
    for c in crimes:
        info = catalogo.busca(c["tipificacao_codigo"])
        print(f"    - {info['artigo']} {info['descricao']}")
    print("  Pessoas (IA, nao conferidas):")
    for ps in pessoas:
        print(f"    - {ps['nome']} ({ps['papel']}/{ps['situacao']})")
    print(f"  PRAZO: limite {p['data_limite']} | restam {p['dias_restantes']} dias "
          f"| {p['cor'].upper()}")
    print("  O QUE FALTA:")
    for x in pend:
        print(f"    [{x['severidade'].upper()}] {x['descricao']}")
    print("=" * 64)
    print("  (tudo conferido=0: aguarda validacao do delegado)")
    con.close()


if __name__ == "__main__":
    main()
