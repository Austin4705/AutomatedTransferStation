import { atom } from "recoil";
import { ReadyState } from "react-use-websocket";

/**
 * Centralized Application State
 *
 * This file contains all primary stateful data for the application.
 * Component-specific UI state (like text input values) can remain local,
 * but all application-level state should be managed here.
 */

// ============================================================================
// TYPES & INTERFACES
// ============================================================================

export interface Position {
  x: number;
  y: number;
  z?: number;
  [key: string]: number | undefined;
}

export interface CameraState {
  selectedCamera: string;
  isRefreshing: boolean;
  error: string | null;
  imageKey: number;
  lastSelectedCamera: string;
}

export interface ConnectionState {
  host: string;
  readyState: ReadyState;
  isConnected: boolean;
}

export interface PositionSettings {
  autoUpdate: boolean;
  pollRate: number; // Hz
  currentPosition: Position | null;
  isLoading: boolean;
}

export type LogType = "command" | "response" | "outgoing" | "packet";

export interface LogEntry {
  id: string;
  timestamp: number;
  type: LogType;
  content: string;
  packetType?: string;
  outgoingType?: string;
  metadata?: any;
}

export interface LogsState {
  entries: LogEntry[];
  visibleLogTypes: Set<LogType>;
  showUnknownPackets: boolean;
  showUnknownOutgoing: boolean;
  selectedPacketTypes: Set<string>;
  selectedOutgoingTypes: Set<string>;
  definedPacketTypes: string[];
  autoScroll: boolean;
}

export interface WaferCoordinates {
  id: number;
  topRight: { x: string; y: string };
  topLeft: { x: string; y: string };
  bottomRight: { x: string; y: string };
  bottomLeft: { x: string; y: string };
}

export interface TraceOverState {
  waferCount: number;
  waferCoordinates: WaferCoordinates[];
  magnification: number;
  picsUntilFocus: number;
  initialWaitTime: number;
  focusWaitTime: number;
  cameraIndex: number;
  saveImages: boolean;
  status: TraceOverResult | null;
}

export interface TraceOverResult {
  success: boolean;
  message: string;
  timestamp: number;
}

export interface FlakeCoordinates {
  x1: string;
  y1: string;
  x2: string;
  y2: string;
  spacing_x: string;
  spacing_y: string;
}

export interface ScanFlakesState {
  selectedDirectory: string;
  flakeCoordinates: FlakeCoordinates;
  keepInputs: boolean;
}

// Main Application State Interface
export interface AppState {
  connection: ConnectionState;
  position: PositionSettings;
  camera: CameraState;
  logs: LogsState;
  traceOver: TraceOverState;
  scanFlakes: ScanFlakesState;
}

// ============================================================================
// DEFAULT STATE VALUES
// ============================================================================

const DEFAULT_CAMERA_STATE: CameraState = {
  selectedCamera: "video_feed0",
  isRefreshing: false,
  error: null,
  imageKey: Date.now(),
  lastSelectedCamera: "video_feed0",
};

const DEFAULT_CONNECTION_STATE: ConnectionState = {
  host: typeof window !== 'undefined'
    ? (localStorage.getItem('connection-host') || '127.0.0.1')
    : '127.0.0.1',
  readyState: ReadyState.CLOSED,
  isConnected: false,
};

const DEFAULT_POSITION_SETTINGS: PositionSettings = {
  autoUpdate: typeof window !== 'undefined'
    ? (localStorage.getItem('position-auto-update') === 'true' || localStorage.getItem('position-auto-update') === null)
    : true,
  pollRate: typeof window !== 'undefined'
    ? (parseFloat(localStorage.getItem('position-poll-rate') || '1.0'))
    : 1.0,
  currentPosition: null,
  isLoading: false,
};

const DEFAULT_LOGS_STATE: LogsState = {
  entries: [],
  visibleLogTypes: new Set(["command", "response", "outgoing", "packet"]),
  showUnknownPackets: true,
  showUnknownOutgoing: true,
  selectedPacketTypes: new Set(),
  selectedOutgoingTypes: new Set(),
  definedPacketTypes: [],
  autoScroll: typeof window !== 'undefined'
    ? (localStorage.getItem('logs-auto-scroll') !== 'false')
    : true,
};

const DEFAULT_TRACE_OVER_STATE: TraceOverState = {
  waferCount: 1,
  waferCoordinates: [
    {
      id: 1,
      topRight: { x: "", y: "" },
      topLeft: { x: "", y: "" },
      bottomRight: { x: "", y: "" },
      bottomLeft: { x: "", y: "" }
    }
  ],
  magnification: 20,
  picsUntilFocus: 300,
  initialWaitTime: 8,
  focusWaitTime: 8,
  cameraIndex: 0,
  saveImages: true,
  status: null,
};

const DEFAULT_SCAN_FLAKES_STATE: ScanFlakesState = {
  selectedDirectory: "",
  flakeCoordinates: {
    x1: "",
    y1: "",
    x2: "",
    y2: "",
    spacing_x: "",
    spacing_y: "",
  },
  keepInputs: false,
};

const DEFAULT_APP_STATE: AppState = {
  connection: DEFAULT_CONNECTION_STATE,
  position: DEFAULT_POSITION_SETTINGS,
  camera: DEFAULT_CAMERA_STATE,
  logs: DEFAULT_LOGS_STATE,
  traceOver: DEFAULT_TRACE_OVER_STATE,
  scanFlakes: DEFAULT_SCAN_FLAKES_STATE,
};

// ============================================================================
// RECOIL ATOMS
// ============================================================================

/**
 * Connection State Atom
 * Manages WebSocket connection and host configuration
 */
export const connectionStateAtom = atom<ConnectionState>({
  key: "connectionState",
  default: DEFAULT_CONNECTION_STATE,
});

/**
 * Position Settings Atom
 * Manages position tracking, auto-update, and poll rate
 */
export const positionSettingsAtom = atom<PositionSettings>({
  key: "positionSettings",
  default: DEFAULT_POSITION_SETTINGS,
});

/**
 * Camera State Atom
 * Manages camera selection and display state
 */
export const cameraStateAtom = atom<CameraState>({
  key: "cameraState",
  default: DEFAULT_CAMERA_STATE,
});

/**
 * Logs State Atom
 * Manages all system logs, filters, and display preferences
 */
export const logsStateAtom = atom<LogsState>({
  key: "logsState",
  default: DEFAULT_LOGS_STATE,
});

/**
 * Trace Over State Atom
 * Manages trace-over operation configuration and status
 */
export const traceOverStateAtom = atom<TraceOverState>({
  key: "traceOverState",
  default: DEFAULT_TRACE_OVER_STATE,
});

/**
 * Scan Flakes State Atom
 * Manages scan flakes operation configuration
 */
export const scanFlakesStateAtom = atom<ScanFlakesState>({
  key: "scanFlakesState",
  default: DEFAULT_SCAN_FLAKES_STATE,
});

/**
 * Complete Application State Atom (Optional - for debugging/inspection)
 * This is a read-only view of the entire app state
 */
export const appStateAtom = atom<AppState>({
  key: "appState",
  default: DEFAULT_APP_STATE,
});
