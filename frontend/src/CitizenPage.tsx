import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, clearSession } from "./api";
import { DecisionMap } from "./DecisionMap";
import { useI18n } from "./I18nProvider";
import { LangToggle } from "./LangToggle";
import { LogoMark } from "./LogoMark";
import type { CopyKey } from "./i18n";

const DEMO = { lat: 32.2395, lon: 77.188 };

export function CitizenPage() {
  const { t } = useI18n();
  const nav = useNavigate();
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["c-snap"], queryFn: api.citizenSnapshot, refetchInterval: 2500 });
  const [lat, setLat] = useState(DEMO.lat);
  const [lon, setLon] = useState(DEMO.lon);
  const [text, setText] = useState("");
  const [type, setType] = useState("landslide");
  const [people, setPeople] = useState(2);
  const [severity, setSeverity] = useState(4);
  const [trapped, setTrapped] = useState(false);
  const [injury, setInjury] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [smsCopied, setSmsCopied] = useState(false);
  const [checkSaved, setCheckSaved] = useState(false);
  const [photo, setPhoto] = useState<File | null>(null);

  const sos = useMutation({
    mutationFn: async () => {
      const r = await api.evidence({
        kind: "sos",
        lat,
        lon,
        raw_text: text || `${type} report`,
        emergency_type: type,
        people_count: people,
        severity,
        trapped,
        injury,
        source: "live",
      });
      if (photo) await api.uploadMedia(r.evidence_id, photo);
      return r;
    },
    onSuccess: (r) => {
      setMsg(`${t("sent")} ${r.incident_code} (${Math.round(r.cluster_confidence * 100)}%)`);
      setErr("");
      qc.invalidateQueries({ queryKey: ["c-snap"] });
    },
    onError: () => setErr(t("sosFail")),
  });
  const check = useMutation({
    mutationFn: (status: string) => api.checkin({ status, lat, lon, source: "live" }),
    onSuccess: () => {
      setCheckSaved(true);
      qc.invalidateQueries({ queryKey: ["c-snap"] });
    },
  });

  const snap = q.data;
  const sms = useMemo(
    () => `AASHRAY SOS ${type} lat=${lat.toFixed(5)} lon=${lon.toFixed(5)} people=${people} trapped=${trapped ? 1 : 0}`,
    [type, lat, lon, people, trapped],
  );

  const layers = {
    alert_zones: snap?.alert_zones ?? { type: "FeatureCollection" as const, features: [], provenance: { source: "rule", as_of: "" } },
    evacuation: snap?.evacuation ?? { type: "FeatureCollection" as const, features: [], provenance: { source: "rule", as_of: "" } },
    infrastructure: {
      type: "FeatureCollection" as const,
      features: (snap?.shelters ?? []).map((s) => ({
        type: "Feature" as const,
        geometry: { type: "Point" as const, coordinates: [s.lon, s.lat] },
        properties: { name: s.name, kind: s.kind },
      })),
      provenance: { source: "rule" as const, as_of: snap?.as_of ?? "" },
    },
  };

  const alertCopy =
    snap?.zone_level === "critical"
      ? t("zoneCriticalMsg")
      : snap?.zone_level === "warning"
        ? t("zoneWarningMsg")
        : snap?.zone_level
          ? t("zoneNearby")
          : t("noAlert");

  const kindLabel = (kind: string) => {
    if (kind === "hospital") return t("hospital");
    if (kind === "shelter") return t("shelter");
    if (kind === "fire") return t("fire");
    return kind;
  };

  const mapLabels = {
    hybrid: t("mapHybrid"),
    satellite: t("mapSatellite"),
    terrain: t("mapTerrain"),
    streets: t("mapStreets"),
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(900px_400px_at_0%_0%,#ccfbf1_0%,transparent_45%),#f4efe4]">
      <header className="sticky top-0 z-20 border-b border-sand/80 bg-paper/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <div className="flex items-center gap-2">
          <LogoMark crop={false} className="h-12 w-auto" />
          <div>
            <p className="font-display text-lg leading-none">{t("brand")}</p>
            <p className="text-[11px] text-moss/70">{t("citizen")}</p>
          </div>
        </div>
        <div className="ml-auto flex shrink-0 items-center gap-2">
          <LangToggle />
          <button className="rounded-full px-3 py-2 text-xs font-semibold text-moss hover:bg-sand" onClick={() => { clearSession(); nav("/"); }}>
            {t("logout")}
          </button>
        </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-6xl gap-5 px-4 py-5 pb-28 lg:grid-cols-[1.05fr_0.95fr] lg:items-start">
        <div className="space-y-4">
          <p className="rounded-3xl bg-white/90 px-5 py-4 text-sm leading-relaxed text-ink/80 shadow-sm">{t("welcomeCitizen")}</p>

          {snap?.isolation.isolated_settlements?.length ? (
            <div className="rounded-3xl bg-gradient-to-br from-orange-700 to-rose-800 px-5 py-4 text-white shadow-lg">
              <p className="text-xs font-bold uppercase tracking-wider">{t("isolation")}</p>
              <p className="mt-1 text-sm">{snap.isolation.cascade || t("isolationHint")}</p>
            </div>
          ) : null}

          <div
            className={`rounded-3xl px-5 py-5 shadow-md ${
              snap?.zone_level === "critical"
                ? "bg-orange-600 text-white"
                : snap?.zone_level === "warning"
                  ? "bg-amber-500 text-amber-950"
                  : snap?.zone_level
                    ? "bg-sky-700 text-white"
                    : "bg-white text-ink"
            }`}
          >
            <p className="text-xs font-bold uppercase tracking-[0.18em]">{t("alertBanner")}</p>
            <p className="mt-1 font-display text-3xl">
              {snap?.zone_level === "critical"
                ? t("zoneCritical")
                : snap?.zone_level === "warning"
                  ? t("zoneWarning")
                  : snap?.zone_level
                    ? t("zoneNearby")
                    : "—"}
            </p>
            <p className="mt-2 text-sm leading-relaxed">{alertCopy}</p>
            {snap?.zone_level && snap.zone_level !== "critical" ? (
              <p className="mt-2 text-xs opacity-80">{t("notCriticalYet")}</p>
            ) : null}
          </div>

          <section className="overflow-hidden rounded-[1.75rem] bg-black shadow-lg ring-1 ring-black/10">
            <div className="h-[22rem] lg:h-[36rem]">
              <DecisionMap
                mode="citizen"
                layers={layers}
                routes={[...(snap?.safest_route ? [snap.safest_route] : []), ...(snap?.rejected_routes ?? [])]}
                own={{ lat, lon }}
                youLabel={t("you")}
                onPick={(la, lo) => { setLat(Number(la.toFixed(5))); setLon(Number(lo.toFixed(5))); }}
                basemapLabels={mapLabels}
                show={{ zones: true, routes: true, risk: false, visibility: false, blocked: false, incidents: false, infra: true, safety: false }}
              />
            </div>
            <div className="flex flex-wrap items-center justify-between gap-2 bg-ops px-4 py-3 text-xs text-emerald-100/80">
              <p>{t("clickMap")} {t("mapHint")}</p>
              <p className="font-mono text-[11px] text-amber-200">{lat.toFixed(4)}, {lon.toFixed(4)}</p>
            </div>
          </section>

          {snap?.safest_route && (
            <section className="rounded-3xl bg-emerald-50 p-5 ring-1 ring-emerald-200/70">
              <p className="text-xs font-bold uppercase tracking-wide text-emerald-800">{t("safest")}</p>
              <p className="mt-1 font-display text-xl text-emerald-950">
                {snap.safest_route.label} · {snap.safest_route.duration_min} {t("minutes")}
              </p>
              {snap.rejected_routes.map((r) => (
                <p key={r.id} className="mt-2 text-sm text-red-800">
                  {t("rejected")}: {r.label} — {r.reason}
                </p>
              ))}
            </section>
          )}
        </div>

        <div className="space-y-4">
          <section className="rounded-3xl bg-white p-5 shadow-sm">
            <h2 className="font-display text-2xl">{t("safetyTitle")}</h2>
            <div className="mt-4 grid grid-cols-3 gap-2">
              {[
                ["safe", t("imSafe"), "bg-emerald-600 hover:bg-emerald-700"],
                ["assist", t("needAssist"), "bg-amber-500 hover:bg-amber-600"],
                ["danger", t("inDanger"), "bg-red-600 hover:bg-red-700"],
              ].map(([st, label, bg]) => (
                <button
                  key={st}
                  onClick={() => check.mutate(st)}
                  className={`${bg} min-h-16 rounded-2xl px-2 py-3 text-xs font-bold leading-snug text-white shadow-sm`}
                >
                  {label}
                </button>
              ))}
            </div>
            {checkSaved && <p className="mt-2 text-xs text-moss">{t("checkinSaved")}</p>}
            {snap?.own_checkin && (
              <p className="mt-2 text-xs text-ink/60">
                {snap.own_checkin.status} · {new Date(snap.own_checkin.t).toLocaleTimeString()}
              </p>
            )}
          </section>

          <section className="rounded-3xl bg-white p-5 shadow-sm">
            <h2 className="font-display text-2xl">{t("sosTitle")}</h2>
            <p className="mt-1 text-sm leading-relaxed text-ink/65">{t("juryCitizen")}</p>
            <button
              disabled={sos.isPending}
              onClick={() => sos.mutate()}
              className="mt-4 w-full rounded-2xl bg-clay py-5 text-lg font-bold text-white shadow-lg shadow-orange-900/25 hover:bg-orange-800 disabled:opacity-60"
            >
              {sos.isPending ? t("sending") : t("sos")}
            </button>
            {err && <p className="mt-3 rounded-2xl bg-red-50 px-3 py-2 text-sm text-red-800">{err}</p>}
            {msg && (
              <div className="mt-3 rounded-2xl bg-emerald-700 px-4 py-4 text-white shadow-lg">
                <p className="text-xs font-bold uppercase tracking-wider">{t("sosOkTitle")}</p>
                <p className="mt-1 font-display text-xl">{msg}</p>
                <p className="mt-1 text-xs text-emerald-100">{t("clusterNote")}</p>
              </div>
            )}
            <p className="mt-4 text-sm leading-relaxed text-ink/65">{t("sosBody")}</p>
            <label className="mt-4 block text-xs font-semibold uppercase tracking-wide text-ink/45">{t("type")}</label>
            <div className="mt-2 grid grid-cols-2 gap-2">
              {(
                [
                  ["landslide", "landslide"],
                  ["blocked_road", "blockedRoad"],
                  ["trapped", "trapped"],
                  ["other", "other"],
                ] as const
              ).map(([k, key]) => (
                <button
                  key={k}
                  type="button"
                  onClick={() => setType(k)}
                  className={`min-h-12 rounded-2xl px-3 py-2 text-sm font-semibold ${type === k ? "bg-moss text-white shadow" : "bg-sand text-ink"}`}
                >
                  {t(key as CopyKey)}
                </button>
              ))}
            </div>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={t("describe")}
              className="mt-4 w-full rounded-2xl border border-sand bg-paper px-4 py-3 text-sm outline-none ring-moss focus:ring-2"
              rows={2}
            />
            <div className="mt-3 grid grid-cols-2 gap-3">
              <label className="text-xs font-medium text-ink/70">
                {t("people")}
                <input type="number" value={people} onChange={(e) => setPeople(+e.target.value)} className="mt-1 w-full rounded-2xl border border-sand bg-paper px-3 py-2.5 text-sm" />
              </label>
              <label className="text-xs font-medium text-ink/70">
                {t("severity")}
                <input type="number" min={0} max={5} value={severity} onChange={(e) => setSeverity(+e.target.value)} className="mt-1 w-full rounded-2xl border border-sand bg-paper px-3 py-2.5 text-sm" />
              </label>
            </div>
            <label className="mt-4 flex min-h-11 items-center gap-3 rounded-2xl bg-paper px-3 text-sm">
              <input type="checkbox" className="h-4 w-4 accent-moss" checked={trapped} onChange={(e) => setTrapped(e.target.checked)} />
              {t("trappedFlag")}
            </label>
            <label className="mt-2 flex min-h-11 items-center gap-3 rounded-2xl bg-paper px-3 text-sm">
              <input type="checkbox" className="h-4 w-4 accent-moss" checked={injury} onChange={(e) => setInjury(e.target.checked)} />
              {t("injuryFlag")}
            </label>
            <p className="mt-4 text-xs font-semibold uppercase tracking-wide text-ink/45">{t("photoOptional")}</p>
            <p className="mt-1 text-[11px] text-ink/50">{t("photoNote")}</p>
            <input
              type="file"
              accept="image/*"
              className="mt-2 block w-full text-xs"
              onChange={(e) => setPhoto(e.target.files?.[0] ?? null)}
            />
            <p className="mt-4 text-xs font-semibold uppercase tracking-wide text-ink/45">{t("location")}</p>
            <p className="mt-1 text-sm text-ink/70">{lat.toFixed(5)}, {lon.toFixed(5)}</p>
            <div className="mt-2 flex flex-wrap gap-3">
              <button type="button" className="rounded-full bg-sand px-3 py-1.5 text-xs font-semibold text-moss" onClick={() => { setLat(DEMO.lat); setLon(DEMO.lon); }}>
                {t("demoPin")}
              </button>
              <button
                type="button"
                className="rounded-full bg-sand px-3 py-1.5 text-xs font-semibold text-moss"
                onClick={() => navigator.geolocation?.getCurrentPosition((p) => { setLat(p.coords.latitude); setLon(p.coords.longitude); })}
              >
                {t("useGps")}
              </button>
            </div>
          </section>

          <section className="rounded-3xl bg-white p-5 shadow-sm">
            <h2 className="font-display text-xl">{t("shelters")}</h2>
            <p className="text-xs text-ink/50">{t("availabilitySim")}</p>
            <ul className="mt-3 space-y-2">
              {(snap?.shelters ?? []).map((s) => (
                <li key={s.id} className="flex items-center justify-between rounded-2xl bg-paper px-4 py-3 text-sm">
                  <span className="font-medium">{s.name}</span>
                  <span className="rounded-full bg-white px-2 py-0.5 text-[11px] text-ink/55">{kindLabel(s.kind)}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="rounded-3xl border border-dashed border-moss/30 bg-white p-5">
            <h2 className="font-display text-xl">{t("smsTitle")}</h2>
            <p className="mt-1 text-sm leading-relaxed text-ink/65">{t("smsBody")}</p>
            <pre className="mt-3 overflow-auto rounded-2xl bg-ops p-3 text-xs text-emerald-100">{sms}</pre>
            <button
              className="mt-3 rounded-full bg-moss px-4 py-2 text-xs font-bold text-white"
              onClick={async () => {
                await navigator.clipboard.writeText(sms);
                setSmsCopied(true);
              }}
            >
              {smsCopied ? t("copied") : t("copySms")}
            </button>
          </section>
          <p className="pb-2 text-center text-[11px] text-ink/45">{t("ownNote")}</p>
        </div>
      </div>

      <div className="fixed inset-x-0 bottom-0 z-30 border-t border-sand bg-paper/95 p-3 backdrop-blur lg:hidden">
        <p className="mb-2 text-center text-[11px] text-ink/50">{t("stickySosHint")}</p>
        <button
          disabled={sos.isPending}
          onClick={() => sos.mutate()}
          className="w-full rounded-2xl bg-clay py-4 text-base font-bold text-white shadow-lg disabled:opacity-60"
        >
          {sos.isPending ? t("sending") : t("sos")}
        </button>
      </div>
    </div>
  );
}
