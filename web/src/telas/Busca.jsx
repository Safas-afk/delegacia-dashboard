import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";

export default function Busca() {
  const [termo, setTermo] = useState("");
  const [res, setRes] = useState(null);
  const [erro, setErro] = useState(null);

  async function buscar(e) {
    e.preventDefault();
    if (!termo.trim()) return;
    setErro(null);
    try {
      setRes(await api.busca(termo));
    } catch (err) {
      setErro(err.message);
    }
  }

  return (
    <div>
      <h2>Busca</h2>
      <form onSubmit={buscar} className="form-busca">
        <input
          value={termo}
          onChange={(e) => setTermo(e.target.value)}
          placeholder="caso, nº do IP ou pessoa"
          autoFocus
        />
        <button type="submit">Buscar</button>
      </form>
      {erro && <p className="aviso erro">Erro: {erro}</p>}

      {res && (
        <div className="resultados">
          <h3>Casos ({res.casos.length})</h3>
          <ul>
            {res.casos.map((c) => (
              <li key={c.id}>
                <Link to={`/caso/${c.id}`}>{c.nome}</Link> — {c.status}
              </li>
            ))}
          </ul>

          <h3>Inquéritos ({res.inqueritos.length})</h3>
          <ul>
            {res.inqueritos.map((i) => (
              <li key={i.id}>
                <Link to={`/caso/${i.caso_id}`}>IP {i.numero_oficial}</Link> —{" "}
                {i.delegado_responsavel}
              </li>
            ))}
          </ul>

          <h3>Pessoas ({res.pessoas.length})</h3>
          <ul>
            {res.pessoas.map((p) => (
              <li key={p.id}>
                <Link to={`/caso/${p.caso_id}`}>{p.nome}</Link> — {p.papel}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
