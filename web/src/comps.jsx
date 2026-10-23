// Pecinhas reutilizadas pelas telas.

export function Estado({ carregando, erro }) {
  if (carregando) return <p className="aviso">Carregando…</p>;
  if (erro) return <p className="aviso erro">Erro: {erro}</p>;
  return null;
}

// bolinha do semaforo do prazo
export function Semaforo({ prazo }) {
  if (!prazo) return <span className="pastilha cinza">sem prazo</span>;
  const texto = prazo.vencido
    ? `vencido há ${-prazo.dias_restantes}d`
    : `${prazo.dias_restantes}d`;
  return <span className={`pastilha ${prazo.cor}`}>{texto}</span>;
}

// etiqueta de severidade da pendencia/alerta
export function Severidade({ nivel }) {
  return <span className={`sev ${nivel}`}>{nivel}</span>;
}
