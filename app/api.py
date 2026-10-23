"""Backend FastAPI do dashboard. So LEITURA nesta etapa: le o banco cifrado e
serve JSON para o front. Escrita (conferencia, processar documento) e login real
vem em ciclos proprios.

Offline real: so escuta em 127.0.0.1. A senha do banco vem de env var
(DELEGACIA_DB_SENHA) ate o login da Secao 3 substituir isso sem mexer nas rotas.
Uma conexao por requisicao (app local, 1 usuario): simples e sem problema de
thread com o SQLCipher.
"""
import os

from fastapi import Depends, FastAPI, HTTPException, Query

from . import db, visao


def abrir_conexao():
    caminho = os.environ.get("DELEGACIA_DB_CAMINHO", "demo.db")
    senha = os.environ.get("DELEGACIA_DB_SENHA")
    if not senha:
        raise RuntimeError("DELEGACIA_DB_SENHA nao definida")
    return db.conectar(caminho, senha)


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
def conferencia(con=Depends(get_con)):
    return visao.itens_conferencia(con)


@app.get("/api/busca")
def busca(q: str = Query(""), con=Depends(get_con)):
    return visao.busca(con, q)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
