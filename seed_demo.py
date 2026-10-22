"""Demonstra a base: cria um banco cifrado, insere o caso do PDF ficticio e
imprime o que o dashboard mostraria (prazo calculado + pendencias automaticas).
Sem interface - so prova que as regras legais funcionam ponta a ponta.
"""
import os
from app import db, prazos, pendencias, catalogo

CAMINHO = "demo.db"
SENHA = "senha-demo-trocar-depois"
HOJE = "2026-03-12"   # simula o dia em que o delegado abre o sistema


def main():
    if os.path.exists(CAMINHO):
        os.remove(CAMINHO)
    con = db.conectar(CAMINHO, SENHA)
    db.inicializa(con)

    # --- caso ---
    cur = con.execute(
        "INSERT INTO caso (nome, data_abertura, origem, segredo_justica, resumo) "
        "VALUES (?,?,?,?,?)",
        ("Operacao Patagonia", "2026-02-15", "mandado de busca e apreensao", 1,
         "Apreensao de drogas e arma em cumprimento de mandado."))
    caso_id = cur.lastrowid

    # --- inquerito (dados que a IA extraiu do PDF) ---
    cur = con.execute(
        "INSERT INTO inquerito (caso_id, numero_oficial, delegado_responsavel, "
        "data_instauracao, situacao_prisional, lei_prazo, status) VALUES (?,?,?,?,?,?,?)",
        (caso_id, "2026.0101.000457-3", "Mariana Teixeira de Almeida",
         "2026-02-15", "preso", "drogas", "em_andamento"))
    inq_id = cur.lastrowid

    # --- crimes (um caso -> varios crimes) ---
    for cod in ("LD_33", "ED_16", "LD_35"):
        con.execute("INSERT INTO crime (inquerito_id, tipificacao_codigo, descricao) "
                    "VALUES (?,?,?)", (inq_id, cod, catalogo.busca(cod)["descricao"]))

    # --- pessoas ---
    con.execute("INSERT INTO pessoa (inquerito_id, nome, papel, situacao) VALUES (?,?,?,?)",
                (inq_id, "Jose Carlos dos Santos Pereira", "preso", "preso"))
    con.execute("INSERT INTO pessoa (inquerito_id, nome, papel, situacao) VALUES (?,?,?,?)",
                (inq_id, "Maria Eduarda Lima Souza", "investigado", "foragido"))

    # --- documento (so a portaria; SEM comunicacao ao MP e SEM laudo definitivo) ---
    con.execute("INSERT INTO documento (inquerito_id, caso_id, nome_arquivo, tipo, "
                "status_extracao) VALUES (?,?,?,?,?)",
                (inq_id, caso_id, "inquerito_ficticio.pdf", "portaria", "conferido"))
    con.commit()
    db.registra_auditoria(con, "delegado", "demo", "inseriu caso Operacao Patagonia")

    # ---------- o que o DASHBOARD mostraria ----------
    inq = dict(con.execute("SELECT * FROM inquerito WHERE id=?", (inq_id,)).fetchone())
    crimes = [dict(r) for r in con.execute(
        "SELECT * FROM crime WHERE inquerito_id=?", (inq_id,))]
    docs = [dict(r) for r in con.execute(
        "SELECT * FROM documento WHERE inquerito_id=?", (inq_id,))]

    p = prazos.calcula_prazo(inq["lei_prazo"], inq["situacao_prisional"],
                             inq["data_instauracao"], bool(inq["prorrogado"]), hoje=HOJE)
    pend = pendencias.avalia_inquerito(inq, crimes, docs, hoje=HOJE)

    print("=" * 64)
    print(f"  CASO: Operacao Patagonia   [SEGREDO DE JUSTICA]   (hoje {HOJE})")
    print("=" * 64)
    print(f"  IP {inq['numero_oficial']} - Del. {inq['delegado_responsavel']}")
    print(f"  Situacao: {inq['situacao_prisional'].upper()} | "
          f"Instaurado: {inq['data_instauracao']} | Lei: {inq['lei_prazo']}")
    print("  Crimes:")
    for c in crimes:
        info = catalogo.busca(c["tipificacao_codigo"])
        print(f"    - {info['artigo']} {info['descricao']} ({info['lei']})")
    cor = {"verde": "VERDE", "amarelo": "AMARELO", "vermelho": "VERMELHO"}[p["cor"]]
    print(f"\n  PRAZO DO IP: limite {p['data_limite']} | "
          f"restam {p['dias_restantes']} dias | semaforo {cor}")
    print("\n  O QUE FALTA / ALERTAS:")
    sev_ordem = {"critica": 0, "alta": 1, "media": 2, "baixa": 3}
    for x in sorted(pend, key=lambda z: sev_ordem[z["severidade"]]):
        print(f"    [{x['severidade'].upper():8}] {x['descricao']}")
    print("=" * 64)
    con.close()


if __name__ == "__main__":
    main()
