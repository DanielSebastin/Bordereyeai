"use client";

import { useEffect, useRef, useCallback } from "react";
import { MapContainer, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { cameraLocations, heatmapPoints } from "@/lib/mockData";
import type { CameraLocation, ThreatLevel } from "@/types";

// ─── Threat colours ────────────────────────────────────────────────────────────

const THREAT_COLOR: Record<ThreatLevel, string> = {
  critical: "#ef4444",
  high:     "#f97316",
  medium:   "#eab308",
  low:      "#22c55e",
};

function createMarkerIcon(cam: CameraLocation) {
  const color = THREAT_COLOR[cam.threatLevel];
  const statusColor = cam.status === "online" ? "#10B981" : cam.status === "degraded" ? "#F59E0B" : "#EF4444";

  const html = `
    <div style="
      display: flex;
      align-items: center;
      background-color: #1A2535;
      border: 1.5px solid ${color};
      border-radius: 20px;
      padding: 3px 10px 3px 4px;
      box-shadow: 0 2px 5px rgba(0,0,0,0.3);
      width: max-content;
      transform: translate(-15px, -15px);
    ">
      <div style="
        width: 18px;
        height: 18px;
        border-radius: 50%;
        background-color: ${color}20;
        border: 1px solid ${color};
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 6px;
      ">
        <div style="width: 6px; height: 6px; border-radius: 50%; background-color: ${statusColor};"></div>
      </div>
      <span style="
        font-family: 'Noto Sans', sans-serif;
        font-size: 11px;
        font-weight: 600;
        color: #FFFFFF;
        white-space: nowrap;
      ">${cam.name}</span>
    </div>
  `;

  return L.divIcon({
    html: html,
    className: "",
    iconSize: [0, 0], // Allows the CSS transform and auto-width to determine size
    iconAnchor: [0, 0],
    popupAnchor: [0, -20],
  });
}

// ─── Canvas heatmap — fixed zoom/resize ───────────────────────────────────────

interface HeatPt { lat: number; lng: number; intensity: number }

function CanvasHeatmap({ points }: { points: HeatPt[] }) {
  const map = useMap();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const layerRef  = useRef<L.Layer | null>(null);

  const redraw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const size = map.getSize();
    canvas.width  = size.x;
    canvas.height = size.y;

    // Position canvas to cover the entire map container
    // (use layerPoint offset so it stays aligned during pan)
    const topLeft = map.containerPointToLayerPoint([0, 0]);
    L.DomUtil.setPosition(canvas, topLeft);

    const ctx = canvas.getContext("2d")!;
    ctx.clearRect(0, 0, size.x, size.y);

    for (const pt of points) {
      // Convert geographic coords → pixel coords relative to current view
      const containerPt = map.latLngToContainerPoint(L.latLng(pt.lat, pt.lng));
      const px = containerPt.x;
      const py = containerPt.y;

      // Scale radius with zoom level so blobs stay geographically proportional
      const zoom   = map.getZoom();
      const base   = 55 + pt.intensity * 35;
      const scale  = Math.pow(2, zoom - 7);           // normalised to zoom 7
      const radius = Math.max(base * scale, 18);

      const alpha = Math.min(pt.intensity * 0.72, 0.72);

      let r: number, g: number, b: number;
      if (pt.intensity >= 0.8)       { r = 239; g = 68;  b = 68;  } // Red
      else if (pt.intensity >= 0.6)  { r = 249; g = 115; b = 22;  } // Orange
      else if (pt.intensity >= 0.35) { r = 234; g = 179; b = 8;   } // Yellow
      else                           { r = 59;  g = 130; b = 246; } // Blue

      const grad = ctx.createRadialGradient(px, py, 0, px, py, radius);
      grad.addColorStop(0,    `rgba(${r},${g},${b},${alpha})`);
      grad.addColorStop(0.5,  `rgba(${r},${g},${b},${alpha * 0.4})`);
      grad.addColorStop(1,    `rgba(${r},${g},${b},0)`);

      ctx.beginPath();
      ctx.arc(px, py, radius, 0, Math.PI * 2);
      ctx.fillStyle = grad;
      ctx.fill();
    }
  }, [map, points]);

  useEffect(() => {
    // Create a custom Leaflet layer that hosts the canvas
    const HeatLayer = L.Layer.extend({
      onAdd(m: L.Map) {
        const canvas = L.DomUtil.create("canvas") as HTMLCanvasElement;
        Object.assign(canvas.style, {
          position:      "absolute",
          pointerEvents: "none",
          zIndex:        "400",
        });
        m.getPanes().overlayPane!.appendChild(canvas);
        canvasRef.current = canvas;

        m.on("moveend zoomend viewreset resize", redraw);
        redraw();
        return this;
      },
      onRemove(m: L.Map) {
        m.off("moveend zoomend viewreset resize", redraw);
        canvasRef.current?.remove();
        canvasRef.current = null;
      },
    });

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const layer = new (HeatLayer as any)();
    layer.addTo(map);
    layerRef.current = layer;

    return () => {
      if (layerRef.current) {
        map.removeLayer(layerRef.current);
        layerRef.current = null;
      }
    };
  }, [map, redraw]);

  return null;
}

