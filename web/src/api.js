// Acesso as rotas de leitura do backend (FastAPI em /api).
async function get(caminho) {
  const r = await fetch(`/api${caminho}`);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

async function enviar(metodo, caminho, corpo) {
  const r = await fetch(`/api${caminho}`, {
    method: metodo,
    headers: corpo ? { "Content-Type": "application/json" } : undefined,
    body: corpo ? JSON.stringify(corpo) : undefined,
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export const api = {
  painel: () => get("/painel"),
  casos: () => get("/casos"),
  caso: (id) => get(`/casos/${id}`),
  conferencia: () => get("/conferencia"),
  busca: (q) => get(`/busca?q=${encodeURIComponent(q)}`),
  catalogo: () => get("/catalogo"),
  conferir: (tipo, id, campos) => enviar("PUT", `/conferencia/${tipo}/${id}`, campos),
  rejeitar: (tipo, id) => enviar("DELETE", `/conferencia/${tipo}/${id}`),
};
