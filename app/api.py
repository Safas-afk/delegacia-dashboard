"""Backend FastAPI do dashboard. So LEITURA nesta etapa: le o banco e serve JSON
para o front. Escrita (conferencia, processar documento) vem em ciclo proprio.

Offline real: so escuta em 127.0.0.1. Sem senha e sem login (decisao do delegado
2026-10-23): o caminho do banco vem de env DELEGACIA_DB_CAMINHO (default demo.db).
Uma conexao por requisicao (app local, 1 usuario): simples e sem problema de thread.
"""
import os

from fastapi import Body, Depends, FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles

from . import catalogo, conferencia, db, visao

DIST = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "dist")


def abrir_conexao():
    caminho = os.environ.get("DELEGACIA_DB_CAMINHO", "demo.db")
    # check_same_thread=False: o FastAPI pode resolver esta dependencia numa
    # thread do pool e rodar o endpoint em outra. A conexao e por requisicao
    # (nunca compartilhada entre requisicoes simultaneas), entao e seguro.
    return db.conectar(caminho, check_same_thread=False)


def get_con():
    con = abrir_conexao()
    try:
        yield con
    finally:
        con.close()


app = FastAPI(title="Dashboard DTE")


@app.get("/api/painel")
def painel(hoje: str | None = Query(None), con=Depends(get_con)):
    return visao.painel(con, hoje)


@app.get("/api/casos")
def casos(hoje: str | None = Query(None), con=Depends(get_con)):
    return visao.lista_casos(con, hoje)


@app.get("/api/casos/{caso_id}")
def caso(caso_id: int, hoje: str | None = Query(None), con=Depends(get_con)):
    d = visao.detalhe_caso(con, caso_id, hoje)
    if d is None:
        raise HTTPException(status_code=404, detail="caso nao encontrado")
    return d


@app.get("/api/conferencia")
def listar_conferencia(con=Depends(get_con)):
    return visao.itens_conferencia(con)


@app.get("/api/busca")
def busca(q: str = Query(""), con=Depends(get_con)):
    return visao.busca(con, q)


@app.get("/api/catalogo")
def catalogo_tipificacoes():
    # para o dropdown de tipificacao na conferencia de crime
    return [{"codigo": c, "rotulo": r} for c, r in catalogo.lista()]


# --- escrita da conferencia (aprovar/corrigir/rejeitar) ---
@app.put("/api/conferencia/{tipo}/{item_id}")
def conferir(tipo: str, item_id: int, campos: dict = Body(default={}),
             con=Depends(get_con)):
    try:
        ok = conferencia.salvar(con, tipo, item_id, campos)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not ok:
        raise HTTPException(status_code=404, detail="item nao encontrado")
    return {"ok": True}


@app.delete("/api/conferencia/{tipo}/{item_id}")
def rejeitar(tipo: str, item_id: int, con=Depends(get_con)):
    try:
        ok = conferencia.rejeitar(con, tipo, item_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not ok:
        raise HTTPException(status_code=404, detail="item nao encontrado")
    return {"ok": True}


# Front empacotado: serve o build do Vite em / (depois das rotas /api, que tem
# prioridade). So monta se o build existir, pra nao quebrar o dev sem `npm run build`.
if os.path.isdir(DIST):
    app.mount("/", StaticFiles(directory=DIST, html=True), name="web")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
