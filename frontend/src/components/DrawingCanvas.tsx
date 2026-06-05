import { useEffect, useRef, useState } from "react";

interface DrawingCanvasProps {
  width?: number;
  height?: number;
  lineWidth?: number;
  onExport: (imageData: string) => void;
  resetKey?: number;
}

interface Point {
  x: number;
  y: number;
}

export function DrawingCanvas({
  width = 400,
  height = 400,
  lineWidth = 3,
  onExport,
  resetKey,
}: DrawingCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const isDrawingRef = useRef(false);
  const strokesRef = useRef<Point[][]>([]);
  const currentPointsRef = useRef<Point[]>([]);
  const [strokeCount, setStrokeCount] = useState(0);

  function drawGuideLines(ctx: CanvasRenderingContext2D) {
    const lines = [
      { y: height * 0.2, label: "ascender" },
      { y: height * 0.4, label: "x-height" },
      { y: height * 0.7, label: "baseline" },
      { y: height * 0.9, label: "descender" },
    ];

    ctx.save();
    for (const line of lines) {
      const isBaseline = line.label === "baseline";
      ctx.strokeStyle = isBaseline ? "rgba(0, 90, 180, 0.35)" : "rgba(0, 90, 180, 0.15)";
      ctx.lineWidth = isBaseline ? 1.5 : 1;
      if (!isBaseline) ctx.setLineDash([6, 4]);
      else ctx.setLineDash([]);
      ctx.beginPath();
      ctx.moveTo(0, line.y);
      ctx.lineTo(width, line.y);
      ctx.stroke();
    }
    ctx.restore();
  }

  function drawAllStrokes() {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, width, height);

    drawGuideLines(ctx);
    ctx.strokeStyle = "#000000";
    ctx.lineWidth = lineWidth;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    for (const pts of strokesRef.current) {
      if (pts.length < 2) continue;
      ctx.beginPath();
      ctx.moveTo(pts[0]!.x, pts[0]!.y);
      for (let i = 1; i < pts.length; i++) {
        ctx.lineTo(pts[i]!.x, pts[i]!.y);
      }
      ctx.stroke();
    }

    // Also draw in-progress stroke
    const curr = currentPointsRef.current;
    if (curr.length >= 2) {
      ctx.beginPath();
      ctx.moveTo(curr[0]!.x, curr[0]!.y);
      for (let i = 1; i < curr.length; i++) {
        ctx.lineTo(curr[i]!.x, curr[i]!.y);
      }
      ctx.stroke();
    }
  }

  useEffect(() => {
    strokesRef.current = [];
    currentPointsRef.current = [];
    setStrokeCount(0);
    drawAllStrokes();
  }, [resetKey]);

  useEffect(() => {
    drawAllStrokes();
  });

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
    isDrawingRef.current = true;
    currentPointsRef.current = [getPos(e)];
  }

  function handleMove(e: React.MouseEvent | React.TouchEvent) {
    if (!isDrawingRef.current) return;
    e.preventDefault();
    const pos = getPos(e);
    currentPointsRef.current.push(pos);

    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!ctx) return;
    const pts = currentPointsRef.current;
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
    if (!isDrawingRef.current) return;
    isDrawingRef.current = false;
    if (currentPointsRef.current.length >= 2) {
      strokesRef.current.push([...currentPointsRef.current]);
    }
    currentPointsRef.current = [];
    setStrokeCount(strokesRef.current.length);
  }

  function handleUndo() {
    strokesRef.current.pop();
    setStrokeCount(strokesRef.current.length);
    drawAllStrokes();
  }

  function handleClear() {
    strokesRef.current = [];
    currentPointsRef.current = [];
    setStrokeCount(0);
    drawAllStrokes();
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
        <button className="btn btn-primary" onClick={handleSubmit} disabled={strokeCount === 0}>
          Submit
        </button>
        <button className="btn" onClick={handleUndo} disabled={strokeCount === 0}>
          Undo
        </button>
        <button className="btn" onClick={handleClear} disabled={strokeCount === 0}>
          Clear
        </button>
      </div>
    </div>
  );
}
