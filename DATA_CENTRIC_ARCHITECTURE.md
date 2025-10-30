# Data-Centric Architecture Overview

## Vision

This codebase is designed around a **data-centric architecture** where all stateful business data is centralized in a single, well-organized location. This makes the application easier to understand, debug, and maintain.

## Architecture Principles

### 1. Centralized State Management

All application-level stateful data resides in **`client/src/state/appState.ts`**

This includes:
- **Connection State** - Host, WebSocket status, connection state
- **Position Data** - Current position, auto-update settings, poll rate
- **Camera State** - Selected camera, refresh status, errors
- **Logs** - All system logs with filters and preferences
- **Operation Configs** - Trace-over and scan-flakes configurations

### 2. Separation of Concerns

**Centralized State (Recoil Atoms)**
- Business logic data
- Shared application state
- User preferences and settings
- Data that persists across component lifecycles

**Component State (useState)**
- Ephemeral UI state
- Form input values (before submission)
- Temporary animation/interaction states
- Component-specific loading indicators

### 3. Single Source of Truth

Instead of scattering state across multiple components:

❌ **Before**:
```
CameraBox: useState for selectedCamera, error, isRefreshing
ActionsBox: useState for selectedDirectory
TraceOverBox: useState for magnification, waferCount, coordinates
ScanFlakesBox: useState for flakeCoordinates, directory
HostConfigInput: separate atom for hostConfig
```

✅ **After**:
```
appState.ts: All stateful data organized by domain
  ├─ connectionStateAtom (host, readyState, isConnected)
  ├─ cameraStateAtom (selectedCamera, error, isRefreshing)
  ├─ positionSettingsAtom (currentPosition, autoUpdate, pollRate)
  ├─ logsStateAtom (entries, filters, preferences)
  ├─ traceOverStateAtom (all trace-over config)
  └─ scanFlakesStateAtom (all scan-flakes config)
```

## Implementation Status

### ✅ Completed

1. **Created Centralized State Structure** ([client/src/state/appState.ts](client/src/state/appState.ts))
   - Defined all state atoms with TypeScript interfaces
   - Organized state by functional domain
   - Added comprehensive JSDoc documentation

2. **State Management Documentation** ([client/src/state/README.md](client/src/state/README.md))
   - Usage patterns and examples
   - Guidelines for what belongs in centralized state
   - Best practices for state organization

3. **Migration Guide** ([client/MIGRATION_GUIDE.md](client/MIGRATION_GUIDE.md))
   - Step-by-step migration instructions
   - Examples for each component
   - Testing checklist

4. **Refactored Components**
   - ✅ **CameraBox** - Now uses `cameraStateAtom`
   - ✅ **HostConfigInput** - Now uses `connectionStateAtom`

### 🔄 Pending Migrations

Components that still need to be migrated to centralized state:

1. **SystemLogsBox** → `logsStateAtom`
   - Migrate log entries array
   - Migrate all filter states
   - Migrate auto-scroll preference

2. **TraceOverBox** → `traceOverStateAtom`
   - Migrate all operation parameters
   - Migrate wafer coordinates
   - Migrate status tracking

3. **ScanFlakesBox** → `scanFlakesStateAtom`
   - Migrate flake coordinates
   - Migrate directory selection
   - Migrate keep inputs preference

4. **ConnectionStatus** → `connectionStateAtom`
   - Use centralized readyState
   - Update isConnected flag

5. **Position Management** → `positionSettingsAtom`
   - Migrate from Context to Recoil atom
   - Update polling logic
   - Maintain localStorage sync

See [MIGRATION_GUIDE.md](client/MIGRATION_GUIDE.md) for detailed migration instructions.

## Directory Structure

```
client/src/
├── state/                          # Centralized State Management
│   ├── appState.ts                # PRIMARY STATE HUB ⭐
│   ├── README.md                  # State management documentation
│   ├── jsonState.ts               # (legacy - to be merged)
│   ├── hostState.ts               # (legacy - deprecated)
│   ├── consoleState.ts            # (legacy - deprecated)
│   └── positionContext.tsx        # (to be migrated to atom)
│
├── components/
│   ├── dashboard/                 # Dashboard components
│   │   ├── CameraBox.tsx         # ✅ Uses cameraStateAtom
│   │   ├── SystemLogsBox.tsx     # 🔄 Needs migration to logsStateAtom
│   │   ├── TraceOverBox.tsx      # 🔄 Needs migration to traceOverStateAtom
│   │   ├── ScanFlakesBox.tsx     # 🔄 Needs migration to scanFlakesStateAtom
│   │   └── ...                    # Other dashboard components
│   │
│   ├── layout/                    # Layout components
│   │   ├── HostConfigInput.tsx   # ✅ Uses connectionStateAtom
│   │   ├── ConnectionStatus.tsx  # 🔄 Needs update to connectionStateAtom
│   │   └── ...                    # Other layout components
│   │
│   └── ui/                        # Reusable UI components
│
└── pages/                         # Page components
```

