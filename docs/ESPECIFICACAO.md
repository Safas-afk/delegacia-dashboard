# Especificação — Sistema de Acompanhamento de Inquéritos (DTE)

> Dashboard local e offline para a Delegacia de Tóxicos e Entorpecentes de Vitória
> da Conquista/BA. Lê documentos (PDF) dos casos, extrai informações com IA local,
> e mostra prazos, urgências e o que falta em cada inquérito.
>
> Documento vivo. Última atualização: 2026-10-22.

---

## 1. Objetivo

O delegado chega na delegacia, abre o programa e vê de imediato: quais casos estão em
andamento, quais prazos estão vencendo, o que é mais urgente e o que falta em cada caso
para dar andamento. As informações são montadas automaticamente a partir dos PDFs dos
procedimentos, com a IA extraindo os dados e o delegado conferindo.

Um **caso** pode gerar vários **inquéritos**, e um inquérito pode apurar vários **crimes**
(ex.: num mandado de busca, acha droga = art. 33; acha arma = art. 16; 2+ pessoas =
associação, art. 35). O sistema modela essa evolução.

## 2. Requisitos duros

| # | Requisito | Motivo |
|---|-----------|--------|
| 1 | **100% local e offline** | Dados sensíveis, segredo de justiça. Nada pode sair da máquina. |
| 2 | **Segurança em primeiro lugar** | Criptografia, controle de acesso, trilha de auditoria. |
| 3 | **Roda em Windows** | PC da delegacia (Windows 11 Pro). |
| 4 | **IA pequena rodando em CPU** | Sem GPU dedicada; modelo leve quantizado. |
| 5 | **IA é assistente, não verdade** | Modelo pequeno erra; é processo criminal. O delegado confere tudo. |

### Hardware-alvo (PC da delegacia)
Lenovo, Intel Core **i3-10100T** (4C/8T, baixo consumo), **16 GB RAM** (~6 GB livres em uso),
GPU **integrada Intel UHD 630** (sem NVIDIA), Windows 11 Pro 64-bit. Perfil **CPU-only, modesto**.

## 3. Arquitetura e stack

- **Linguagem:** Python (melhor ecossistema para IA local, PDF, OCR).
- **Interface:** aplicação **web local** servida só em `127.0.0.1` (backend FastAPI + front no
  navegador). Dashboard rico, offline, sem expor nenhuma porta de rede.
- **Banco:** **SQLite + SQLCipher** (AES-256), arquivo único, cifrado em repouso.
- **IA:** modelo **Qwen** pequeno quantizado (GGUF) via **llama.cpp** (binário portátil, offline).
- **Empacotamento:** PyInstaller → executável; build do `.exe` via GitHub Actions (runner Windows).

Princípio central: **as ferramentas determinísticas fazem o peso** (ler PDF, OCR, converter
para markdown, regex para datas/números) e **a IA só faz o que exige entender texto**
(classificar, resumir). Mais rápido e mais preciso em CPU fraca.

## 4. Modelo de dados

Hierarquia: `caso → inquérito → {crimes, pessoas, documentos, prazos, pendências}`.

Tabelas (ver `app/schema.sql`):

- **caso** — operação/ocorrência raiz; nome, data, origem, status, resumo, flag de segredo de justiça.
- **inquerito** — nº oficial, delegado, data de instauração, situação prisional (preso/solto),
  lei de prazo aplicável (drogas/cpp), prorrogação, status (em andamento/relatado/arquivado/na justiça).
- **crime** — tipificação (código do catálogo), descrição, data do fato. Vários por inquérito.
- **pessoa** — nome, papel (investigado/preso/testemunha/vítima/condutor), situação.
- **documento** — nome do PDF, caminho, tipo, hash, texto extraído (markdown), status da extração.
- **prazo** — prazos avulsos (laudo, resposta de ofício). O prazo principal do IP é **calculado**.
- **pendencia** — "o que falta"; descrição, categoria, severidade, aberta/resolvida, origem (regra/manual).
- **auditoria** — trilha de quem fez o quê e quando (boa prática / LGPD).

## 5. Base legal (prazos e regras automáticas)

