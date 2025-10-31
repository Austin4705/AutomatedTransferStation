import { atom } from 'recoil';

export interface GridLayoutItem {
  id: string;
  x: number;
  y: number;
  w: number;
  h: number;
}

// Local storage effect for persisting grid layout
const localStorageEffect = (key: string) => ({ setSelf, onSet }: any) => {
  const savedValue = localStorage.getItem(key);
  if (savedValue != null) {
    try {
      setSelf(JSON.parse(savedValue));
    } catch (e) {
      console.error('Error parsing saved grid layout:', e);
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

export const gridLayoutAtom = atom<GridLayoutItem[]>({
  key: 'gridLayout',
  default: [],
  effects: [localStorageEffect('gridstack-layout')],
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
