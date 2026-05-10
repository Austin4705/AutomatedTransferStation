import { atom } from 'recoil';

export interface GridLayoutItem {
  id: string;
  type: string;
  x: number;
  y: number;
  w: number;
  h: number;
}

const localStorageEffect = (key: string) => ({ setSelf, onSet }: any) => {
  const savedValue = localStorage.getItem(key);
  if (savedValue != null) {
    try {
      setSelf(JSON.parse(savedValue));
    } catch (e) {
      console.error(`Error parsing localStorage value for ${key}:`, e);
    }
  }

  onSet((newValue: any, _: any, isReset: boolean) => {
    if (isReset) {
      localStorage.removeItem(key);
    } else {
      localStorage.setItem(key, JSON.stringify(newValue));
    }
  });
};

export const DEFAULT_DASHBOARD_LAYOUT: GridLayoutItem[] = [
  { id: 'camera-1', type: 'camera', x: 0, y: 0, w: 6, h: 6 },
  { id: 'camera-2', type: 'camera', x: 6, y: 0, w: 6, h: 6 },
  { id: 'trace-over', type: 'trace-over', x: 0, y: 6, w: 6, h: 5 },
  { id: 'scan-flakes', type: 'scan-flakes', x: 6, y: 6, w: 6, h: 5 },
  { id: 'goto-flake', type: 'goto-flake', x: 0, y: 11, w: 4, h: 4 },
  { id: 'commands', type: 'commands', x: 4, y: 11, w: 4, h: 4 },
  { id: 'control-panel', type: 'control-panel', x: 0, y: 15, w: 4, h: 6 },
  { id: 'trace-over-area', type: 'trace-over-area', x: 4, y: 15, w: 8, h: 6 },
  { id: 'packets', type: 'packets', x: 8, y: 11, w: 4, h: 4 },
  { id: 'logs', type: 'logs', x: 0, y: 21, w: 12, h: 6 },
];

export const gridLayoutAtom = atom<GridLayoutItem[]>({
  key: 'gridLayout',
  default: [],
});

export interface SavedDashboardLayout {
  id: string;
  name: string;
  layout: GridLayoutItem[];
  created_at?: string;
  updated_at?: string;
}

export interface DashboardLayoutConfigState {
  initialLayout: GridLayoutItem[];
  savedLayouts: SavedDashboardLayout[];
  activeLayoutId: string | null;
  isLoaded: boolean;
}

export const dashboardLayoutConfigAtom = atom<DashboardLayoutConfigState>({
  key: 'dashboardLayoutConfig',
  default: {
    initialLayout: [],
    savedLayouts: [],
    activeLayoutId: null,
    isLoaded: false,
  },
});

// Atom to control visibility of widgets
export const widgetVisibilityAtom = atom<Record<string, boolean>>({
  key: 'widgetVisibility',
  default: {
    'camera-primary': true,
    'camera-secondary': true,
    'trace-over': true,
    'scan-flakes': true,
    'actions': true,
    'commands': true,
    'ts-commands': true,
    'packets': true,
    'logs': true,
  },
  effects: [localStorageEffect('widget-visibility')],
});
