export type Role = "citizen" | "responder";

export type Snapshot = {
  tick: number;
  rainfall_index: number;
  playing: boolean;
  as_of: string;
  health: { db: string; llm: string; routing: string };
  incidents: Incident[];
  evidence: Evidence[];
  layers: Record<string, FeatureCollection>;
  visibility: {
    coverage_pct: number;
    unconfirmed_safety_status: number;
    simulated_registered_users: number;
    note: string;
  };
  priority_weights: Record<string, number>;
  priority_queue: {
    incident_code: string;
    score: number;
    breakdown: Record<string, number>;
    nearest_resource?: string | null;
    reason?: string | null;
  }[];
  isolation: { isolated_settlements: string[]; cascade: string | null };
  sitrep: string | null;
  resources: Record<string, unknown>[];
  routes: RouteScore[];
  alerts: { user_email: string; incident_code: string; zone_level: string; t: string }[];
  corroborated: Record<string, boolean>;
};

export type Incident = {
  id: number;
  code: string;
  confidence: number;
  status: string;
  isolated: boolean;
  disagreement: boolean;
  sitrep: string | null;
  member_evidence_ids: number[];
  provenance: { source: string; as_of: string };
};

export type Evidence = {
  id: number;
  kind: string;
  lat: number;
  lon: number;
  t: string;
  raw_text: string | null;
  emergency_type: string | null;
  people_count: number | null;
  severity: number | null;
  trapped: boolean;
  injury: boolean;
  source: string;
  as_of: string;
  incident_code: string | null;
  has_media: boolean;
  contribution_score?: number;
};

export type FeatureCollection = {
  type: "FeatureCollection";
  features: {
    type: "Feature";
    geometry: { type: string; coordinates: unknown } | null;
    properties: Record<string, unknown>;
  }[];
  provenance: { source: string; as_of: string };
};

export type RouteScore = {
  id: string;
  label: string;
  duration_min: number;
  status: string;
  reason?: string | null;
  coordinates: [number, number][];
  source?: string;
};

export type CitizenSnapshot = {
  tick: number;
  rainfall_index: number;
  as_of: string;
  zone_level: string | null;
  zone_message: string | null;
  safest_route: RouteScore | null;
  rejected_routes: RouteScore[];
  shelters: { id: string; name: string; kind: string; lat: number; lon: number }[];
  isolation: { isolated_settlements: string[]; cascade: string | null };
  own_checkin: { id: number; status: string; lat: number; lon: number; t: string } | null;
  own_evidence_ids: number[];
  note: string;
  alert_zones?: FeatureCollection | null;
  evacuation?: FeatureCollection | null;
};

export type IncidentDetail = Incident & { locker: Evidence[] };
