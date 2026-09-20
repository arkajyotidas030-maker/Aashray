import { Navigate, Outlet, useLocation } from "react-router-dom";
import { getRole, getToken } from "./api";

export function RequireAuth({ role }: { role?: "citizen" | "responder" }) {
  const loc = useLocation();
  const token = getToken();
  const have = getRole();
  if (!token) return <Navigate to="/" replace state={{ from: loc }} />;
  if (role && have !== role) return <Navigate to="/" replace />;
  return <Outlet />;
}