Toda regra abaixo foi pesquisada na fonte e vira cálculo/alerta no sistema — **não é chute**.

### Prazo do inquérito (`app/prazos.py`)

| Lei | Situação | Prazo base | Prorrogação |
|-----|----------|------------|-------------|
| **Lei de Drogas 11.343/2006, art. 51** | preso | 30 dias | juiz pode duplicar → 60 |
| Lei de Drogas, art. 51 | solto | 90 dias | juiz pode duplicar → 180 |
| **CPP, art. 10** (arma, orcrim) | preso | 10 dias | — |
| CPP, art. 10 | solto | 30 dias | prorrogável |

A prorrogação é autorizada pelo **juiz**, ouvido o MP, a pedido justificado do delegado.
Semáforo: vencido ou ≤3 dias = **vermelho**; ≤15 dias = **amarelo**; senão **verde**.

### Pendências e alertas automáticos (`app/pendencias.py`)

| Regra | Fonte | Vira |
|-------|-------|------|
| Comunicar instauração ao MP em **48h** | Portaria PCBA 494/2023, art. 2 | pendência (crítica após 48h sem comunicar) |
| Autos não podem passar **90 dias** na unidade sem manifestação do juízo/MP | Portaria PCBA 494/2023, art. 4 | **alerta de risco disciplinar** (protege o delegado) |
| Materialidade do tráfico exige **laudo definitivo** | Lei 11.343/2006, art. 50 | pendência "falta laudo toxicológico definitivo" |
| Prazo do IP vencendo/vencido | ver tabela acima | alerta por semáforo |

### Catálogo de tipificações (`app/catalogo.py`)
Lista fechada (ajuda a IA a classificar): Lei de Drogas (arts. 28, 33, 34, 35, 36, 37),
Estatuto do Desarmamento 10.826/2003 (arts. 12, 14, 16, 17, 18), Organização Criminosa
12.850/2013 (art. 2). Cada item carrega a lei e qual regra de prazo se aplica.

## 6. Pipeline de documentos + IA

Processamento **sob comando** (o delegado clica "processar"); um script leve apenas detecta
PDFs novos na pasta e registra caminho + hash como "pendente".

```
pasta vigiada → detecta PDF novo (hash) → "pendente"
     │ (ao clicar "processar")
     ├─ 1. PDF → Markdown   (PyMuPDF4LLM p/ nativo; Docling+OCR p/ escaneado)
     ├─ 2. regex/layout     → dados estruturados (datas, números)
     ├─ 3. IA local (Qwen)  → classifica tipo, tipificação, resumo (saída JSON forçada)
     └─ 4. preenche o modelo com status "não conferido"
              → delegado confere/corrige (correção vira dado de treino futuro)
```

- **Modelo de IA:** Qwen ~3–4B quantizado Q4 (GGUF), rodando em CPU via llama.cpp.
- **Transcrição de áudio:** whisper.cpp (modelo base/small, pt), offline, sob demanda.
- **Sem fine-tuning no MVP:** prompt em português + exemplos + saída JSON forçada.
  Treino (QLoRA, dados anonimizados, GPU externa) só se a precisão real exigir.

### Validação (protótipo em `prototipo/`)
PDF fictício → markdown (PyMuPDF4LLM, ~1s) → Qwen2.5-3B-Instruct Q4 → JSON.
**Resultado: 9/9 campos corretos** (nº IP, delegado, segredo de justiça, 2 datas
normalizadas, preso, 3 tipificações). Tempo do Qwen: ~117s/documento em CPU — confirma o
processamento sob comando/em lote (não em tempo real).

## 7. Dashboard (telas)

1. **Início — painel de urgência** (abre já mostrando): alertas críticos (prazo vencendo,
   90 dias/risco disciplinar, 48h MP), contadores, casos por semáforo 🔴🟡🟢.
2. **Lista de casos/inquéritos** — tabela filtrável e ordenável por prazo.
3. **Detalhe do caso** — inquéritos, crimes, pessoas, documentos, linha do tempo e o bloco
   **"O que falta"** (pendências automáticas); botão "processar documentos".
