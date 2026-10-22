"""Ingestao: liga o pipeline de IA ao banco.
  extrai(pdf)  -> dict com os campos (parte lenta: PDF->markdown->Qwen)
  grava(con, dados, ...) -> escreve no banco como PROPOSTA (conferido=0),
                            casando pelo numero do IP.
As duas funcoes sao separadas de proposito: grava() e testavel com um JSON
fixo, sem precisar rodar o modelo.
"""
import hashlib
import json
import os

from . import catalogo

MODELO_PADRAO = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                             "prototipo", "modelos",
                             "qwen2.5-3b-instruct-q4_k_m.gguf")

ESQUEMA = {
    "numero_ip": "string - numero do inquerito policial",
    "nome_operacao": "string - nome/apelido da operacao, se houver; senao null",
    "delegado_responsavel": "string - nome da autoridade policial",
    "segredo_de_justica": "boolean - true se mencionar segredo de justica",
    "data_do_fato": "string YYYY-MM-DD - data do fato",
    "data_instauracao": "string YYYY-MM-DD - data de instauracao/assinatura",
    "situacao_prisional": "string - 'preso' se houver preso em flagrante, senao 'solto'",
    "resumo": "string - resumo curto do caso em uma frase",
    "tipificacoes": "lista de strings - artigos de lei citados (ex: 'art. 33 da Lei 11.343/2006')",
    "pessoas": "lista de objetos {nome, papel, situacao} - papel: investigado|preso|testemunha|vitima|condutor",
}

PROMPT = """Voce extrai dados de documentos policiais brasileiros.
Leia o DOCUMENTO (markdown) e preencha EXATAMENTE o JSON pedido.
Regras:
- Responda SOMENTE com JSON valido, sem texto antes ou depois.
- Datas no formato YYYY-MM-DD. Campo inexistente = null.
- Em "tipificacoes" liste todos os artigos de lei citados.
- Em "pessoas" liste cada pessoa com seu papel.

CAMPOS:
{esquema}

DOCUMENTO:
---
{documento}
---

JSON:"""


# --------------------------------------------------------------------------
# Extracao (parte lenta - usa o modelo)
# --------------------------------------------------------------------------
def pdf_para_markdown(caminho_pdf):
    import pymupdf4llm
    return pymupdf4llm.to_markdown(caminho_pdf)


def extrai(caminho_pdf, modelo=MODELO_PADRAO):
    """PDF -> markdown -> Qwen -> dict de campos. Retorna tambem o markdown."""
    from llama_cpp import Llama
    md = pdf_para_markdown(caminho_pdf)
    prompt = PROMPT.format(esquema=json.dumps(ESQUEMA, ensure_ascii=False, indent=2),
                           documento=md)
    llm = Llama(model_path=modelo, n_ctx=4096, n_threads=8, verbose=False)
    out = llm.create_chat_completion(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0, max_tokens=1024,
        response_format={"type": "json_object"})
    dados = json.loads(out["choices"][0]["message"]["content"])
    dados["_markdown"] = md
    return dados


# --------------------------------------------------------------------------
# Mapeamento deterministico tipificacao-texto -> codigo do catalogo
# --------------------------------------------------------------------------
def _num_lei(texto):
    import re
    m = re.search(r"(\d{2}\.?\d{3})", texto or "")
    return m.group(1).replace(".", "") if m else ""


def mapeia_tipificacoes(lista_texto):
    """['art. 33 da Lei 11.343/2006', ...] -> ['LD_33', ...] (deterministico)."""
    codigos = []
    for texto in lista_texto or []:
        t = (texto or "").lower()
        num = _num_lei(t)
        for cod, info in catalogo.TIPIFICACOES.items():
            artigo = info["artigo"].lower()                 # ex: 'art. 33'
            lei_num = info["lei"].split()[1].split("/")[0].replace(".", "")  # ex: '11343'
            if artigo in t and lei_num == num:
                if cod not in codigos:
                    codigos.append(cod)
                break
    return codigos


def _lei_prazo(codigos):
    """Se houver qualquer crime de droga, o prazo principal e o da Lei de Drogas."""
    for c in codigos:
        info = catalogo.busca(c)
        if info and info["lei_prazo"] == "drogas":
            return "drogas"
    return "cpp" if codigos else "drogas"


