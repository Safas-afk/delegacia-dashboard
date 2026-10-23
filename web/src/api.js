// Acesso as rotas de leitura do backend (FastAPI em /api).
async function get(caminho) {
  const r = await fetch(`/api${caminho}`);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export const api = {
  painel: () => get("/painel"),
  casos: () => get("/casos"),
  caso: (id) => get(`/casos/${id}`),
  conferencia: () => get("/conferencia"),
  busca: (q) => get(`/busca?q=${encodeURIComponent(q)}`),
};
