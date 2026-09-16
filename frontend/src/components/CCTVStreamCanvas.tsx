"use client";

import { useEffect, useRef } from "react";

interface CCTVStreamCanvasProps {
  cameraId: string;
  cameraName: string;
  sector: string;
  fps?: number;
  expanded?: boolean;
}

export default function CCTVStreamCanvas({
  cameraId,
  cameraName,
  sector,
  fps = 30,
  expanded = false,
}: CCTVStreamCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let frameCount = 0;

    // Simulated moving objects
    const entities = [
      { x: 120, y: 220, vx: 0.8, vy: 0.1, type: "person", id: "P-101", color: "#22c55e" },
      { x: 340, y: 180, vx: -0.6, vy: 0.15, type: "person", id: "P-102", color: "#3b82f6" },
      { x: 200, y: 280, vx: 1.4, vy: -0.05, type: "vehicle", id: "TN11AA1234", color: "#f59e0b" },
      { x: 450, y: 310, vx: -0.9, vy: -0.1, type: "intruder", id: "ALERT-INT", color: "#ef4444" },
    ];

    const isNight = cameraId === "cam-03";
    const isFence = cameraId === "cam-04";
    const isANPR = cameraId === "cam-02";
    const isFace = cameraId === "cam-06";

    const render = () => {
      frameCount++;
      const w = canvas.width;
      const h = canvas.height;

      // 1. Background scene
      if (isNight) {
        // Green-phosphor / IR night vision
        ctx.fillStyle = "#021208";
        ctx.fillRect(0, 0, w, h);
      } else {
        // CCTV slate / asphalt surveillance background
        ctx.fillStyle = "#0b131e";
        ctx.fillRect(0, 0, w, h);
      }

      // 2. Horizon and environment perspective lines
      ctx.strokeStyle = isNight ? "rgba(34, 197, 94, 0.15)" : "rgba(255, 255, 255, 0.08)";
      ctx.lineWidth = 1;

      // Ground plane
      ctx.beginPath();
      ctx.moveTo(0, h * 0.45);
      ctx.lineTo(w, h * 0.45);
      ctx.stroke();

      // Road / corridor perspective
      ctx.beginPath();
      ctx.moveTo(w * 0.35, h * 0.45);
      ctx.lineTo(w * 0.1, h);
      ctx.moveTo(w * 0.65, h * 0.45);
      ctx.lineTo(w * 0.9, h);
      ctx.stroke();

      // Gate / fence structures
      if (isFence) {
        ctx.strokeStyle = "rgba(239, 68, 68, 0.35)";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(w * 0.2, h * 0.5);
        ctx.lineTo(w * 0.8, h * 0.5);
        ctx.lineTo(w * 0.85, h * 0.85);
        ctx.lineTo(w * 0.15, h * 0.85);
        ctx.closePath();
        ctx.stroke();
        ctx.fillStyle = "rgba(239, 68, 68, 0.06)";
        ctx.fill();
      }

      // 3. Animated Entities
      entities.forEach((e, idx) => {
        // Only show relevant entities per camera
        if (isANPR && e.type !== "vehicle") return;
        if (isFence && e.type !== "intruder" && e.type !== "person") return;

        e.x += e.vx;
        e.y += e.vy;

        if (e.x > w * 0.85 || e.x < w * 0.15) e.vx *= -1;
        if (e.y > h * 0.8 || e.y < h * 0.48) e.vy *= -1;

        const boxW = e.type === "vehicle" ? 80 : 32;
        const boxH = e.type === "vehicle" ? 45 : 68;

        // Bounding box
        const strokeCol = isNight ? "#22c55e" : e.color;
        ctx.strokeStyle = strokeCol;
        ctx.lineWidth = 1.5;
        ctx.strokeRect(e.x - boxW / 2, e.y - boxH / 2, boxW, boxH);

        // Corner accents
        const cornerLen = 6;
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        // Top-left
        ctx.moveTo(e.x - boxW / 2, e.y - boxH / 2 + cornerLen);
        ctx.lineTo(e.x - boxW / 2, e.y - boxH / 2);
        ctx.lineTo(e.x - boxW / 2 + cornerLen, e.y - boxH / 2);
        // Top-right
        ctx.moveTo(e.x + boxW / 2 - cornerLen, e.y - boxH / 2);
        ctx.lineTo(e.x + boxW / 2, e.y - boxH / 2);
        ctx.lineTo(e.x + boxW / 2, e.y - boxH / 2 + cornerLen);
        ctx.stroke();

        // Label pill
        ctx.fillStyle = strokeCol;
        ctx.fillRect(e.x - boxW / 2, e.y - boxH / 2 - 14, boxW, 14);
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 9px monospace";
        ctx.fillText(e.id, e.x - boxW / 2 + 3, e.y - boxH / 2 - 3);
      });

      // 4. Optical Scanline Effect
      ctx.fillStyle = "rgba(0, 0, 0, 0.12)";
      for (let y = 0; y < h; y += 4) {
        ctx.fillRect(0, y, w, 1);
      }

      // 5. HUD OSD & Timestamps
      const now = new Date();
      const timeStr = now.toISOString().replace("T", " ").substring(0, 19) + " IST";

      ctx.fillStyle = isNight ? "#4ade80" : "#94a3b8";
      ctx.font = "10px monospace";

      // Top-right status
      ctx.fillText(`${timeStr}`, w - 190, 20);
      ctx.fillText(`SEC: ${sector.substring(0, 18)}`, w - 190, 34);
      ctx.fillText(`FPS: ${fps}.0 | AI: ACTIVE`, w - 190, 48);

      // REC indicator (blinking)
      if (Math.floor(frameCount / 25) % 2 === 0) {
        ctx.fillStyle = "#ef4444";
        ctx.beginPath();
        ctx.arc(w - 200, 16, 4, 0, Math.PI * 2);
        ctx.fill();
      }

      // Optical Center Crosshair
      ctx.strokeStyle = isNight ? "rgba(34, 197, 94, 0.3)" : "rgba(255, 255, 255, 0.2)";
      ctx.lineWidth = 1;
      const cx = w / 2;
      const cy = h / 2;
      ctx.beginPath();
      ctx.moveTo(cx - 15, cy);
      ctx.lineTo(cx + 15, cy);
      ctx.moveTo(cx, cy - 15);
      ctx.lineTo(cx, cy + 15);
      ctx.stroke();

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [cameraId, sector, fps]);

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        width: "100%",
        height: "100%",
        background: "#050B13",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <canvas
        ref={canvasRef}
        width={640}
        height={360}
        style={{
          width: "100%",
          height: "100%",
          objectFit: expanded ? "contain" : "cover",
          display: "block",
        }}
      />
    </div>
  );
}
