import React from 'react';

interface GridstackWidgetProps {
  id: string;
  x?: number;
  y?: number;
  w?: number;
  h?: number;
  minW?: number;
  minH?: number;
  maxW?: number;
  maxH?: number;
  noResize?: boolean;
  noMove?: boolean;
  locked?: boolean;
  children: React.ReactNode;
  className?: string;
}

export const GridstackWidget: React.FC<GridstackWidgetProps> = ({
  id,
  x = 0,
  y = 0,
  w = 4,
  h = 4,
  minW = 2,
  minH = 2,
  maxW,
  maxH,
  noResize = false,
  noMove = false,
  locked = false,
  children,
  className = '',
}) => {
  return (
    <div
      className={`grid-stack-item ${className}`}
      gs-id={id}
      gs-x={x}
      gs-y={y}
      gs-w={w}
      gs-h={h}
      gs-min-w={minW}
      gs-min-h={minH}
      gs-max-w={maxW}
      gs-max-h={maxH}
      gs-no-resize={noResize}
      gs-no-move={noMove}
      gs-locked={locked}
    >
      <div className="grid-stack-item-content">
        {children}
      </div>
    </div>
  );
};

export default GridstackWidget;
