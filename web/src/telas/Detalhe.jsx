import { useParams, Link } from "react-router-dom";
import { api } from "../api.js";
import { useFetch } from "../useFetch.js";
import { Estado, Semaforo, Severidade } from "../comps.jsx";

function Inquerito({ bloco }) {
  const { inquerito, prazo, crimes, pessoas, documentos, pendencias } = bloco;
  return (
    <section className="inq">
      <div className="inq-topo">
        <h3>
          IP {inquerito.numero_oficial || "(sem número)"}{" "}
          {inquerito.conferido ? "" : <span className="tag-ia">sugestão IA</span>}
        </h3>
        <Semaforo prazo={prazo} />
      </div>
      <p className="meta">
        {inquerito.situacao_prisional?.toUpperCase()} · instaurado{" "}
        {inquerito.data_instauracao} · lei {inquerito.lei_prazo} · limite{" "}
        {prazo.data_limite} · {inquerito.delegado_responsavel || "—"}
      </p>

      <div className="colunas">
        <div>
          <h4>Crimes</h4>
          <ul>
            {crimes.map((c) => (
              <li key={c.id}>
                {c.catalogo
                  ? `${c.catalogo.artigo} — ${c.catalogo.descricao} (${c.catalogo.lei})`
                  : c.descricao || c.tipificacao_codigo}
              </li>
            ))}
          </ul>

          <h4>Pessoas</h4>
          <ul>
            {pessoas.map((p) => (
              <li key={p.id}>
                {p.nome} — {p.papel}
                {p.situacao ? ` (${p.situacao})` : ""}
              </li>
            ))}
          </ul>

          <h4>Documentos</h4>
          <ul>
            {documentos.map((d) => (
              <li key={d.id}>
                {d.nome_arquivo} — {d.tipo || "?"} [{d.status_extracao}]
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h4>O que falta</h4>
          {pendencias.length === 0 ? (
            <p className="aviso">Nada pendente.</p>
          ) : (
            <ul className="pendencias">
              {pendencias.map((p, i) => (
                <li key={i}>
                  <Severidade nivel={p.severidade} />
                  {p.descricao}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}

export default function Detalhe() {
  const { id } = useParams();
  const { dados, carregando, erro } = useFetch(() => api.caso(id), [id]);
  if (!dados) return <Estado carregando={carregando} erro={erro} />;

  return (
    <div>
      <Link to="/casos" className="voltar">
        ← casos
      </Link>
      <h2>
        {dados.nome} {dados.segredo_justica ? "🔒" : ""}
      </h2>
      {dados.resumo && <p className="resumo">{dados.resumo}</p>}
      {dados.inqueritos.map((b) => (
        <Inquerito key={b.inquerito.id} bloco={b} />
      ))}
    </div>
  );
}
