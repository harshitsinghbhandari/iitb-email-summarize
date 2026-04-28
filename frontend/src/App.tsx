import { Route, Routes } from "react-router-dom";

import EmailDetail from "./pages/EmailDetail";
import Inbox from "./pages/Inbox";
import Offline from "./pages/Offline";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Inbox />} />
      <Route path="/email/:uid" element={<EmailDetail />} />
      <Route path="/offline" element={<Offline />} />
      <Route path="*" element={<Inbox />} />
    </Routes>
  );
}
