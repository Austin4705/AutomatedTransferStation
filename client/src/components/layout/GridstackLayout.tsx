import React, { useEffect, useRef } from 'react';
import { GridStack } from 'gridstack';
import 'gridstack/dist/gridstack.min.css';
import { useRecoilState } from 'recoil';
import { GridLayoutItem, gridLayoutAtom } from '../../state/gridLayoutState';

interface GridstackLayoutProps {
  children: React.ReactNode;
  onPaletteDrop?: (widgetId: string, position: { x: number; y: number }) => void;
}

export const GridstackLayout: React.FC<GridstackLayoutProps> = ({ children, onPaletteDrop }) => {
  const gridRef = useRef<HTMLDivElement>(null);
  const gridInstanceRef = useRef<GridStack | null>(null);
  const isApplyingExternalLayoutRef = useRef(false);
  const isGridOriginLayoutUpdateRef = useRef(false);
  const [savedLayout, setSavedLayout] = useRecoilState(gridLayoutAtom);

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
      isGridOriginLayoutUpdateRef.current = true;
      setSavedLayout((currentLayout) => {
        const currentById = new Map(currentLayout.map((item) => [item.id, item]));
        return layout.map((item) => {
          const itemId = String(item.id);
          const currentItem = currentById.get(itemId);
          return {
            ...currentItem,
            id: itemId,
            type: currentItem?.type || String(item.type || itemId),
            x: Number(item.x || 0),
            y: Number(item.y || 0),
            w: Number(item.w || 1),
            h: Number(item.h || 1),
          };
        });
      });
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
    if (!grid || !gridRef.current) {
      return;
    }

    if (isGridOriginLayoutUpdateRef.current) {
      isGridOriginLayoutUpdateRef.current = false;
      return;
    }

    isApplyingExternalLayoutRef.current = true;

    const layoutById = new Map(savedLayout.map((item) => [item.id, item]));
    const liveElements = Array.from(gridRef.current.querySelectorAll('.grid-stack-item')) as HTMLElement[];
    const liveIds = new Set(
      liveElements
        .map((element) => element.getAttribute('gs-id'))
        .filter((id): id is string => Boolean(id))
    );

    [...grid.engine.nodes].forEach((node) => {
      const nodeId = String(node.id || '');
      if (node.el && (!node.el.isConnected || !liveIds.has(nodeId))) {
        grid.removeWidget(node.el, false, false);
      }
    });

    if (savedLayout.length === 0) {
      grid.removeAll(false, false);
    }

    liveElements.forEach((element) => {
      const itemId = element.getAttribute('gs-id');
      if (!itemId) {
        return;
      }

      const layoutItem = layoutById.get(itemId);
      if (!layoutItem) {
        return;
      }

      if (!(element as any).gridstackNode) {
        grid.makeWidget(element);
      }
      grid.update(element, {
        id: layoutItem.id,
        x: layoutItem.x,
        y: layoutItem.y,
        w: layoutItem.w,
        h: layoutItem.h,
      });
    });

    window.setTimeout(() => {
      isApplyingExternalLayoutRef.current = false;
    }, 0);
  }, [children, savedLayout]);

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    if (event.dataTransfer.types.includes('application/x-dashboard-widget')) {
      event.preventDefault();
      event.dataTransfer.dropEffect = 'copy';
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    const widgetId = event.dataTransfer.getData('application/x-dashboard-widget');
    if (!widgetId || !gridRef.current || !onPaletteDrop) {
      return;
    }

    event.preventDefault();
    const rect = gridRef.current.getBoundingClientRect();
    const columnWidth = rect.width / 12;
    const x = Math.max(0, Math.min(11, Math.floor((event.clientX - rect.left) / columnWidth)));
    const y = Math.max(0, Math.floor((event.clientY - rect.top) / 80));
    onPaletteDrop(widgetId, { x, y });
  };

  return (
    <div
      className="grid-stack"
      ref={gridRef}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      {children}
    </div>
  );
};

export default GridstackLayout;
