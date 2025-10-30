# State Management Architecture

This directory contains the centralized state management for the Automated Transfer Station application.

## Philosophy

The application follows a **data-centric architecture** where:

1. **All application-level stateful data** is managed through Recoil atoms in this directory
2. **Component-local UI state** (like text input values before submission) can remain in individual components
3. **Stateful business logic** (position, connection, logs, operation configs) is centralized

## State Structure

### Core State Files

#### `appState.ts` - **Primary State Hub**
Contains all centralized application state organized into logical domains:

- **`connectionStateAtom`** - WebSocket connection and host configuration
  - Host IP address
  - Connection ready state
  - Connection status

- **`positionSettingsAtom`** - Position tracking and auto-update settings
  - Current position (x, y, z)
  - Auto-update enabled/disabled
  - Poll rate (Hz)
  - Loading state

- **`cameraStateAtom`** - Camera display and control
  - Selected camera feed
  - Refresh state
  - Error messages
  - Image cache key

- **`logsStateAtom`** - System logs and filters
  - Log entries array
  - Visible log types
  - Packet/outgoing type filters
  - Auto-scroll preference

- **`traceOverStateAtom`** - Trace-over operation configuration
  - Wafer coordinates
  - Operation parameters (magnification, wait times, etc.)
  - Current status

- **`scanFlakesStateAtom`** - Scan flakes operation configuration
  - Flake coordinates
  - Directory selection
  - Input persistence preferences

#### Legacy State Files (to be migrated/deprecated)

- `jsonState.ts` - WebSocket message state (will be merged into connectionStateAtom)
- `hostState.ts` - Host configuration (merged into connectionStateAtom)
- `positionContext.tsx` - Position management (being migrated to positionSettingsAtom)
- `consoleState.ts` - Console messages (deprecated in favor of logsStateAtom)
- `packetTrafficState.ts` - Packet traffic logs (merged into logsStateAtom)

## Usage Patterns

### Reading State
```typescript
import { useRecoilValue } from 'recoil';
import { positionSettingsAtom, cameraStateAtom } from '../state/appState';

function MyComponent() {
  const position = useRecoilValue(positionSettingsAtom);
  const camera = useRecoilValue(cameraStateAtom);

  return <div>X: {position.currentPosition?.x}</div>;
}
```

### Writing State
```typescript
import { useSetRecoilState } from 'recoil';
import { cameraStateAtom } from '../state/appState';

function CameraControls() {
  const setCameraState = useSetRecoilState(cameraStateAtom);

  const selectCamera = (cameraId: string) => {
    setCameraState(prev => ({
      ...prev,
      selectedCamera: cameraId
    }));
  };

  return <button onClick={() => selectCamera('video_feed1')}>Select Camera 1</button>;
}
```

### Reading and Writing
```typescript
import { useRecoilState } from 'recoil';
import { logsStateAtom } from '../state/appState';

function LogControls() {
  const [logsState, setLogsState] = useRecoilState(logsStateAtom);

  const toggleAutoScroll = () => {
    setLogsState(prev => ({
      ...prev,
      autoScroll: !prev.autoScroll
    }));
  };

  return (
    <label>
      <input
        type="checkbox"
        checked={logsState.autoScroll}
        onChange={toggleAutoScroll}
      />
      Auto Scroll
    </label>
  );
}
```

## Guidelines

### What Goes in Centralized State?

✅ **YES** - Store in Recoil atoms:
- Connection status and configuration
- Current position data
- Camera selection and settings
- Log entries and filter preferences
- Operation configurations (trace-over, scan-flakes)
- User preferences (auto-scroll, poll rate, etc.)
- Any data shared between multiple components
- Any data that persists across component unmounts

❌ **NO** - Keep in component useState:
- Form input values before submission
- Temporary UI state (hover states, dropdown open/closed)
- Animation states
- Component-specific loading states for UI feedback
- Validation error messages for forms in progress

### State Organization

Each atom should represent a **cohesive domain** of functionality:
- `connectionStateAtom` - Everything about WebSocket connectivity
- `positionSettingsAtom` - Everything about position tracking
- `logsStateAtom` - Everything about logging and display

### Persistence

State that should persist across sessions should:
1. Use localStorage for initial values (see DEFAULT_POSITION_SETTINGS example)
2. Use useEffect to sync changes back to localStorage

```typescript
useEffect(() => {
  localStorage.setItem('position-poll-rate', position.pollRate.toString());
}, [position.pollRate]);
```

## Migration Path

Components should be gradually migrated to use centralized state:

1. **Phase 1**: Create atoms in `appState.ts` (✅ DONE)
2. **Phase 2**: Update components to read from centralized state
3. **Phase 3**: Update components to write to centralized state
4. **Phase 4**: Remove local useState for migrated data
5. **Phase 5**: Deprecate legacy state files

## Benefits

✅ **Single Source of Truth** - All stateful data in one place
✅ **Easier Debugging** - Can inspect entire app state from Recoil DevTools
✅ **Better Testing** - Can mock entire app state easily
✅ **Reduced Props Drilling** - Components access state directly
✅ **Clearer Architecture** - Explicit separation of UI state vs. business state
