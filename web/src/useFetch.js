import { useEffect, useState } from "react";

// Hook simples: roda `fn` e devolve {dados, carregando, erro}.
// `deps` dispara nova busca (ex: id do caso, termo de busca).
export function useFetch(fn, deps = []) {
  const [dados, setDados] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    let vivo = true;
    setCarregando(true);
    setErro(null);
    fn()
      .then((d) => vivo && setDados(d))
      .catch((e) => vivo && setErro(e.message))
      .finally(() => vivo && setCarregando(false));
    return () => {
      vivo = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { dados, carregando, erro };
}
