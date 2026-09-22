"use client";

import React, { useState, useEffect } from "react";
import {
  Sparkles,
  Search,
  Video,
  Bot,
  Database,
  CheckCircle,
  AlertCircle,
  HelpCircle,
  Send,
  Layers,
  ChevronRight,
  Terminal,
  Activity,
  Radio,
  Shield,
  Car,
  Fence,
  UserCheck,
  Volume2,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { BACKEND_URL } from "@/lib/detectionStream";

interface Feature12QueryEngineProps {
  initialMode?: "surveillance" | "video";
  compact?: boolean;
  defaultQuery?: string;
  title?: string;
}

const CAMERAS = [
  { id: "all", label: "All Live Feeds", icon: Radio, queryPrefix: "Summarize live status across all cameras: " },
  { id: "cam-01", label: "CAM-01 (ByteTrack)", icon: Shield, queryPrefix: "CAM-01: What persons are being tracked right now? " },
  { id: "cam-02", label: "CAM-02 (ANPR Plates)", icon: Car, queryPrefix: "CAM-02: List all vehicles and license plates recognized: " },
  { id: "cam-03", label: "CAM-03 (Night Enhancement)", icon: Activity, queryPrefix: "CAM-03: What is the current perimeter visibility state? " },
  { id: "cam-04", label: "CAM-04 (Virtual Fence)", icon: Fence, queryPrefix: "CAM-04: Are there any approaching or active intrusions across the fence? " },
  { id: "cam-05", label: "CAM-05 (Surveillance)", icon: Layers, queryPrefix: "CAM-05: Show current crowd and object count: " },
  { id: "cam-06", label: "CAM-06 (FaceNet Access)", icon: UserCheck, queryPrefix: "CAM-06: Who is at the checkpoint? Any unauthorized intruders? " },
];

export default function Feature12QueryEngine({
  initialMode = "surveillance",
  compact = false,
  defaultQuery = "",
  title = "AI Intelligence Query Engine (Feature 12)",
}: Feature12QueryEngineProps) {
  const [mode, setMode] = useState<"surveillance" | "video">(initialMode);
  const [query, setQuery] = useState(defaultQuery);
  const [videoFile, setVideoFile] = useState("cam2.mp4");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Changed from single result to array of messages
  const [messages, setMessages] = useState<Array<{role: "user" | "assistant", content: string, error?: boolean}>>([]);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sampleSurveillanceQueries = [
    "Find unauthorized intrusions across Sector 4 in the last 24 hours",
    "Show all vehicle detections and number plate reads",
    "List movement trajectory for suspicious person around perimeter fence",
    "Summarize all high-severity threats and fence violations",
  ];

  const handleAsk = async (queryText?: string) => {
    const textToSubmit = queryText || query;
    if (!textToSubmit.trim()) return;

    // Add user message to history
    setMessages((prev) => [...prev, { role: "user", content: textToSubmit.trim() }]);
    setQuery("");
    setLoading(true);
    setError(null);

    try {
      if (mode === "surveillance") {
        const res = await fetch(`${BACKEND_URL}/api/v1/query/ask`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: textToSubmit.trim() }),
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || "Query execution failed");
        }

        const data = await res.json();
        setMessages((prev) => [...prev, { role: "assistant", content: data.response || data.ai_answer || "No text synthesis generated." }]);
      }
    } catch (err: any) {
      setError(err.message || "Failed to reach AI Query Engine");
      setMessages((prev) => [...prev, { role: "assistant", content: err.message || "Failed to reach AI Query Engine", error: true }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        background: "#FFFFFF",
        border: "1px solid var(--border)",
        borderRadius: "var(--r)",
        overflow: "hidden",
        boxShadow: "var(--sh)",
        display: "flex",
        flexDirection: "column",
        gap: 0,
        height: "100%", // Take up full height
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "10px 14px",
          borderBottom: "1px solid var(--border)",
          background: "#F4F6FB",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 8,
          flexShrink: 0,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div
            style={{
              width: 26,
              height: 26,
              borderRadius: "var(--r)",
              background: "var(--navy-lt)",
              border: "1px solid var(--border)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Sparkles size={14} style={{ color: "var(--navy)" }} />
          </div>
          <div>
            <div style={{ fontSize: 12, fontWeight: 700, color: "var(--navy)", letterSpacing: "0.02em" }}>
              {title}
            </div>
            <div style={{ fontSize: 9.5, color: "var(--text-muted)" }}>
              Natural language intelligence briefing interface
            </div>
          </div>
        </div>
      </div>

      {/* Message History Area */}
      <div 
        style={{ 
          flex: 1, 
          overflowY: "auto", 
          padding: "20px", 
          display: "flex", 
          flexDirection: "column", 
          gap: "16px" 
        }}
      >
        {messages.length === 0 && (
          <div style={{ margin: "auto", textAlign: "center", color: "var(--text-muted)" }}>
            <Bot size={40} style={{ margin: "0 auto 12px", opacity: 0.2 }} />
            <p>How can I help you with BorderEye Intelligence today?</p>
          </div>
        )}
        
        {messages.map((msg, idx) => (
          <div 
            key={idx} 
            style={{
              display: "flex",
              justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
              width: "100%",
              maxWidth: "850px", // Constrain the chat flow width
              margin: "0 auto", // Center the message block horizontally
            }}
          >
            <div
              style={{
                maxWidth: "800px", // ChatGPT-like max width
                width: "fit-content",
                padding: "16px",
                background: msg.role === "user" ? "var(--navy)" : (msg.error ? "var(--crit-lt)" : "#F4F6FB"),
                color: msg.role === "user" ? "#FFFFFF" : (msg.error ? "var(--crit)" : "var(--text)"),
                border: msg.role === "assistant" ? "1px solid var(--border-lt)" : "none",
                borderRadius: "12px",
                borderBottomRightRadius: msg.role === "user" ? "4px" : "12px",
                borderBottomLeftRadius: msg.role === "assistant" ? "4px" : "12px",
                boxShadow: msg.role === "assistant" ? "0 2px 8px rgba(0,0,0,0.02)" : "none",
              }}
            >
              {msg.role === "user" ? (
                <div style={{ fontSize: 14 }}>{msg.content}</div>
              ) : (
                <div
                  style={{
                    fontSize: 14,
                    lineHeight: 1.7,
                    fontFamily: "inherit",
                    whiteSpace: "pre-wrap", // Preserve single newlines as line breaks
                  }}
                  className="prose prose-sm max-w-none"
                >
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ display: "flex", justifyContent: "flex-start", width: "100%", maxWidth: "850px", margin: "0 auto" }}>
             <div
              style={{
                maxWidth: "800px",
                width: "fit-content",
                padding: "16px",
                background: "#F4F6FB",
                border: "1px solid var(--border-lt)",
                borderRadius: "12px",
                borderBottomLeftRadius: "4px",
                color: "var(--text-muted)",
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <Sparkles size={14} className="animate-spin" /> Analyzing feeds...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Bottom Input Area */}
      <div 
        style={{ 
          padding: "16px", 
          borderTop: "1px solid var(--border)",
          background: "#FFFFFF",
          flexShrink: 0
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 10, maxWidth: "900px", margin: "0 auto" }}>
          
          {/* Quick Suggestion Chips */}
          {messages.length === 0 && (
            <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap", justifyContent: "center", marginBottom: 8 }}>
              {sampleSurveillanceQueries.map((sample, i) => (
                <button
                  key={i}
                  onClick={() => {
                    handleAsk(sample);
                  }}
                  style={{
                    padding: "6px 12px",
                    background: "#F4F6FB",
                    border: "1px solid var(--border-lt)",
                    borderRadius: "100px",
                    fontSize: 11,
                    fontWeight: 600,
                    color: "var(--navy)",
                    cursor: "pointer",
                    whiteSpace: "nowrap",
                    transition: "all 0.15s",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = "var(--navy-lt)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = "#F4F6FB";
                  }}
                >
                  {sample}
                </button>
              ))}
            </div>
          )}

          <div style={{ display: "flex", gap: 8 }}>
            <div style={{ position: "relative", flex: 1 }}>
              <input
                type="text"
                placeholder="Message BorderEye AI..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleAsk();
                }}
                style={{
                  width: "100%",
                  padding: "14px 16px 14px 44px",
                  background: "#F9FAFB",
                  border: "1px solid var(--border)",
                  borderRadius: "24px",
                  color: "var(--text)",
                  fontSize: 14,
                  outline: "none",
                  boxShadow: "inset 0 1px 2px rgba(0,0,0,0.02)",
                }}
              />
              <Search
                size={18}
                style={{
                  position: "absolute",
                  left: 16,
                  top: "50%",
                  transform: "translateY(-50%)",
                  color: "var(--text-muted)",
                }}
              />
            </div>
            <button
              onClick={() => handleAsk()}
              disabled={loading || !query.trim()}
              style={{
                width: "50px",
                height: "50px",
                borderRadius: "50%",
                background: "var(--navy)",
                border: "none",
                color: "#FFFFFF",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: loading || !query.trim() ? "not-allowed" : "pointer",
                opacity: loading || !query.trim() ? 0.6 : 1,
                boxShadow: "0 2px 6px rgba(0,0,0,0.1)",
                flexShrink: 0,
              }}
            >
              <Send size={18} style={{ marginLeft: -2 }} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
