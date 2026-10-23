import { NavLink, Outlet } from "react-router-dom";

const LINKS = [
  { to: "/", rotulo: "Início", fim: true },
  { to: "/casos", rotulo: "Casos" },
  { to: "/conferencia", rotulo: "Conferência" },
  { to: "/busca", rotulo: "Busca" },
];

export default function App() {
  return (
    <div className="layout">
      <aside className="menu">
        <h1 className="marca">DTE</h1>
        <nav>
          {LINKS.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.fim}>
              {l.rotulo}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="conteudo">
        <Outlet />
      </main>
    </div>
  );
}
