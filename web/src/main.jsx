import React from "react";
import { createRoot } from "react-dom/client";
import { HashRouter, Routes, Route } from "react-router-dom";

import App from "./App.jsx";
import Inicio from "./telas/Inicio.jsx";
import Lista from "./telas/Lista.jsx";
import Detalhe from "./telas/Detalhe.jsx";
import Conferencia from "./telas/Conferencia.jsx";
import Busca from "./telas/Busca.jsx";
import "./estilo.css";

createRoot(document.getElementById("root")).render(
  <HashRouter>
    <Routes>
      <Route path="/" element={<App />}>
        <Route index element={<Inicio />} />
        <Route path="casos" element={<Lista />} />
        <Route path="caso/:id" element={<Detalhe />} />
        <Route path="conferencia" element={<Conferencia />} />
        <Route path="busca" element={<Busca />} />
      </Route>
    </Routes>
  </HashRouter>
);
