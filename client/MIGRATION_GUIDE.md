# Data-Centric Architecture Migration Guide

This guide outlines the migration to a centralized, data-centric state management architecture.

## Overview

The application is being refactored to separate **stateful business data** from **ephemeral UI state**:

- ✅ **Centralized State** (`src/state/appState.ts`) - All business logic and shared data
- ✅ **Component State** (useState) - Temporary UI state only

## Completed Migrations

### ✅ CameraBox
**Before**: Used local useState for camera selection, errors, refresh state
**After**: Uses `cameraStateAtom` from centralized state

```typescript
// OLD
const [selectedCamera, setSelectedCamera] = useState(CAMERA_OPTIONS[0].id);
const [error, setError] = useState<string | null>(null);

// NEW
const [cameraState, setCameraState] = useRecoilState(cameraStateAtom);
const updateCameraState = (updates: Partial<typeof cameraState>) => {
  setCameraState(prev => ({ ...prev, ...updates }));
};
```

### ✅ HostConfigInput
**Before**: Used `hostConfigAtom` (legacy)
**After**: Uses `connectionStateAtom.host` from centralized state

```typescript
// OLD
import { hostConfigAtom } from "../../state/hostState";
const [hostConfig, setHostConfig] = useRecoilState(hostConfigAtom);

// NEW
import { connectionStateAtom } from "../../state/appState";
const [connection, setConnection] = useRecoilState(connectionStateAtom);
```

## Pending Migrations

### 🔄 SystemLogsBox
**Current State** (in component):
- `logs` - Array of log entries
- `visibleLogTypes` - Set of visible log types
- `showUnknownPackets` - Boolean filter
- `showUnknownOutgoing` - Boolean filter
- `selectedPacketTypes` - Set of selected packet types
- `selectedOutgoingTypes` - Set of selected outgoing types
- `definedPacketTypes` - Array of defined packet types
- `autoScroll` - Boolean preference

**Target**: Use `logsStateAtom` from `appState.ts`

**Migration Steps**:
1. Import `logsStateAtom` from `../../state/appState`
2. Replace `const [logs, setLogs] = useState<LogEntry[]>([])` with `const [logsState, setLogsState] = useRecoilState(logsStateAtom)`
3. Update all log manipulation to use `logsState.entries`
4. Update all filter states to use `logsState.visibleLogTypes`, etc.
5. Remove all local useState declarations for logs-related data

**Example**:
```typescript
// OLD
const [logs, setLogs] = useState<LogEntry[]>([]);
const [autoScroll, setAutoScroll] = useState<boolean>(true);

// NEW
const [logsState, setLogsState] = useRecoilState(logsStateAtom);
const updateLogsState = (updates: Partial<LogsState>) => {
  setLogsState(prev => ({ ...prev, ...updates }));
};

// Adding a log entry
updateLogsState({
  entries: [...logsState.entries, newLogEntry]
});

// Toggling auto-scroll
updateLogsState({ autoScroll: !logsState.autoScroll });
```

### 🔄 TraceOverBox
**Current State** (in component):
- `waferCount` - Number of wafers
- `waferCoordinates` - Array of wafer coordinate objects
- `magnification` - Number
- `picsUntilFocus` - Number
- `initialWaitTime` - Number
- `focusWaitTime` - Number
- `cameraIndex` - Number
- `saveImages` - Boolean
- `traceOverStatus` - Result object

**Target**: Use `traceOverStateAtom` from `appState.ts`

**Migration Steps**:
1. Import `traceOverStateAtom` from `../../state/appState`
2. Replace all individual useState with `const [traceOverState, setTraceOverState] = useRecoilState(traceOverStateAtom)`
3. Create helper: `const updateTraceOverState = (updates: Partial<TraceOverState>) => setTraceOverState(prev => ({ ...prev, ...updates }))`
4. Update all state setters to use `updateTraceOverState`

**Example**:
```typescript
// OLD
const [magnification, setMagnification] = useState<number>(20);
const [saveImages, setSaveImages] = useState<boolean>(true);

// NEW
const [traceOverState, setTraceOverState] = useRecoilState(traceOverStateAtom);
const updateTraceOverState = (updates: Partial<TraceOverState>) => {
  setTraceOverState(prev => ({ ...prev, ...updates }));
};

// Update magnification
updateTraceOverState({ magnification: 40 });

// Update multiple values
updateTraceOverState({
  saveImages: false,
  cameraIndex: 1
});
```

### 🔄 ScanFlakesBox
**Current State** (in component):
- `selectedDirectory` - String
- `flakeCoordinates` - Object with x1, y1, x2, y2, spacing_x, spacing_y
- `keepInputs` - Boolean

**Target**: Use `scanFlakesStateAtom` from `appState.ts`

