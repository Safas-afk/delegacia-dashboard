# Sistema de Acompanhamento de Inquéritos (DTE)

Dashboard **local e offline** para a Delegacia de Tóxicos e Entorpecentes de Vitória da
Conquista/BA. Lê os PDFs dos casos, extrai informações com **IA local (offline)**, e mostra
prazos, urgências e o que falta em cada inquérito — tudo rodando na máquina, sem internet,
com os dados cifrados.

> Dados sensíveis / segredo de justiça. Segurança é prioridade. Nada sai da máquina.

## Estado

- Protótipo de IA validado (PDF → markdown → Qwen local, extração correta em CPU).
- Base de dados pronta: banco cifrado (SQLCipher) + catálogo de tipificações + motores de
  prazo e pendência baseados na lei. 18 testes passando.
- Backend e interface: a fazer.

Veja a especificação completa em [`docs/ESPECIFICACAO.md`](docs/ESPECIFICACAO.md).

## Rodar (desenvolvimento)

```bash
prototipo/.venv/bin/python -m pytest -q     # testes
prototipo/.venv/bin/python seed_demo.py     # demonstração ponta a ponta
```

## Estrutura

```
app/        base: schema.sql, db.py, catalogo.py, prazos.py, pendencias.py
tests/      testes das regras legais e do banco cifrado
prototipo/  pipeline de IA (PDF → markdown → Qwen)
docs/       especificação técnica
```
