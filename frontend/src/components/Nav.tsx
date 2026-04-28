import { NavLink } from "react-router-dom";

export function Nav() {
  return (
    <nav className="nav">
      <NavLink to="/" end>
        Inbox
      </NavLink>
      <NavLink to="/offline">Offline fixture</NavLink>
    </nav>
  );
}
