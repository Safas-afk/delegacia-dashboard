import { useEffect, useState } from "react";
import { api } from "../api.js";
import { useFetch } from "../useFetch.js";
import { Estado } from "../comps.jsx";

// campos editaveis por tipo (bate com a whitelist do backend)
const CAMPOS = {
  inquerito: [
    { campo: "numero_oficial", rotulo: "Nº do IP" },
    { campo: "delegado_responsavel", rotulo: "Delegado" },
    { campo: "data_instauracao", rotulo: "Instauração" },
    { campo: "situacao_prisional", rotulo: "Situação", opcoes: ["preso", "solto"] },
    { campo: "lei_prazo", rotulo: "Lei do prazo", opcoes: ["drogas", "cpp"] },
    {
      campo: "status",
      rotulo: "Status",
      opcoes: ["em_andamento", "relatado", "arquivado", "na_justica"],
    },
  ],
  pessoa: [
    { campo: "nome", rotulo: "Nome" },
    {
      campo: "papel",
      rotulo: "Papel",
      opcoes: ["investigado", "preso", "testemunha", "vitima", "condutor"],
    },
    { campo: "situacao", rotulo: "Situação" },
  ],
  // crime tem um caso especial (dropdown do catalogo) tratado no componente
  crime: [{ campo: "data_fato", rotulo: "Data do fato" }],
};

function Campo({ spec, valor, onChange }) {
  return (
    <label className="campo">
      <span>{spec.rotulo}</span>
      {spec.opcoes ? (
        <select value={valor || ""} onChange={(e) => onChange(e.target.value)}>
          {spec.opcoes.map((o) => (
            <option key={o} value={o}>
              {o}
            </option>
          ))}
        </select>
      ) : (
        <input value={valor || ""} onChange={(e) => onChange(e.target.value)} />
      )}
    </label>
  );
}

function ItemConf({ tipo, item, catalogo, aoMudar }) {
  const [edit, setEdit] = useState(item);
  const [ocupado, setOcupado] = useState(false);
  const [erro, setErro] = useState(null);

  function setCampo(campo, valor) {
    setEdit((e) => ({ ...e, [campo]: valor }));
  }

  async function acao(fn) {
    setOcupado(true);
    setErro(null);
    try {
      await fn();
      aoMudar();
    } catch (e) {
      setErro(e.message);
      setOcupado(false);
    }
  }

  const campos = CAMPOS[tipo];
  return (
    <div className="item-conf">
      <div className="campos-grade">
        {tipo === "crime" && (
          <label className="campo">
            <span>Tipificação</span>
            <select
              value={edit.tipificacao_codigo || ""}
              onChange={(e) => setCampo("tipificacao_codigo", e.target.value)}
            >
              <option value="">—</option>
              {catalogo.map((c) => (
                <option key={c.codigo} value={c.codigo}>
                  {c.rotulo}
                </option>
              ))}
            </select>
          </label>
        )}
        {campos.map((spec) => (
          <Campo
            key={spec.campo}
            spec={spec}
            valor={edit[spec.campo]}
            onChange={(v) => setCampo(spec.campo, v)}
          />
        ))}
      </div>
      {erro && <p className="aviso erro">Erro: {erro}</p>}
      <div className="acoes">
        <button
          disabled={ocupado}
          onClick={() => acao(() => api.conferir(tipo, item.id, campos_editados(item, edit, tipo)))}
        >
          Salvar
        </button>
        <button
          className="rejeitar"
          disabled={ocupado}
          onClick={() => acao(() => api.rejeitar(tipo, item.id))}
        >
          Rejeitar
        </button>
      </div>
    </div>
  );
}

// manda so o que mudou (mais o tipificacao_codigo do crime)
function campos_editados(original, edit, tipo) {
  const campos = {};
  const chaves = CAMPOS[tipo].map((c) => c.campo);
  if (tipo === "crime") chaves.push("tipificacao_codigo");
  for (const k of chaves) {
    if (edit[k] !== original[k]) campos[k] = edit[k];
  }
  return campos;
}

function Grupo({ titulo, tipo, itens, catalogo, aoMudar, rotulo }) {
  if (!itens.length) return null;
  return (
    <section>
      <h3>
        {titulo} ({itens.length})
      </h3>
      {itens.map((it) => (
        <div key={it.id} className="bloco-item">
          <p className="rotulo-item">{rotulo(it)}</p>
          <ItemConf tipo={tipo} item={it} catalogo={catalogo} aoMudar={aoMudar} />
        </div>
      ))}
    </section>
  );
}

export default function Conferencia() {
  const [versao, setVersao] = useState(0);
  const recarregar = () => setVersao((v) => v + 1);
  const { dados, carregando, erro } = useFetch(() => api.conferencia(), [versao]);
  const [catalogo, setCatalogo] = useState([]);

  useEffect(() => {
    api.catalogo().then(setCatalogo).catch(() => setCatalogo([]));
  }, []);

  if (!dados) return <Estado carregando={carregando} erro={erro} />;

  const { inqueritos, crimes, pessoas, documentos } = dados;
  const vazio =
    !inqueritos.length && !crimes.length && !pessoas.length;

  return (
    <div>
      <h2>Conferência da IA</h2>
      <p className="aviso">
        Sugestões da IA aguardando conferência. Edite se precisar e clique Salvar
        (aprova), ou Rejeitar (apaga). Nada vira fato até ser conferido.
      </p>
      {vazio && <p className="aviso">Nada aguardando conferência. 🎉</p>}

      <Grupo
        titulo="Inquéritos"
        tipo="inquerito"
        itens={inqueritos}
        catalogo={catalogo}
        aoMudar={recarregar}
        rotulo={(i) => `IP ${i.numero_oficial || "(sem número)"}`}
      />
      <Grupo
        titulo="Crimes"
        tipo="crime"
        itens={crimes}
        catalogo={catalogo}
        aoMudar={recarregar}
        rotulo={(c) => c.descricao || c.tipificacao_codigo || "(crime)"}
      />
      <Grupo
        titulo="Pessoas"
        tipo="pessoa"
        itens={pessoas}
        catalogo={catalogo}
        aoMudar={recarregar}
        rotulo={(p) => p.nome}
      />

      {documentos.length > 0 && (
        <section>
          <h3>Documentos processados (trecho de origem)</h3>
          {documentos.map((d) => (
            <details key={d.id} className="doc">
              <summary>
                {d.nome_arquivo} — {d.tipo || "?"}
              </summary>
              <pre className="json">{d.extracao_json || "(sem JSON)"}</pre>
            </details>
          ))}
        </section>
      )}
    </div>
  );
}
