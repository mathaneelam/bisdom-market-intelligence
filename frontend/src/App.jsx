import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Signals from "./pages/Signals";
import Competitors from "./pages/Competitors";
import TradeShows from "./pages/TradeShows";

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/"            element={<Dashboard />}  />
          <Route path="/signals"     element={<Signals />}    />
          <Route path="/competitors" element={<Competitors />}/>
          <Route path="/trade-shows" element={<TradeShows />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
