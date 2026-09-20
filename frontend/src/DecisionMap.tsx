import { useEffect, useMemo, useState } from "react";
import L from "leaflet";
import {
  CircleMarker,
  GeoJSON,
  MapContainer,
  Polyline,
  Popup,
  TileLayer,
  ZoomControl,
  useMap,
  useMapEvents,
} from "react-leaflet";
import type { FeatureCollection, RouteScore } from "./types";
import "leaflet/dist/leaflet.css";

const CENTER: [number, number] = [32.2398, 77.1889];

export type Basemap = "hybrid" | "satellite" | "terrain" | "streets";

function Fit() {
  const map = useMap();
  useEffect(() => {
    const id = window.setTimeout(() => map.invalidateSize(), 80);
    return () => window.clearTimeout(id);
  }, [map]);
  return null;
}

function ScaleBar() {
  const map = useMap();
  useEffect(() => {
    const control = L.control.scale({ imperial: false, metric: true, position: "bottomleft" }).addTo(map);
    return () => {
      control.remove();
    };
  }, [map]);
  return null;
}

function ClickSet({ onPick }: { onPick?: (lat: number, lon: number) => void }) {
  useMapEvents({
    click(e) {
      onPick?.(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

function BaseTiles({ kind }: { kind: Basemap }) {
  if (kind === "streets") {
    return (
      <TileLayer
        attribution='&copy; OpenStreetMap &copy; CARTO'
        url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
        maxZoom={20}
      />
    );
  }
  if (kind === "terrain") {
    return (
      <TileLayer
        attribution="Tiles &copy; Esri"
        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}"
        maxZoom={19}
      />
    );
  }
  return (
    <>
      <TileLayer
        attribution="Tiles &copy; Esri — Earthstar Geographics"
        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        maxZoom={19}
      />
      {kind === "hybrid" && (
        <TileLayer
          attribution="Esri"
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
          maxZoom={19}
        />
      )}
    </>
  );
}

function zoneStyle(props: Record<string, unknown>) {
  const level = String(props.level ?? "");
  if (level === "critical") return { color: "#fb923c", fillColor: "#ea580c", fillOpacity: 0.22, weight: 2 };
  if (level === "warning") return { color: "#facc15", fillColor: "#eab308", fillOpacity: 0.16, weight: 2 };
  return { color: "#7dd3fc", fillColor: "#0ea5e9", fillOpacity: 0.12, weight: 1.5 };
}

function visStyle(props: Record<string, unknown>) {
  const v = Number(props.visibility ?? 0);
  const fill = v < 0.35 ? "#7f1d1d" : v < 0.7 ? "#a16207" : "#047857";
  return { color: fill, fillColor: fill, fillOpacity: 0.18, weight: 1 };
}

export function DecisionMap({
  layers,
  routes,
  own,
  show,
  youLabel = "You",
  onPick,
  basemapLabels,
}: {
  layers?: Record<string, FeatureCollection>;
  routes?: RouteScore[];
  own?: { lat: number; lon: number } | null;
  mode?: "ops" | "citizen";
  show: Record<string, boolean>;
  youLabel?: string;
  onPick?: (lat: number, lon: number) => void;
  basemapLabels: { hybrid: string; satellite: string; terrain: string; streets: string };
}) {
  const geo = useMemo(() => layers ?? {}, [layers]);
  const [basemap, setBasemap] = useState<Basemap>("hybrid");
  const options: { id: Basemap; label: string }[] = [
    { id: "hybrid", label: basemapLabels.hybrid },
    { id: "satellite", label: basemapLabels.satellite },
    { id: "terrain", label: basemapLabels.terrain },
    { id: "streets", label: basemapLabels.streets },
  ];

  return (
    <div className="relative h-full w-full">
      <MapContainer
        center={CENTER}
        zoom={14}
        className="h-full w-full"
        scrollWheelZoom
        zoomControl={false}
        maxZoom={19}
      >
        <BaseTiles kind={basemap} />
        <ZoomControl position="bottomright" />
        <ScaleBar />
        <Fit />
        <ClickSet onPick={onPick} />
        {show.zones && geo.alert_zones && (
          <GeoJSON
            key={`z-${geo.alert_zones.features.length}-${geo.alert_zones.provenance?.as_of}`}
            data={geo.alert_zones as never}
            style={(f) => zoneStyle((f?.properties as Record<string, unknown>) ?? {})}
          />
        )}
        {show.risk && geo.risk && (
          <GeoJSON
            key={`r-${geo.risk.features.length}`}
            data={geo.risk as never}
            style={() => ({ color: "#fdba74", fillColor: "#9a3412", fillOpacity: 0.28, weight: 2 })}
          />
        )}
        {show.visibility && geo.visibility && (
          <GeoJSON
            key={`v-${geo.visibility.features.length}`}
            data={geo.visibility as never}
            style={(f) => visStyle((f?.properties as Record<string, unknown>) ?? {})}
          />
        )}
        {show.blocked && geo.blocked_roads && (
          <GeoJSON
            key="b"
            data={geo.blocked_roads as never}
            style={() => ({ color: "#fecaca", weight: 6, dashArray: "10 8" })}
          />
        )}
        {show.routes &&
          (routes ?? []).map((r) => (
            <Polyline
              key={r.id}
              positions={r.coordinates.map(([lon, lat]) => [lat, lon] as [number, number])}
              pathOptions={{
                color: r.status === "rejected" ? "#fda4af" : r.status === "safest_available" ? "#6ee7b7" : "#cbd5e1",
                weight: r.status === "safest_available" ? 7 : 4,
                dashArray: r.status === "rejected" ? "8 10" : undefined,
                opacity: 0.95,
              }}
            >
              <Popup>
                {r.label} · {r.status}
                {r.reason ? ` — ${r.reason}` : ""}
              </Popup>
            </Polyline>
          ))}
        {show.incidents &&
          geo.incidents?.features.map((f, i) => {
            const g = f.geometry;
            if (!g || g.type !== "Point") return null;
            const [lon, lat] = g.coordinates as [number, number];
            return (
              <CircleMarker
                key={`i${i}`}
                center={[lat, lon]}
                radius={12}
                pathOptions={{ color: "#fff", weight: 2, fillColor: "#e11d48", fillOpacity: 1 }}
              >
                <Popup>
                  {(f.properties.code as string) ?? "incident"} ·{" "}
                  {Math.round(Number(f.properties.confidence ?? 0) * 100)}%
                </Popup>
              </CircleMarker>
            );
          })}
        {show.infra &&
          geo.infrastructure?.features.map((f, i) => {
            const g = f.geometry;
            if (!g || g.type !== "Point") return null;
            const [lon, lat] = g.coordinates as [number, number];
            return (
              <CircleMarker
                key={`p${i}`}
                center={[lat, lon]}
                radius={8}
                pathOptions={{ color: "#fff", weight: 2, fillColor: "#38bdf8", fillOpacity: 1 }}
              >
                <Popup>
                  {String(f.properties.name ?? "")} · {String(f.properties.kind ?? "")}
                </Popup>
              </CircleMarker>
            );
          })}
        {show.safety &&
          geo.human_safety?.features.map((f, i) => {
            const g = f.geometry;
            if (!g || g.type !== "Point") return null;
            const [lon, lat] = g.coordinates as [number, number];
            const st = String(f.properties.status ?? "safe");
            const color = st === "danger" ? "#ef4444" : st === "assist" ? "#f59e0b" : "#22c55e";
            return (
              <CircleMarker
                key={`s${i}`}
                center={[lat, lon]}
                radius={7}
                pathOptions={{ color: "#fff", weight: 2, fillColor: color, fillOpacity: 1 }}
              />
            );
          })}
        {own && (
          <CircleMarker
            center={[own.lat, own.lon]}
            radius={11}
            pathOptions={{ color: "#ecfdf5", weight: 3, fillColor: "#14b8a6", fillOpacity: 1 }}
          >
            <Popup>{youLabel}</Popup>
          </CircleMarker>
        )}
      </MapContainer>
      <div className="pointer-events-auto absolute right-3 top-3 z-[500] flex flex-wrap justify-end gap-1 rounded-2xl bg-black/55 p-1 shadow-lg backdrop-blur">
        {options.map((o) => (
          <button
            key={o.id}
            type="button"
            onClick={() => setBasemap(o.id)}
            className={`rounded-xl px-2.5 py-1.5 text-[11px] font-semibold ${
              basemap === o.id ? "bg-white text-ink" : "text-white/85 hover:bg-white/10"
            }`}
          >
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );
}