// ─── Camera markers ────────────────────────────────────────────────────────────

function CameraMarkers() {
  const map = useMap();

  useEffect(() => {
    const markers: L.Marker[] = [];

    for (const cam of cameraLocations) {
      const color = THREAT_COLOR[cam.threatLevel];

      const popup = L.popup({ maxWidth: 220, closeButton: true }).setContent(`
        <div style="padding:10px 12px;font-family:'Noto Sans',sans-serif;background:#FFFFFF;border-radius:4px;color:#1A2535;">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid #C8D0DE;">
            <span style="font-size:12px;font-weight:700;color:#002060;">${cam.name}</span>
            <span style="font-size:9px;font-weight:700;padding:2px 7px;border-radius:3px;
              background:${color}18;border:1px solid ${color}60;color:${color};letter-spacing:.08em;">
              ${cam.threatLevel.toUpperCase()}
            </span>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:6px;">
            <div style="background:#F4F6FB;border:1px solid #E4E9F2;border-radius:4px;padding:6px 8px;">
              <div style="font-size:9px;color:#5A6A7C;margin-bottom:2px;text-transform:uppercase;letter-spacing:.06em;font-weight:600;">Risk Score</div>
              <div style="font-size:20px;font-weight:700;color:${color};line-height:1;font-family:'Roboto Mono',monospace;">${cam.riskScore}</div>
            </div>
            <div style="background:#F4F6FB;border:1px solid #E4E9F2;border-radius:4px;padding:6px 8px;">
              <div style="font-size:9px;color:#5A6A7C;margin-bottom:4px;text-transform:uppercase;letter-spacing:.06em;font-weight:600;">Status</div>
              <div style="display:flex;align-items:center;gap:4px;">
                <span style="height:6px;width:6px;border-radius:50%;background:${
                  cam.status === "online" ? "#1A6B3C" : cam.status === "degraded" ? "#C05000" : "#B71C1C"
                };flex-shrink:0;"></span>
                <span style="font-size:11px;color:#1A2535;font-weight:600;text-transform:capitalize;">${cam.status}</span>
              </div>
            </div>
          </div>
          <div style="font-size:10px;color:#5A6A7C;">Last activity: <strong style="color:#1A2535;">${cam.lastActivity}</strong></div>
        </div>
      `);

      const m = L.marker([cam.lat, cam.lng], { icon: createMarkerIcon(cam) })
        .bindPopup(popup)
        .addTo(map);
      markers.push(m);
    }

    return () => markers.forEach((m) => m.remove());
  }, [map]);

  return null;
}

// ─── Map controls ─────────────────────────────────────────────────────────────

function MapControls() {
  const map = useMap();
  return (
    <div
      style={{
        position: "absolute",
        top: 10, right: 10,
        zIndex: 500,
        display: "flex",
        flexDirection: "column",
        gap: 4,
      }}
    >
      {[
        { label: "+", fn: () => map.zoomIn()  },
        { label: "−", fn: () => map.zoomOut() },
      ].map(({ label, fn }) => (
        <button
          key={label}
          onClick={fn}
          style={{
            width: 28, height: 28,
            display: "flex", alignItems: "center", justifyContent: "center",
            background: "#FFFFFF",
            border: "1px solid #C8D0DE",
            borderRadius: 4,
            color: "#003380",
            fontSize: 15, fontWeight: 700,
            cursor: "pointer",
            boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
          }}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

// ─── Threat legend ────────────────────────────────────────────────────────────

function ThreatLegend() {
  return (
    <div
      style={{
        position: "absolute",
        bottom: 10, left: 10,
        zIndex: 500,
        background: "#FFFFFF",
        border: "1px solid #C8D0DE",
        borderRadius: 4,
        padding: "8px 10px",
        boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
      }}
    >
      <p style={{ fontSize: 9, fontWeight: 700, color: "#003380", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 5 }}>
        Threat Level
      </p>
      <div style={{ height: 6, width: 120, borderRadius: 3, background: "linear-gradient(to right, #1A6B3C, #0D5EA6, #C05000, #B71C1C)", marginBottom: 4 }} />
      <div style={{ display: "flex", justifyContent: "space-between", width: 120 }}>
        {["Low", "Med", "High", "Crit"].map((l) => (
          <span key={l} style={{ fontSize: 8.5, fontWeight: 600, color: "#5A6A7C" }}>{l}</span>
        ))}
      </div>
    </div>
  );
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function BorderHeatmap() {
  // Centred on Pakistan–India border (Kashmir / Punjab region)
  const center: [number, number] = [32.5, 74.5];

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <MapContainer
        center={center}
        zoom={7}
        style={{ height: "100%", width: "100%" }}
        zoomControl={false}
        attributionControl={false}
        preferCanvas
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution=""
          keepBuffer={4}
        />
        <CanvasHeatmap points={heatmapPoints} />
        <CameraMarkers />
        <MapControls />
      </MapContainer>

      <ThreatLegend />
    </div>
  );
}
