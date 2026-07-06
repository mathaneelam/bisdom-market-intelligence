import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Signals from "./pages/Signals";
import Sources from "./pages/Sources";
import Competitors from "./pages/Competitors";
import TradeShows from "./pages/TradeShows";
import ContentBank from "./pages/ContentBank";
import { SavedItemsProvider } from "./lib/SavedItemsContext";

export default function App() {
  return (
    <BrowserRouter>
      <SavedItemsProvider>
        <Layout>
          <Routes>
          <Route path="/"             element={<Dashboard />}   />
          <Route path="/signals"      element={<Signals />}     />
          <Route path="/sources"      element={<Sources />}     />
          <Route path="/competitors"  element={<Competitors />} />
          <Route path="/trade-shows"  element={<TradeShows />}  />
          <Route path="/content-bank" element={<ContentBank />} />
        </Routes>
        </Layout>
      </SavedItemsProvider>
    </BrowserRouter>
  );
}
