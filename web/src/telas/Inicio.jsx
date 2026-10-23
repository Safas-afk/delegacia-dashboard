import { Link } from "react-router-dom";
import { api } from "../api.js";
import { useFetch } from "../useFetch.js";
import { Estado, Severidade } from "../comps.jsx";

export default function Inicio() {
  const { dados, carregando, erro } = useFetch(() => api.painel());
  if (!dados) return <Estado carregando={carregando} erro={erro} />;

  const { contadores, semaforo, alertas } = dados;
  return (
    <div>
      <h2>Painel de urgência</h2>

      <div className="cartoes">
        <div className="cartao">
          <span className="numero">{contadores.casos}</span>casos
        </div>
        <div className="cartao">
          <span className="numero">{contadores.inqueritos}</span>inquéritos
        </div>
        <div className="cartao">
          <span className="numero">{contadores.nao_conferidos}</span>a conferir
        </div>
        <div className="cartao vermelho">
          <span className="numero">{semaforo.vermelho}</span>🔴 crítico
        </div>
        <div className="cartao amarelo">
          <span className="numero">{semaforo.amarelo}</span>🟡 atenção
        </div>
        <div className="cartao verde">
          <span className="numero">{semaforo.verde}</span>🟢 no prazo
        </div>
      </div>

      <h3>Alertas críticos</h3>
      {alertas.length === 0 ? (
        <p className="aviso">Nenhum alerta crítico. 🎉</p>
      ) : (
        <ul className="alertas">
          {alertas.map((a, i) => (
            <li key={i}>
              <Severidade nivel={a.severidade} />
              <Link to={`/caso/${a.caso_id}`} className="alvo">
                {a.caso_nome}
                {a.numero_ip ? ` · IP ${a.numero_ip}` : ""}
              </Link>
              <span className="desc">{a.descricao}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
