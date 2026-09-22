export type Priority = "critical" | "high" | "medium" | "low";
export type IncidentStatus = "open" | "investigating" | "escalated" | "closed";
export type SceneVariant = "checkpoint" | "road" | "tower" | "fence" | "cargo" | "night";

export interface Incident {
  id: string;
  type: string;
  icon: "watchlist" | "intrusion" | "anpr" | "suspicious" | "fence" | "vehicle" | "human" | "night";
  title: string;
  priority: Priority;
  status: IncidentStatus;
  camera: string;
  sector: string;
  date: string;
  time: string;
  location: string;
  snapshotTime: string;
  confidence: number;
  frameVariant: SceneVariant;
  description: string;
  timeline: { time: string; label: string }[];
  snapshotUrl?: string;
  evidenceNotes?: string;
  operatorNotes?: string;
}

export interface LinkedDetection {
  id: string;
  time: string;
  camera: string;
  type: string;
  confidence: number;
  similarity: number;
  frameVariant: SceneVariant;
  snapshotUrl?: string;
  icon: "watchlist" | "intrusion" | "anpr" | "suspicious" | "fence" | "vehicle" | "human" | "night";
}

export const incidents: Incident[] = [
  {
    id: "INC-2026-089",
    type: "Watchlist Match",
    icon: "watchlist",
    title: "Watchlist Suspect Identified: PERSON_001",
    priority: "critical",
    status: "investigating",
    camera: "CAM_01_GATE_NORTH",
    sector: "Sector 1 (North Gate)",
    date: "07 Sep 2026",
    time: "14:32:04",
    location: "Main North Gate Entry (Sector 1)",
    snapshotTime: "14:32:04",
    confidence: 99.4,
    frameVariant: "checkpoint",
    snapshotUrl: "/snapshots/cam-01_INC-2026-089.jpg",
    description: "Multi-camera Person Re-ID verified subject matching PERSON_001 with 0.998 Re-ID similarity score across CAM_01 and CAM_02.",
    timeline: [
      { time: "14:30:10", label: "Initial person detection at Gate North entry portal" },
      { time: "14:32:04", label: "Re-ID feature match against High-Value Watchlist (99.4%)" },
      { time: "14:32:20", label: "Transit logged entering Plaza steps corridor" },
    ],
    evidenceNotes: "Cross-camera trajectory confirms transit from Gate North to Plaza Steps in 2m 14s.",
    operatorNotes: "Operator dispatched QRF unit to Plaza Entry.",
  },
  {
    id: "INC-2026-088",
    type: "Perimeter Intrusion",
    icon: "intrusion",
    title: "Virtual Perimeter Intrusion",
    priority: "high",
    status: "open",
    camera: "CAM_04_SERVER_ROOM",
    sector: "Sector 4 (Vault)",
    date: "07 Sep 2026",
    time: "14:18:12",
    location: "Server Vault Perimeter (Sector 4)",
    snapshotTime: "14:18:12",
    confidence: 96.2,
    frameVariant: "fence",
    snapshotUrl: "/snapshots/cam-04_INC-2026-088.jpg",
    description: "Subject entered restricted yellow perimeter tripwire zone without authorization credential.",
    timeline: [
      { time: "14:17:50", label: "Subject entered field of view approaching perimeter" },
      { time: "14:18:12", label: "Virtual fence polygon breach detected (confidence 96.2%)" },
      { time: "14:18:30", label: "Automatic lockdown signal triggered" },
    ],
    evidenceNotes: "Optical flow and ByteTrack confirm rapid crossing direction toward Vault door.",
    operatorNotes: "Surveillance lock engaged on Sector 4 corridor.",
  },
  {
    id: "INC-2026-087",
    type: "Acoustic Threat",
    icon: "suspicious",
    title: "Acoustic UAV Detection - Sector 2",
    priority: "high",
    status: "escalated",
    camera: "CAM_02_LOBBY",
    sector: "Sector 2 (Plaza)",
    date: "07 Sep 2026",
    time: "14:05:30",
    location: "Plaza Steps & Outer Courtyard (Sector 2)",
    snapshotTime: "14:05:30",
    confidence: 91.8,
    frameVariant: "road",
    snapshotUrl: "/snapshots/cam-02_INC-2026-090.jpg",
    description: "Blade-pass acoustic harmonics identified approaching micro-UAV (BPF: 168 Hz, ~5,040 RPM).",
    timeline: [
      { time: "14:04:15", label: "Acoustic sensor picked up high-frequency harmonic buzz" },
      { time: "14:05:30", label: "BPF matched DJI Phantom rotor signature (168 Hz)" },
      { time: "14:06:00", label: "Sentry alert escalated to EW unit" },
    ],
    evidenceNotes: "Acoustic sentry triangulation matches heading North-Northwest.",
    operatorNotes: "Electronic countermeasure sentry alerted.",
  },
  {
    id: "INC-2026-090",
    type: "Vehicle Detection",
    icon: "vehicle",
    title: "Unauthorized Vehicle CAM-02",
    priority: "medium",
    status: "investigating",
    camera: "CAM_02_LOBBY",
    sector: "Sector 2 (Plaza)",
    date: "07 Sep 2026",
    time: "13:45:22",
    location: "Plaza Outer Courtyard",
    snapshotTime: "13:45:22",
    confidence: 94.3,
    frameVariant: "road",
    snapshotUrl: "/snapshots/cam-02_INC-2026-093.jpg",
    description: "Unregistered vehicle detected in restricted plaza zone.",
    timeline: [
      { time: "13:45:10", label: "Vehicle entered camera frame" },
      { time: "13:45:22", label: "License plate scan initiated" },
      { time: "13:45:40", label: "Vehicle flagged as unauthorized" },
    ],
    evidenceNotes: "License plate did not match authorized database.",
    operatorNotes: "Security team notified for inspection.",
  },
  {
    id: "INC-2026-091",
    type: "Corridor Activity",
    icon: "human",
    title: "After-Hours Movement CAM-03",
    priority: "medium",
    status: "closed",
    camera: "CAM_03_CORRIDOR_1F",
    sector: "Sector 3 (Corridor 1F)",
    date: "07 Sep 2026",
    time: "22:18:05",
    location: "First Floor Corridor",
    snapshotTime: "22:18:05",
    confidence: 88.7,
    frameVariant: "checkpoint",
    snapshotUrl: "/snapshots/cam-03_INC-2026-091.jpg",
    description: "Personnel movement detected during after-hours period.",
    timeline: [
      { time: "22:17:50", label: "Motion detected in corridor" },
      { time: "22:18:05", label: "Personnel identified as authorized maintenance" },
      { time: "22:18:30", label: "Incident cleared" },
    ],
    evidenceNotes: "Authorized maintenance personnel confirmed via badge scan.",
    operatorNotes: "Routine maintenance activity - no action required.",
  },
  {
    id: "INC-2026-092",
    type: "Suspicious Activity",
    icon: "suspicious",
    title: "Loitering Detected CAM-05",
    priority: "high",
    status: "investigating",
    camera: "CAM_05_PARKING",
    sector: "Sector 5 (Parking)",
    date: "07 Sep 2026",
    time: "16:42:11",
    location: "Parking Lot Zone B",
    snapshotTime: "16:42:11",
    confidence: 92.5,
    frameVariant: "night",
    snapshotUrl: "/snapshots/cam-05_INC-2026-092.jpg",
    description: "Individual loitering near restricted parking zone for extended period.",
    timeline: [
      { time: "16:30:00", label: "Subject entered parking lot" },
      { time: "16:42:11", label: "Loitering behavior detected (12+ minutes stationary)" },
      { time: "16:45:00", label: "Security patrol dispatched" },
    ],
    evidenceNotes: "Subject remained in same position for 15 minutes without vehicle interaction.",
    operatorNotes: "Patrol unit en route to investigate.",
  },
  {
    id: "INC-2026-093",
    type: "Traffic Monitoring",
    icon: "vehicle",
    title: "Heavy Traffic CAM-02",
    priority: "low",
    status: "closed",
    camera: "CAM_02_LOBBY",
    sector: "Sector 2 (Plaza)",
    date: "07 Sep 2026",
    time: "08:15:33",
    location: "Plaza Entry Road",
    snapshotTime: "08:15:33",
    confidence: 97.1,
    frameVariant: "road",
    snapshotUrl: "/snapshots/cam-02_INC-2026-094.jpg",
    description: "Morning rush hour traffic monitoring snapshot.",
    timeline: [
      { time: "08:00:00", label: "Morning peak traffic period began" },
      { time: "08:15:33", label: "Traffic density reached threshold" },
      { time: "08:30:00", label: "Traffic normalized" },
    ],
    evidenceNotes: "Normal morning traffic pattern observed.",
    operatorNotes: "Routine monitoring - no incidents.",
  },
  {
    id: "INC-2026-094",
    type: "Perimeter Check",
    icon: "fence",
    title: "Perimeter Scan CAM-02",
    priority: "low",
    status: "closed",
    camera: "CAM_02_LOBBY",
    sector: "Sector 2 (Plaza)",
    date: "07 Sep 2026",
    time: "12:00:00",
    location: "Plaza Perimeter",
    snapshotTime: "12:00:00",
    confidence: 99.9,
    frameVariant: "checkpoint",
    snapshotUrl: "/snapshots/cam-02_INC-2026-095.jpg",
    description: "Scheduled perimeter integrity verification.",
    timeline: [
      { time: "12:00:00", label: "Automated perimeter scan initiated" },
      { time: "12:00:15", label: "All zones clear" },
      { time: "12:00:30", label: "Scan completed successfully" },
    ],
    evidenceNotes: "All perimeter zones verified secure.",
    operatorNotes: "Scheduled automated scan - all clear.",
  },
];

