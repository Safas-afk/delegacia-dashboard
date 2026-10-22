"""Prototipo do pipeline de extracao:
  PDF -> markdown (pymupdf4llm) -> Qwen local (llama-cpp-python) -> JSON de campos.
Mede a precisao comparando com o gabarito do documento ficticio.
Tudo offline, CPU-only.
"""
import json
import sys
import time

PDF = "pdfs/inquerito_ficticio.pdf"
MODELO = "modelos/qwen2.5-3b-instruct-q4_k_m.gguf"

# ---- Gabarito (o que o documento ficticio realmente diz) -------------------
GABARITO = {
    "numero_ip": "2026.0101.000457-3",
    "delegacia": "DTE Vitoria da Conquista",
    "delegado_responsavel": "Mariana Teixeira de Almeida",
    "segredo_de_justica": True,
    "data_do_fato": "2026-02-14",
    "data_instauracao": "2026-02-15",
    "indiciado_preso": "Jose Carlos dos Santos Pereira",
    "situacao_prisional": "preso",
    "tipificacoes": ["art. 33 da Lei 11.343/2006",
                     "art. 16 da Lei 10.826/2003",
                     "art. 35 da Lei 11.343/2006"],
}

# ---- Esquema de saida que pedimos ao modelo --------------------------------
ESQUEMA = {
    "numero_ip": "string - numero do inquerito policial",
    "delegacia": "string - unidade policial",
    "delegado_responsavel": "string - nome da autoridade policial",
    "segredo_de_justica": "boolean - true se o documento mencionar segredo de justica",
    "data_do_fato": "string YYYY-MM-DD - data em que o fato ocorreu",
    "data_instauracao": "string YYYY-MM-DD - data de instauracao/assinatura",
    "indiciado_preso": "string - nome da pessoa presa em flagrante",
    "situacao_prisional": "string - 'preso' ou 'solto'",
    "tipificacoes": "lista de strings - artigos/leis dos crimes citados",
}

PROMPT = """Voce e um assistente que extrai dados de documentos policiais brasileiros.
Leia o DOCUMENTO abaixo (em markdown) e preencha EXATAMENTE o JSON pedido.
Regras:
- Responda SOMENTE com um objeto JSON valido, sem texto antes ou depois.
- Datas no formato YYYY-MM-DD.
- Se um campo nao existir no documento, use null.
- Em "tipificacoes" liste todos os artigos de lei citados.

CAMPOS E SIGNIFICADOS:
{esquema}

DOCUMENTO:
---
{documento}
---

JSON:"""


def pdf_para_markdown(caminho):
    import pymupdf4llm
    return pymupdf4llm.to_markdown(caminho)


def roda_qwen(prompt):
    from llama_cpp import Llama
    llm = Llama(model_path=MODELO, n_ctx=4096, n_threads=8, verbose=False)
    out = llm.create_chat_completion(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=1024,
        response_format={"type": "json_object"},
    )
    return out["choices"][0]["message"]["content"]


def compara(extraido, gabarito):
    acertos, total = 0, len(gabarito)
    linhas = []
    for campo, esperado in gabarito.items():
        obtido = extraido.get(campo)
        if isinstance(esperado, list):
            ok = isinstance(obtido, list) and all(
                any(e.split(" da ")[0].lower() in str(o).lower() for o in obtido)
                for e in esperado)
        elif isinstance(esperado, bool):
            ok = bool(obtido) == esperado
        else:
            ok = obtido is not None and esperado.lower().replace(".", "") in \
                str(obtido).lower().replace(".", "")
        acertos += ok
        linhas.append(f"  [{'OK ' if ok else 'XX '}] {campo}: {obtido!r}")
    return acertos, total, linhas


def main():
    print(">> convertendo PDF para markdown...")
    t0 = time.time()
    md = pdf_para_markdown(PDF)
    open("saida/doc.md", "w").write(md)
    print(f"   markdown: {len(md)} chars em {time.time()-t0:.1f}s")

    prompt = PROMPT.format(esquema=json.dumps(ESQUEMA, ensure_ascii=False, indent=2),
                           documento=md)

    print(">> rodando Qwen local (CPU)...")
    t0 = time.time()
    bruto = roda_qwen(prompt)
    dt = time.time() - t0
    open("saida/extraido.json", "w").write(bruto)
    print(f"   Qwen respondeu em {dt:.1f}s")

    try:
        extraido = json.loads(bruto)
    except Exception as e:
        print("!! JSON invalido:", e)
        print(bruto[:500])
        sys.exit(1)

    acertos, total, linhas = compara(extraido, GABARITO)
    print("\n== RESULTADO DA EXTRACAO ==")
    print("\n".join(linhas))
    print(f"\n>> PRECISAO: {acertos}/{total} campos ({100*acertos//total}%)  |  "
          f"Qwen: {dt:.1f}s")


if __name__ == "__main__":
    main()
