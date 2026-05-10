import React, { useEffect, useRef } from 'react';
import { GridStack } from 'gridstack';
import 'gridstack/dist/gridstack.min.css';
import { useRecoilState } from 'recoil';
import { GridLayoutItem, gridLayoutAtom } from '../../state/gridLayoutState';

interface GridstackLayoutProps {
  children: React.ReactNode;
}

export const GridstackLayout: React.FC<GridstackLayoutProps> = ({ children }) => {
  const gridRef = useRef<HTMLDivElement>(null);
  const gridInstanceRef = useRef<GridStack | null>(null);
  const isApplyingExternalLayoutRef = useRef(false);
  const [savedLayout, setSavedLayout] = useRecoilState(gridLayoutAtom);
  const cloneLayout = (layout: GridLayoutItem[]): GridLayoutItem[] =>
    layout.map((item) => ({ ...item }));

  useEffect(() => {
    if (!gridRef.current) return;

    // Initialize GridStack
    const grid = GridStack.init(
      {
        column: 12,
        cellHeight: '80px',
        margin: '12px', // Border spacing between widgets
        resizable: {
          handles: 'e, se, s, sw, w',
        },
        draggable: {
          handle: '.grid-stack-item-drag-handle, .dashboard-box-header',
        },
        animate: true,
        float: true,
        minRow: 1,
        acceptWidgets: false,
      },
      gridRef.current
    );

    gridInstanceRef.current = grid;

    // Save layout on change
    grid.on('change', () => {
      if (isApplyingExternalLayoutRef.current) {
        return;
      }
      const layout = grid.save(false) as any[];
      setSavedLayout(layout);
    });

    // Cleanup
    return () => {
      grid.destroy(false);
    };
  }, []);

  // Expose grid instance for external controls
  useEffect(() => {
    if (gridInstanceRef.current) {
      (window as any).gridstackInstance = gridInstanceRef.current;
    }
  }, []);

  useEffect(() => {
    const grid = gridInstanceRef.current;
    if (!grid || !savedLayout || savedLayout.length === 0) {
      return;
    }

    isApplyingExternalLayoutRef.current = true;
    grid.load(cloneLayout(savedLayout));

    // Allow GridStack change events from user interactions after load finishes.
    window.setTimeout(() => {
      isApplyingExternalLayoutRef.current = false;
    }, 0);
  }, [savedLayout]);

  return (
    <div className="grid-stack" ref={gridRef}>
      {children}
    </div>
  );
};

export default GridstackLayout;