def hash_arquivo(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            h.update(bloco)
    return h.hexdigest()


# --------------------------------------------------------------------------
# Gravacao (testavel sem modelo) - casa pelo numero do IP
# --------------------------------------------------------------------------
def grava(con, dados, caminho_pdf=None, nome_arquivo=None):
    """Escreve os dados extraidos como PROPOSTA (conferido=0).
    Casa pelo numero do IP: existe -> anexa doc e completa campos vazios
    (sem sobrescrever o que ja foi conferido); nao existe -> cria caso+inquerito.
    Retorna dict com inquerito_id, caso_id e 'novo' (bool).
    """
    numero = (dados.get("numero_ip") or "").strip()
    codigos = mapeia_tipificacoes(dados.get("tipificacoes"))
    lei_prazo = _lei_prazo(codigos)

    existente = None
    if numero:
        row = con.execute(
            "SELECT * FROM inquerito WHERE numero_oficial = ?", (numero,)).fetchone()
        existente = dict(row) if row else None

    if existente:
        inq_id = existente["id"]
        caso_id = existente["caso_id"]
        novo = False
        _completa_campos_vazios(con, existente, dados, lei_prazo)
    else:
        caso_id = con.execute(
            "INSERT INTO caso (nome, data_abertura, origem, segredo_justica, resumo) "
            "VALUES (?,?,?,?,?)",
            (dados.get("nome_operacao") or f"IP {numero or 'sem numero'}",
             dados.get("data_instauracao"), "documento",
             1 if dados.get("segredo_de_justica") else 0,
             dados.get("resumo"))).lastrowid
        inq_id = con.execute(
            "INSERT INTO inquerito (caso_id, numero_oficial, delegado_responsavel, "
            "data_instauracao, situacao_prisional, lei_prazo, conferido) "
            "VALUES (?,?,?,?,?,?,0)",
            (caso_id, numero or None, dados.get("delegado_responsavel"),
             dados.get("data_instauracao"),
             dados.get("situacao_prisional") or "solto", lei_prazo)).lastrowid
        novo = True

    _insere_crimes(con, inq_id, codigos, dados.get("data_do_fato"))
    _insere_pessoas(con, inq_id, dados.get("pessoas"))

    if nome_arquivo or caminho_pdf:
        nome = nome_arquivo or os.path.basename(caminho_pdf)
        h = hash_arquivo(caminho_pdf) if caminho_pdf and os.path.exists(caminho_pdf) else None
        dados_json = {k: v for k, v in dados.items() if k != "_markdown"}
        con.execute(
            "INSERT INTO documento (inquerito_id, caso_id, nome_arquivo, caminho, tipo, "
            "hash, texto_extraido, extracao_json, status_extracao) "
            "VALUES (?,?,?,?,?,?,?,?,'processado')",
            (inq_id, caso_id, nome, caminho_pdf, "portaria", h,
             dados.get("_markdown"), json.dumps(dados_json, ensure_ascii=False)))

    con.commit()
    return {"inquerito_id": inq_id, "caso_id": caso_id, "novo": novo,
            "tipificacoes": codigos}


def _completa_campos_vazios(con, inq, dados, lei_prazo):
    """Preenche so colunas vazias; nunca mexe em inquerito ja conferido."""
    if inq.get("conferido"):
        return
    mapa = {
        "delegado_responsavel": dados.get("delegado_responsavel"),
        "data_instauracao": dados.get("data_instauracao"),
        "situacao_prisional": dados.get("situacao_prisional"),
        "lei_prazo": lei_prazo,
    }
    for col, valor in mapa.items():
        if valor and not (inq.get(col) or "").strip():
            con.execute(f"UPDATE inquerito SET {col} = ? WHERE id = ?", (valor, inq["id"]))


def _insere_crimes(con, inq_id, codigos, data_fato):
    existentes = {r["tipificacao_codigo"] for r in con.execute(
        "SELECT tipificacao_codigo FROM crime WHERE inquerito_id = ?", (inq_id,))}
    for cod in codigos:
        if cod in existentes:
            continue
        info = catalogo.busca(cod)
        con.execute(
            "INSERT INTO crime (inquerito_id, tipificacao_codigo, descricao, data_fato, "
            "conferido) VALUES (?,?,?,?,0)",
            (inq_id, cod, info["descricao"] if info else None, data_fato))


def _insere_pessoas(con, inq_id, pessoas):
    existentes = {(r["nome"] or "").lower() for r in con.execute(
        "SELECT nome FROM pessoa WHERE inquerito_id = ?", (inq_id,))}
    for p in pessoas or []:
        nome = (p.get("nome") or "").strip()
        if not nome or nome.lower() in existentes:
            continue
        con.execute(
            "INSERT INTO pessoa (inquerito_id, nome, papel, situacao, conferido) "
            "VALUES (?,?,?,?,0)",
            (inq_id, nome, p.get("papel"), p.get("situacao")))
        existentes.add(nome.lower())


def ingesta(con, caminho_pdf, modelo=MODELO_PADRAO):
    """Pipeline completo: extrai do PDF (lento) e grava no banco."""
    dados = extrai(caminho_pdf, modelo)
    return grava(con, dados, caminho_pdf=caminho_pdf)
