import { api } from "../api.js";
import { useFetch } from "../useFetch.js";
import { Estado } from "../comps.jsx";

// Leitura nesta etapa: mostra o que a IA sugeriu e aguarda conferencia.
// Aprovar/corrigir vem em ciclo proprio (escrita).
export default function Conferencia() {
  const { dados, carregando, erro } = useFetch(() => api.conferencia());
  if (!dados) return <Estado carregando={carregando} erro={erro} />;

  const { inqueritos, crimes, pessoas, documentos } = dados;
  const vazio =
    !inqueritos.length && !crimes.length && !pessoas.length && !documentos.length;

  return (
    <div>
      <h2>Conferência da IA</h2>
      <p className="aviso">
        Itens sugeridos pela IA, aguardando conferência. Nada vira fato até ser
        conferido. (Aprovar/corrigir chega na próxima etapa.)
      </p>
      {vazio && <p className="aviso">Nada aguardando conferência.</p>}

      {inqueritos.length > 0 && (
        <>
          <h3>Inquéritos</h3>
          <ul>
            {inqueritos.map((i) => (
              <li key={i.id}>
                IP {i.numero_oficial || "(sem número)"} — {i.delegado_responsavel}
              </li>
            ))}
          </ul>
        </>
      )}

      {documentos.length > 0 && (
        <>
          <h3>Documentos processados (trecho de origem)</h3>
          {documentos.map((d) => (
            <details key={d.id} className="doc">
              <summary>
                {d.nome_arquivo} — {d.tipo || "?"}
              </summary>
              <pre className="json">{d.extracao_json || "(sem JSON)"}</pre>
            </details>
          ))}
        </>
      )}
    </div>
  );
}
