const TOKEN_KEY = "aashray.token";
const ROLE_KEY = "aashray.role";

export const apiBase = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}
export function getRole() {
  return localStorage.getItem(ROLE_KEY);
}
export function setSession(token: string, role: string) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(ROLE_KEY, role);
}
export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ROLE_KEY);
}

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(init.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
    ...(init.headers as Record<string, string> | undefined),
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${apiBase}/api/v1${path}`, { ...init, headers });
  if (res.status === 401) {
    clearSession();
    throw new Error("auth");
  }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) =>
    req<{ access_token: string; role: string; email: string; user_id: number }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  health: () => req<{ db: string; llm: string; routing: string }>("/health"),
  opsSnapshot: () => req<import("./types").Snapshot>("/ops/snapshot"),
  citizenSnapshot: () => req<import("./types").CitizenSnapshot>("/citizen/snapshot"),
  tick: () => req<{ tick: number; rainfall_index: number }>("/demo/tick", { method: "POST" }),
  evidence: (body: Record<string, unknown>) =>
    req<{ evidence_id: number; incident_code: string; cluster_confidence: number; confidence_label: string }>(
      "/evidence",
      { method: "POST", body: JSON.stringify(body) },
    ),
  uploadMedia: (evidenceId: number, file: File) => {
    const body = new FormData();
    body.append("file", file);
    return req<{ evidence_id: number; incident_code: string; cluster_confidence: number }>(
      `/evidence/${evidenceId}/media`,
      { method: "POST", body },
    );
  },
  checkin: (body: Record<string, unknown>) =>
    req("/checkins", { method: "POST", body: JSON.stringify(body) }),
  incident: (id: number) => req<import("./types").IncidentDetail>(`/incidents/${id}`),
  assign: (id: number) => req(`/ops/incidents/${id}/assign`, { method: "POST" }),
  dismiss: (id: number) => req(`/ops/incidents/${id}/dismiss`, { method: "POST" }),
  routes: () => req<{ routes: import("./types").RouteScore[] }>("/routes/safest"),
};
