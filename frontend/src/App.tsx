import { Route, Routes } from "react-router-dom";

import Offline from "./pages/Offline";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Offline />} />
      <Route path="/offline" element={<Offline />} />
      <Route path="*" element={<Offline />} />
    </Routes>
  );
}
