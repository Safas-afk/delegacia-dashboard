import { Link } from "react-router-dom";
import { api } from "../api.js";
import { useFetch } from "../useFetch.js";
import { Estado, Semaforo } from "../comps.jsx";

export default function Lista() {
  // o backend ja devolve ordenado por prazo (mais urgente primeiro)
  const { dados, carregando, erro } = useFetch(() => api.casos());
  if (!dados) return <Estado carregando={carregando} erro={erro} />;

  return (
    <div>
      <h2>Casos</h2>
      {dados.length === 0 ? (
        <p className="aviso">Nenhum caso cadastrado.</p>
      ) : (
        <table className="tabela">
          <thead>
            <tr>
              <th>Prazo</th>
              <th>Caso</th>
              <th>Inquéritos</th>
              <th>Pendências</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {dados.map((c) => (
              <tr key={c.id}>
                <td>
                  <Semaforo prazo={c.prazo} />
                </td>
                <td>
                  <Link to={`/caso/${c.id}`}>
                    {c.nome}
                    {c.segredo_justica ? " 🔒" : ""}
                  </Link>
                </td>
                <td className="num">{c.qtd_inqueritos}</td>
                <td className="num">{c.qtd_pendencias}</td>
                <td>{c.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
