import { useCallback, useEffect, useRef, useState } from "react";

interface DrawingCanvasProps {
  width?: number;
  height?: number;
  lineWidth?: number;
  onExport: (imageData: string) => void;
}

interface Stroke {
  points: Array<{ x: number; y: number }>;
}

export function DrawingCanvas({
  width = 400,
  height = 400,
  lineWidth = 3,
  onExport,
}: DrawingCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [strokes, setStrokes] = useState<Stroke[]>([]);
  const currentStrokeRef = useRef<Stroke>({ points: [] });

  const redraw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, width, height);
    ctx.strokeStyle = "#000000";
    ctx.lineWidth = lineWidth;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    for (const stroke of strokes) {
      const first = stroke.points[0];
      if (stroke.points.length < 2 || !first) continue;
      ctx.beginPath();
      ctx.moveTo(first.x, first.y);
      for (let i = 1; i < stroke.points.length; i++) {
        const pt = stroke.points[i];
        if (pt) ctx.lineTo(pt.x, pt.y);
      }
      ctx.stroke();
    }
  }, [strokes, width, height, lineWidth]);

  useEffect(() => {
    redraw();
  }, [redraw]);

  function getPos(e: React.MouseEvent | React.TouchEvent) {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    const scaleX = width / rect.width;
    const scaleY = height / rect.height;

    if ("touches" in e) {
      const touch = e.touches[0];
      if (!touch) return { x: 0, y: 0 };
      return {
        x: (touch.clientX - rect.left) * scaleX,
        y: (touch.clientY - rect.top) * scaleY,
      };
    }
    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY,
    };
  }

  function handleStart(e: React.MouseEvent | React.TouchEvent) {
    e.preventDefault();
    setIsDrawing(true);
    const pos = getPos(e);
    currentStrokeRef.current = { points: [pos] };
  }

  function handleMove(e: React.MouseEvent | React.TouchEvent) {
    if (!isDrawing) return;
    e.preventDefault();
    const pos = getPos(e);
    currentStrokeRef.current.points.push(pos);

    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!ctx) return;
    const pts = currentStrokeRef.current.points;
    if (pts.length < 2) return;
    ctx.strokeStyle = "#000000";
    ctx.lineWidth = lineWidth;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    const prev = pts[pts.length - 2];
    const curr = pts[pts.length - 1];
    if (!prev || !curr) return;
    ctx.beginPath();
    ctx.moveTo(prev.x, prev.y);
    ctx.lineTo(curr.x, curr.y);
    ctx.stroke();
  }

  function handleEnd() {
    if (!isDrawing) return;
    setIsDrawing(false);
    setStrokes((prev) => [...prev, { ...currentStrokeRef.current }]);
    currentStrokeRef.current = { points: [] };
  }

  function handleUndo() {
    setStrokes((prev) => prev.slice(0, -1));
  }

  function handleClear() {
    setStrokes([]);
  }

  function handleSubmit() {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dataUrl = canvas.toDataURL("image/png");
    const base64 = dataUrl.split(",")[1] ?? "";
    onExport(base64);
  }

  return (
    <div className="canvas-area">
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        className="canvas-box"
        onMouseDown={handleStart}
        onMouseMove={handleMove}
        onMouseUp={handleEnd}
        onMouseLeave={handleEnd}
        onTouchStart={handleStart}
        onTouchMove={handleMove}
        onTouchEnd={handleEnd}
      />
      <div className="actions">
        <button className="btn btn-primary" onClick={handleSubmit} disabled={strokes.length === 0}>
          Submit
        </button>
        <button className="btn" onClick={handleUndo} disabled={strokes.length === 0}>
          Undo
        </button>
        <button className="btn" onClick={handleClear} disabled={strokes.length === 0}>
          Clear
        </button>
      </div>
    </div>
  );
}
