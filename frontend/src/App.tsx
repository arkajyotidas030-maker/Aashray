import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { CitizenPage } from "./CitizenPage";
import { I18nProvider } from "./I18nProvider";
import { LoginPage } from "./LoginPage";
import { OpsPage } from "./OpsPage";
import { RequireAuth } from "./RequireAuth";

const qc = new QueryClient();

export function App() {
  return (
    <QueryClientProvider client={qc}>
      <I18nProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LoginPage />} />
            <Route element={<RequireAuth role="citizen" />}>
              <Route path="/c" element={<CitizenPage />} />
            </Route>
            <Route element={<RequireAuth role="responder" />}>
              <Route path="/ops" element={<OpsPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </I18nProvider>
    </QueryClientProvider>
  );
}