**Migration Steps**:
1. Import `scanFlakesStateAtom` from `../../state/appState`
2. Replace useState declarations with `const [scanFlakesState, setScanFlakesState] = useRecoilState(scanFlakesStateAtom)`
3. Update coordinate handling to use `scanFlakesState.flakeCoordinates`

**Example**:
```typescript
// OLD
const [selectedDirectory, setSelectedDirectory] = useState<string>("");
const [flakeCoordinates, setFlakeCoordinates] = useState<FlakeCoordinates>({...});

// NEW
const [scanFlakesState, setScanFlakesState] = useRecoilState(scanFlakesStateAtom);
const updateScanFlakesState = (updates: Partial<ScanFlakesState>) => {
  setScanFlakesState(prev => ({ ...prev, ...updates }));
};

// Update directory
updateScanFlakesState({ selectedDirectory: "/path/to/dir" });

// Update coordinates
updateScanFlakesState({
  flakeCoordinates: {
    ...scanFlakesState.flakeCoordinates,
    x1: "10.5"
  }
});
```

### 🔄 ConnectionStatus
**Current State**: Uses `jsonStateAtom` for `readyState`

**Target**: Use `connectionStateAtom.readyState` from `appState.ts`

**Migration Steps**:
1. Import `connectionStateAtom` from `../../state/appState`
2. Replace `jsonState.readyState` with `connection.readyState`
3. Update connection logic to write to `connectionStateAtom.isConnected`

**Example**:
```typescript
// OLD
import { jsonStateAtom } from "../../state/jsonState";
const jsonState = useRecoilValue(jsonStateAtom);
const readyState = jsonState.readyState;

// NEW
import { connectionStateAtom } from "../../state/appState";
const connection = useRecoilValue(connectionStateAtom);
const readyState = connection.readyState;
```

### 🔄 Position Management
**Current State**: Uses `PositionContext` (React Context)

**Target**: Migrate to `positionSettingsAtom` from `appState.ts`

**Migration Steps**:
1. Update `positionContext.tsx` to use `positionSettingsAtom` internally
2. OR: Replace `usePositionContext()` calls with `useRecoilState(positionSettingsAtom)`
3. Update polling logic to read/write from atom
4. Update localStorage sync to use atom effects or separate useEffect

**Example**:
```typescript
// OLD (via Context)
const { autoUpdate, setAutoUpdate, pollRate, position } = usePositionContext();

// NEW (direct atom access)
const [positionSettings, setPositionSettings] = useRecoilState(positionSettingsAtom);
const updatePositionSettings = (updates: Partial<PositionSettings>) => {
  setPositionSettings(prev => ({ ...prev, ...updates }));
};

// Toggle auto-update
updatePositionSettings({ autoUpdate: !positionSettings.autoUpdate });

// Update position
updatePositionSettings({ currentPosition: { x: 10, y: 20 } });
```

## Components with Local UI State (Keep as-is)

These components correctly use local useState for ephemeral UI state:

✅ **CommandInputBox** - `command` and `keepText` (form state before submission)
✅ **PacketInputBox** - `packetJson`, `error`, `keepText`, `rows`, `showPlaceholder` (form state)
✅ **TransferStationCommandsBox** - `command`, `parameters`, `keepText` (form state)
✅ **ActionsBox** - `isRefreshing`, `selectedDirectory` (temporary action state)

## Migration Checklist

For each component migration:

- [ ] 1. Identify stateful data in component
- [ ] 2. Determine if it belongs in centralized state (see guidelines in `src/state/README.md`)
- [ ] 3. Import appropriate atom from `appState.ts`
- [ ] 4. Replace `useState` with `useRecoilState`
- [ ] 5. Create `update___State` helper function
- [ ] 6. Replace all `set___` calls with `update___State` calls
- [ ] 7. Update any derived computations to use atom state
- [ ] 8. Remove old useState declarations
- [ ] 9. Test component functionality
- [ ] 10. Verify state persists across component unmount/remount (if applicable)

## Testing Strategy

After migrating each component:

1. **Verify Reads**: Component displays correct data from centralized state
2. **Verify Writes**: User actions update centralized state correctly
3. **Verify Persistence**: State survives component unmount/remount
4. **Verify Sharing**: Multiple components reading same state see updates
5. **Verify localStorage**: Settings that should persist are saved/loaded correctly

## Benefits of Migration

✅ **Single Source of Truth** - All app state in `appState.ts`
✅ **Easier Debugging** - Inspect all state in Recoil DevTools
✅ **Better Testing** - Mock entire app state easily
✅ **State Sharing** - Multiple components can access same data
✅ **Clearer Code** - Obvious separation between business logic and UI state

## Questions?

See `src/state/README.md` for detailed state management guidelines and usage patterns.
