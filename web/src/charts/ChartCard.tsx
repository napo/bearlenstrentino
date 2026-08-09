import { useEffect, useRef, useState, type ReactNode } from "react";
import ReactECharts from "echarts-for-react";
import type { EChartsOption } from "echarts-for-react";

// Every chart on the site renders through this one wrapper so fullscreen
// and "save as image" behave identically everywhere, instead of each
// chart component reimplementing its own toolbar.
export function ChartCard({
  option,
  height,
  filename,
  id,
  children,
}: {
  option: EChartsOption;
  height: number;
  filename: string;
  id?: string;
  children?: ReactNode;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<ReactECharts>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    const onChange = () => {
      setIsFullscreen(document.fullscreenElement === containerRef.current);
    };
    document.addEventListener("fullscreenchange", onChange);
    return () => document.removeEventListener("fullscreenchange", onChange);
  }, []);

  useEffect(() => {
    // Runs after React has committed the layout change for this state
    // (the flex/height swap between windowed and fullscreen), unlike a
    // resize() called directly from the fullscreenchange handler, which
    // races that commit and measures the stale size.
    window.requestAnimationFrame(() => chartRef.current?.getEchartsInstance().resize());
  }, [isFullscreen]);

  const toggleFullscreen = () => {
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      containerRef.current?.requestFullscreen();
    }
  };

  const saveImage = () => {
    const instance = chartRef.current?.getEchartsInstance();
    if (!instance) return;
    const url = instance.getDataURL({ type: "png", pixelRatio: 2, backgroundColor: "#fff" });
    const link = document.createElement("a");
    link.href = url;
    link.download = `${filename}.png`;
    link.click();
  };

  return (
    <div className="chart-card" ref={containerRef} id={id}>
      <div className="chart-toolbar">
        <button type="button" onClick={saveImage} title="Salva il grafico come immagine">
          Salva immagine
        </button>
        <button type="button" onClick={toggleFullscreen} title="Schermo intero">
          {isFullscreen ? "Esci da schermo intero" : "Schermo intero"}
        </button>
      </div>
      <div style={isFullscreen ? { flex: 1, minHeight: 0 } : undefined}>
        <ReactECharts
          ref={chartRef}
          option={option}
          style={{ height: isFullscreen ? "100%" : height }}
          notMerge
        />
      </div>
      {children}
    </div>
  );
}
