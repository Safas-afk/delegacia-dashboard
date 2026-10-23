# Sistema de Acompanhamento de Inquéritos (DTE)

Dashboard **local e offline** para a Delegacia de Tóxicos e Entorpecentes de Vitória da
Conquista/BA. Lê os PDFs dos casos, extrai informações com **IA local (offline)**, e mostra
prazos, urgências e o que falta em cada inquérito — tudo rodando na máquina, sem internet.

> Dados sensíveis / segredo de justiça. Nada sai da máquina. Proteção é física: o PC fica em
> sala com câmera e só liga com o login do delegado (decisão 2026-10-23: app sem senha/cifra).

## Estado

- Protótipo de IA validado (PDF → markdown → Qwen local, extração correta em CPU).
- Base de dados pronta: SQLite + catálogo de tipificações + motores de prazo e pendência
  baseados na lei.
- Backend FastAPI (5 rotas de leitura) + dashboard React (5 telas), só leitura. 37 testes passando.

Veja a especificação completa em [`docs/ESPECIFICACAO.md`](docs/ESPECIFICACAO.md).

## Rodar (desenvolvimento)

```bash
prototipo/.venv/bin/python -m pytest -q     # testes
prototipo/.venv/bin/python seed_demo.py     # demonstração ponta a ponta
```

## Estrutura

```
app/        base + API: schema.sql, db.py, catalogo.py, prazos.py, pendencias.py, visao.py, api.py
web/        dashboard React+Vite (5 telas)
tests/      testes das regras legais, do banco, da visao e da API
prototipo/  pipeline de IA (PDF → markdown → Qwen)
docs/       especificação técnica
```
