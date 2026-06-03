import { BrowserRouter, Route, Routes } from "react-router-dom";
import { PracticePage } from "./pages/PracticePage";

export function App() {
  return (
    <BrowserRouter>
      <div style={{ maxWidth: 800, margin: "0 auto", padding: 20 }}>
        <h1>Teeline Shorthand Checker</h1>
        <Routes>
          <Route path="/" element={<PracticePage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
