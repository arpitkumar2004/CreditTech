import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import SakhiEntry from "./pages/SakhiEntry";
import BorrowerView from "./pages/BorrowerView";
import ConsentView from "./pages/ConsentView";
import Applications from "./pages/officer/Applications";
import ApplicationDetail from "./pages/officer/ApplicationDetail";
import Fairness from "./pages/officer/Fairness";
import ModelRegistry from "./pages/officer/ModelRegistry";
import Grievances from "./pages/officer/Grievances";
import NotFound from "./pages/NotFound";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="applications" element={<Applications />} />
        <Route path="applications/new" element={<SakhiEntry />} />
        <Route path="applications/:id" element={<ApplicationDetail />} />
        <Route path="borrowers" element={<BorrowerView />} />
        <Route path="consent" element={<ConsentView />} />
        <Route path="fairness" element={<Fairness />} />
        <Route path="models" element={<ModelRegistry />} />
        <Route path="grievances" element={<Grievances />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
