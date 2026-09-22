import type { ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api, clearSession } from "./api";
import { DecisionMap } from "./DecisionMap";
import { useI18n } from "./I18nProvider";
import { LangToggle } from "./LangToggle";
import { LogoMark } from "./LogoMark";

const LAYER_KEYS = ["incidents", "risk", "zones", "visibility", "routes", "infra", "safety", "blocked"] as const;

export function OpsPage() {
  const { t } = useI18n();
  const nav = useNavigate();
  const qc = useQueryClient();
  const [sp, setSp] = useSearchParams();
  const q = useQuery({ queryKey: ["ops"], queryFn: api.opsSnapshot, refetchInterval: 2000 });
  const [show, setShow] = useState<Record<string, boolean>>({
    incidents: true, risk: true, zones: true, visibility: true, routes: true, infra: true, safety: true, blocked: true,
  });
  const tick = useMutation({ mutationFn: api.tick, onSuccess: () => qc.invalidateQueries({ queryKey: ["ops"] }) });
  const snap = q.data;
  const selected = Number(sp.get("incident") ?? snap?.incidents[0]?.id ?? 0);
  const detail = useQuery({
    queryKey: ["inc", selected],
    queryFn: () => api.incident(selected),
    enabled: selected > 0,
  });
  const act = useMutation({
    mutationFn: (kind: "assign" | "dismiss") => (kind === "assign" ? api.assign(selected) : api.dismiss(selected)),
    onSuccess: () => qc.invalidateQueries(),
  });

  const labels: Record<(typeof LAYER_KEYS)[number], string> = {
    incidents: t("incidents"),
    risk: t("risk"),
    zones: t("zones"),
    visibility: t("visibility"),
    routes: t("routes"),
    infra: t("infra"),
    safety: t("safety"),
    blocked: t("blocked"),
  };

  const weights = snap
    ? Object.entries(snap.priority_weights).map(([name, value]) => ({ name, value }))
    : [];

  const mapLabels = {
    hybrid: t("mapHybrid"),
    satellite: t("mapSatellite"),
    terrain: t("mapTerrain"),
    streets: t("mapStreets"),
  };

  return (
    <div className="flex min-h-screen flex-col bg-ops text-emerald-50">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 bg-black/20 px-4 py-3">
        <div className="flex items-center gap-3">
          <LogoMark crop={false} className="h-12 w-auto" />
          <div>
            <p className="font-display text-lg leading-none">{t("brand")} · {t("opsTitle")}</p>
            <p className="text-[11px] text-emerald-200/70">{t("thesis")}</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-[11px]">
          {snap && (
            <>
              <Pill k={t("tick")} v={String(snap.tick)} />
              <Pill k={t("rain")} v={`${snap.rainfall_index} · ${t("simulated")}`} />
              <Pill k={t("llm")} v={snap.health.llm === "ok" ? `${t("ok")} · ${t("optionalLlm")}` : t("down")} />
              <Pill k={t("routing")} v={t("precomputed")} />
            </>
          )}
          <button onClick={() => tick.mutate()} className="rounded-full bg-amber-200 px-4 py-2 text-xs font-bold text-ops shadow hover:bg-amber-100">{t("advance")}</button>
          <LangToggle dark />
          <button className="rounded-full px-3 py-2 text-xs text-emerald-100/80 hover:bg-white/10" onClick={() => { clearSession(); nav("/"); }}>{t("logout")}</button>
        </div>
      </header>

      {snap?.isolation.isolated_settlements?.length ? (
        <div className="bg-gradient-to-r from-orange-700 to-rose-800 px-4 py-2 text-sm font-semibold">
          {t("isolation")}: {snap.isolation.isolated_settlements.join(", ")} — {snap.isolation.cascade}
        </div>
      ) : null}

      <div className="grid flex-1 grid-cols-1 lg:grid-cols-[1fr_380px]">
        <div className="relative min-h-[420px] p-3">
          <div className="h-[calc(100vh-8rem)] overflow-hidden rounded-3xl border border-white/10 shadow-2xl">
            {snap && (
              <DecisionMap
                mode="ops"
                layers={snap.layers}
                routes={snap.routes}
                show={show}
                basemapLabels={mapLabels}
              />
            )}
          </div>
          <div className="pointer-events-auto absolute bottom-8 left-6 flex max-w-xl flex-wrap gap-1.5 rounded-2xl bg-black/70 p-2.5 text-[11px] shadow-xl backdrop-blur">
            {LAYER_KEYS.map((k) => (
              <button
                key={k}
                onClick={() => setShow((s) => ({ ...s, [k]: !s[k] }))}
                className={`rounded-full px-2 py-1 ${show[k] ? "bg-amber-200 text-ops" : "bg-white/10"}`}
              >
                {labels[k]}
              </button>
            ))}
          </div>
        </div>

        <aside className="space-y-3 overflow-y-auto border-l border-white/10 p-3">
          <p className="text-[11px] text-emerald-200/60">{t("playHint")}</p>
          <Card title={t("priority")}>
            <p className="mb-2 text-[11px] text-emerald-200/60">{t("weights")}</p>
            <div className="h-28">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={weights}>
                  <XAxis dataKey="name" hide />
                  <YAxis hide />
                  <Tooltip />
                  <Bar dataKey="value" fill="#fcd34d" radius={4} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            {(snap?.priority_queue ?? []).map((p) => (
              <div key={p.incident_code} className="mt-2 rounded-2xl bg-white/5 p-3">
                <div className="flex justify-between text-sm font-bold">
                  <span>{p.incident_code}</span>
                  <span className="text-amber-200">{p.score.toFixed(1)}</span>
                </div>
                <p className="mt-1 text-[11px] text-emerald-100/70">{t("resources")}: {p.nearest_resource} · {t("availabilitySim")}</p>
                <p className="text-[11px] text-emerald-100/50">{p.reason}</p>
              </div>
            ))}
            {!snap?.priority_queue.length && <p className="text-sm text-emerald-100/50">{t("noIncident")}</p>}
          </Card>

          <Card title={t("visibility")}>
            <p className="text-2xl font-display text-amber-200">{snap?.visibility.coverage_pct ?? 0}%</p>
            <p className="text-xs text-emerald-100/70">{t("unconfirmed")}: {snap?.visibility.unconfirmed_safety_status}</p>
            <p className="mt-1 text-[11px] leading-relaxed text-emerald-100/50">{t("notMissing")}</p>
          </Card>

          <Card title={t("locker")}>
            {(snap?.incidents ?? []).map((inc) => (
              <button
                key={inc.id}
                onClick={() => setSp({ incident: String(inc.id), tick: String(snap?.tick ?? 0) })}
                className={`mb-2 w-full rounded-2xl p-3 text-left ${selected === inc.id ? "bg-amber-200/20 ring-1 ring-amber-200" : "bg-white/5"}`}
              >
                <div className="flex justify-between text-sm font-semibold">
                  <span>{inc.code}</span>
                  <span>{Math.round(inc.confidence * 100)}%</span>
                </div>
                <p className="text-[11px] text-emerald-100/60">
                  {inc.status} {inc.isolated ? t("isolated") : ""} {inc.disagreement ? t("disagreement") : ""} {snap?.corroborated[inc.code] ? t("corroborated") : t("unverified")}
                </p>
              </button>
            ))}
            {detail.data && (
              <ul className="mt-2 space-y-2 text-xs">
                {detail.data.locker.map((e) => (
                  <li key={e.id} className="rounded-xl bg-black/20 p-2">
                    <span className="font-semibold">{e.emergency_type}</span> · {e.kind} · {e.source}
                    {e.has_media ? ` · ${t("photoOnFile")}` : ""}
                    <p className="text-emerald-100/70">{e.raw_text}</p>
                  </li>
                ))}
                <div className="flex gap-2 pt-2">
                  <button onClick={() => act.mutate("assign")} className="rounded-full bg-emerald-500 px-3 py-1 text-[11px] font-bold text-ops">{t("assign")}</button>
                  <button onClick={() => act.mutate("dismiss")} className="rounded-full bg-white/10 px-3 py-1 text-[11px]">{t("dismiss")}</button>
                </div>
                <p className="pt-1 text-[10px] text-emerald-100/40">{t("assignSim")}</p>
              </ul>
            )}
          </Card>

          {snap?.sitrep && (
            <Card title={t("sitrep")}><p className="text-sm">{snap.sitrep}</p></Card>
          )}
        </aside>
      </div>
    </div>
  );
}

function Pill({ k, v }: { k: string; v: string }) {
  return (
    <span className="rounded-full bg-white/10 px-3 py-1">
      {k} <strong className="text-amber-200">{v}</strong>
    </span>
  );
}

function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-3xl border border-white/10 bg-white/5 p-4">
      <h3 className="mb-2 font-display text-base">{title}</h3>
      {children}
    </section>
  );
}