export const linkedDetections: LinkedDetection[] = [
  { 
    id: "LK-01", 
    time: "14:30:10", 
    camera: "CAM_01_GATE_NORTH", 
    type: "Person Detection", 
    confidence: 99.2, 
    similarity: 100,
    frameVariant: "checkpoint",
    icon: "human",
    snapshotUrl: "/snapshots/cam-01_INC-2026-089.jpg"
  },
  { 
    id: "LK-02", 
    time: "14:32:24", 
    camera: "CAM_02_LOBBY", 
    type: "Cross-Camera Sighting", 
    confidence: 98.7, 
    similarity: 99.8,
    frameVariant: "road",
    icon: "watchlist",
    snapshotUrl: "/snapshots/cam-02_INC-2026-090.jpg"
  },
  { 
    id: "LK-03", 
    time: "14:34:01", 
    camera: "CAM_03_CORRIDOR_1F", 
    type: "Transit Corroboration", 
    confidence: 95.1, 
    similarity: 97.4,
    frameVariant: "checkpoint",
    icon: "human",
    snapshotUrl: "/snapshots/cam-03_INC-2026-091.jpg"
  },
  { 
    id: "LK-04", 
    time: "14:18:12", 
    camera: "CAM_04_SERVER_ROOM", 
    type: "Perimeter Breach", 
    confidence: 96.2, 
    similarity: 94.5,
    frameVariant: "fence",
    icon: "intrusion",
    snapshotUrl: "/snapshots/cam-04_INC-2026-088.jpg"
  },
  { 
    id: "LK-05", 
    time: "16:42:11", 
    camera: "CAM_05_PARKING", 
    type: "Suspicious Activity", 
    confidence: 92.5, 
    similarity: 91.3,
    frameVariant: "night",
    icon: "suspicious",
    snapshotUrl: "/snapshots/cam-05_INC-2026-092.jpg"
  },
  { 
    id: "LK-06", 
    time: "08:15:33", 
    camera: "CAM_02_LOBBY", 
    type: "Vehicle Detected", 
    confidence: 97.1, 
    similarity: 88.7,
    frameVariant: "road",
    icon: "vehicle",
    snapshotUrl: "/snapshots/cam-02_INC-2026-094.jpg"
  },
];
