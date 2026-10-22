"""Catalogo fixo de tipificacoes penais que a DTE encontra.
Cada item carrega a lei e qual regra de prazo de IP se aplica ('drogas' ou 'cpp').
Usado como dropdown na interface e como lista fechada para a IA classificar.
"""

# codigo interno -> dados da tipificacao
TIPIFICACOES = {
    # Lei de Drogas 11.343/2006 -> prazo da propria Lei de Drogas (art. 51)
    "LD_28":  {"lei": "Lei 11.343/2006", "artigo": "art. 28", "lei_prazo": "drogas",
               "descricao": "Porte de droga para consumo pessoal"},
    "LD_33":  {"lei": "Lei 11.343/2006", "artigo": "art. 33", "lei_prazo": "drogas",
               "descricao": "Trafico de drogas"},
    "LD_34":  {"lei": "Lei 11.343/2006", "artigo": "art. 34", "lei_prazo": "drogas",
               "descricao": "Maquinario para o trafico"},
    "LD_35":  {"lei": "Lei 11.343/2006", "artigo": "art. 35", "lei_prazo": "drogas",
               "descricao": "Associacao para o trafico"},
    "LD_36":  {"lei": "Lei 11.343/2006", "artigo": "art. 36", "lei_prazo": "drogas",
               "descricao": "Financiamento do trafico"},
    "LD_37":  {"lei": "Lei 11.343/2006", "artigo": "art. 37", "lei_prazo": "drogas",
               "descricao": "Informante/colaborador do trafico"},

    # Estatuto do Desarmamento 10.826/2003 -> prazo comum do CPP
    "ED_12":  {"lei": "Lei 10.826/2003", "artigo": "art. 12", "lei_prazo": "cpp",
               "descricao": "Posse irregular de arma de uso permitido"},
    "ED_14":  {"lei": "Lei 10.826/2003", "artigo": "art. 14", "lei_prazo": "cpp",
               "descricao": "Porte ilegal de arma de uso permitido"},
    "ED_16":  {"lei": "Lei 10.826/2003", "artigo": "art. 16", "lei_prazo": "cpp",
               "descricao": "Posse/porte de arma de uso restrito ou proibido"},
    "ED_17":  {"lei": "Lei 10.826/2003", "artigo": "art. 17", "lei_prazo": "cpp",
               "descricao": "Comercio ilegal de arma de fogo"},
    "ED_18":  {"lei": "Lei 10.826/2003", "artigo": "art. 18", "lei_prazo": "cpp",
               "descricao": "Trafico internacional de arma de fogo"},

    # Organizacao criminosa 12.850/2013 -> prazo comum do CPP
    "OC_2":   {"lei": "Lei 12.850/2013", "artigo": "art. 2", "lei_prazo": "cpp",
               "descricao": "Integrar organizacao criminosa"},
}


def busca(codigo):
    return TIPIFICACOES.get(codigo)


def lista():
    """Lista para dropdown: [(codigo, 'art. 33 - Trafico de drogas (Lei 11.343/2006)'), ...]."""
    return [(c, f"{v['artigo']} - {v['descricao']} ({v['lei']})")
            for c, v in TIPIFICACOES.items()]