4. **Conferência da IA** — mostra o trecho de origem e o campo sugerido; delegado aprova/corrige.
5. **Busca** — casos, pessoas, nº de IP, documentos.

Nada vindo da IA aparece como fato até ser conferido.

## 8. Segurança e implantação

- **Offline real:** backend só em `127.0.0.1`, zero telemetria; regra de firewall bloqueando o `.exe`.
- **Cripto em repouso:** banco SQLCipher AES-256, chave derivada da senha (login). Markdown,
  transcrições e dados ficam **dentro** do banco cifrado; temporários são apagados.
- **Acesso:** senha forte (Argon2) no MVP; **auto-bloqueio por inatividade**. YubiKey/FIDO2 como
  2º fator fica para fase posterior.
- **Trilha de auditoria:** quem aprovou o quê e quando.
- **Implantação — instalado no PC da delegacia:** o programa (app + modelos + banco) fica instalado
  na máquina de trabalho. O banco SQLCipher cifrado protege os dados em repouso (máquina
  desligada/roubada = arquivo ilegível). **Backup** do banco cifrado (continua cifrado) num HD/PC
  pessoal do delegado.
  > Decisão do delegado (2026-10-22): roda só no PC do trabalho. O drive portátil criptografado foi
  > avaliado e **descartado** do escopo.
- **Legal:** dado de investigação penal tem regime próprio (fora da LGPD comum, art. 4º III da
  Lei 13.709), mas valem o devido processo e o segredo de justiça; cripto + acesso + auditoria +
  minimização atendem as boas práticas esperadas (art. 44).

## 9. Empacotamento (.exe) e teste no Linux

- App é Python → **roda nativo no Linux** durante todo o desenvolvimento (testa 100% da lógica).
- O `.exe` Windows é gerado via **GitHub Actions (runner Windows)** — PyInstaller não faz
  cross-compile. Opcional: rodar o `.exe` pronto no **Wine** para um smoke test.
- Binários de llama.cpp/whisper.cpp e o GGUF são por sistema (Linux no dev, Windows na instalação
  final do PC); o código Python é o mesmo.

## 10. Estado atual e roadmap

### Feito (2026-10-22)
- [x] Protótipo de IA validado (PDF → markdown → Qwen, 9/9 campos).
- [x] Base de dados: schema cifrado, catálogo, motor de prazos, motor de pendências.
- [x] Integração pipeline→banco (`app/ingestao.py`): extrai do PDF e grava como
      proposta não conferida, casando pelo nº do IP; mapeamento determinístico de
      tipificações. Validado com o Qwen real (`ingesta_demo.py`).
- [x] 24 testes passando; demos ponta a ponta (`seed_demo.py`, `ingesta_demo.py`).

### A fazer
- [ ] Backend FastAPI + API das telas.
- [ ] Dashboard (5 telas).
- [ ] Login + auto-bloqueio + senha→chave do banco.
- [ ] Caminho OCR para PDFs escaneados (Docling).
- [ ] Empacotamento: instalador/`.exe` para o PC da delegacia (build via GitHub Actions).
- [ ] Coletar com o delegado: tipos reais de documento e campos mais usados.

## 11. Como rodar (desenvolvimento)

```bash
cd ~/projetos/delegacia-dashboard
# ambiente (reusa o venv do prototipo, que ja tem as libs)
prototipo/.venv/bin/python -m pytest -q        # roda os testes (24)
prototipo/.venv/bin/python seed_demo.py        # demo das regras (sem IA)
prototipo/.venv/bin/python ingesta_demo.py     # integracao real PDF->Qwen->banco (~2min)
# protótipo de IA isolado (precisa do modelo em prototipo/modelos/*.gguf)
cd prototipo && .venv/bin/python pipeline.py
```

### Estrutura
```
delegacia-dashboard/
├─ app/            base: schema.sql, db.py, catalogo.py, prazos.py, pendencias.py
├─ tests/          testes das regras legais e do banco cifrado
├─ prototipo/      pipeline de IA validado (PDF→markdown→Qwen)
├─ docs/           esta especificação
└─ seed_demo.py    demonstração ponta a ponta
```