## Benefits

### 🎯 Clarity
- All stateful data in one predictable location
- Clear separation between business logic and UI state
- Easier for new developers to understand the application

### 🔍 Debuggability
- Can inspect entire app state with Recoil DevTools
- Single location to trace state changes
- Easier to reproduce and fix bugs

### 🧪 Testability
- Can mock entire app state easily
- Consistent testing patterns across components
- Simpler integration tests

### 🔄 Maintainability
- Changes to state structure happen in one place
- Less prop drilling and callback passing
- Easier refactoring with TypeScript safety

### 📊 Data Flow
- Explicit data flow from centralized state to components
- Components act as views of centralized data
- Actions update centralized state, components re-render

## Communication Architecture

```
┌─────────────────────────────────────────┐
│         WebSocket Connection            │
│    (HTTP Camera Routes + WS Data)       │
└─────────────┬───────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────┐
│      Centralized State (Recoil)         │
│                                         │
│  ┌────────────────────────────────┐    │
│  │  connectionStateAtom           │    │
│  │  - host, readyState            │    │
│  └────────────────────────────────┘    │
│                                         │
│  ┌────────────────────────────────┐    │
│  │  positionSettingsAtom          │    │
│  │  - currentPosition, autoUpdate │    │
│  └────────────────────────────────┘    │
│                                         │
│  ┌────────────────────────────────┐    │
│  │  cameraStateAtom               │    │
│  │  - selectedCamera, error       │    │
│  └────────────────────────────────┘    │
│                                         │
│  ┌────────────────────────────────┐    │
│  │  logsStateAtom                 │    │
│  │  - entries, filters            │    │
│  └────────────────────────────────┘    │
│                                         │
│  ┌────────────────────────────────┐    │
│  │  traceOverStateAtom            │    │
│  │  - waferCoords, params         │    │
│  └────────────────────────────────┘    │
│                                         │
│  ┌────────────────────────────────┐    │
│  │  scanFlakesStateAtom           │    │
│  │  - flakeCoords, directory      │    │
│  └────────────────────────────────┘    │
└─────────────┬───────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────┐
│        Dashboard Components             │
│  (Read from atoms, dispatch actions)    │
│                                         │
│  • CameraBox                            │
│  • SystemLogsBox                        │
│  • TraceOverBox                         │
│  • ScanFlakesBox                        │
│  • ActionsBox                           │
│  • CommandInputBox                      │
│  • PacketInputBox                       │
│  • TransferStationCommandsBox           │
└─────────────────────────────────────────┘
```

## Getting Started

### For New Features

1. **Identify Required State**
   - What data needs to persist?
   - Is it shared between components?
   - Does it represent business logic?

2. **Add to Centralized State**
   - Define TypeScript interface in `appState.ts`
   - Create Recoil atom with sensible defaults
   - Document the state purpose

3. **Use in Components**
   ```typescript
   import { useRecoilState } from 'recoil';
   import { myNewStateAtom } from '../state/appState';

   const MyComponent = () => {
     const [myState, setMyState] = useRecoilState(myNewStateAtom);

     const updateMyState = (updates: Partial<typeof myState>) => {
       setMyState(prev => ({ ...prev, ...updates }));
     };

     return <div>{myState.someValue}</div>;
   };
   ```

### For Existing Components

See [MIGRATION_GUIDE.md](client/MIGRATION_GUIDE.md) for step-by-step migration instructions.

## Questions?

- **State Management**: See [client/src/state/README.md](client/src/state/README.md)
- **Migration Help**: See [client/MIGRATION_GUIDE.md](client/MIGRATION_GUIDE.md)
- **Architecture Decisions**: Review this document

## Next Steps

1. Complete pending component migrations (see MIGRATION_GUIDE.md)
2. Deprecate legacy state files (jsonState, hostState, consoleState)
3. Add Recoil DevTools for development
4. Consider adding atom effects for localStorage persistence
5. Write integration tests using centralized state mocking
