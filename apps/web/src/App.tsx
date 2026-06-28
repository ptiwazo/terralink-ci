import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import CataloguePage from "./pages/CataloguePage";
import CommandesPage from "./pages/CommandesPage";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import OffresPage from "./pages/OffresPage";
import RegisterPage from "./pages/RegisterPage";
import AcheteurPage from "./pages/AcheteurPage";
import TransporteurPage from "./pages/TransporteurPage";
import TransporteursAdminPage from "./pages/TransporteursAdminPage";
import TresoreriePage from "./pages/TresoreriePage";

function Protege({ children }: { children: React.ReactNode }) {
  return <ProtectedRoute>{children}</ProtectedRoute>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/connexion" element={<LoginPage />} />
      <Route path="/inscription" element={<RegisterPage />} />
      <Route path="/" element={<Protege><DashboardPage /></Protege>} />
      <Route path="/offres" element={<Protege><OffresPage /></Protege>} />
      <Route path="/catalogue" element={<Protege><CataloguePage /></Protege>} />
      <Route path="/commandes" element={<Protege><CommandesPage /></Protege>} />
      <Route path="/transporteur" element={<Protege><TransporteurPage /></Protege>} />
      <Route path="/transporteurs" element={<Protege><TransporteursAdminPage /></Protege>} />
      <Route path="/acheteur" element={<Protege><AcheteurPage /></Protege>} />
      <Route path="/tresorerie" element={<Protege><TresoreriePage /></Protege>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
