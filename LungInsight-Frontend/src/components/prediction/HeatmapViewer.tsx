import { useState } from 'react';
import clsx from 'clsx';

interface HeatmapViewerProps {
  originalImageUrl: string;
  heatmapUrl: string | null;
  label: 'Normal' | 'Pneumonia';
}

/**
 * Displays the original X-ray with an optional Grad-CAM heatmap overlay
 * (produced by the AI module, see LungInsight-AI/utils/gradcam.py). This
 * component only renders whatever `heatmapUrl` it's given -- no heatmap
 * generation happens on the frontend.
 */
export function HeatmapViewer({ originalImageUrl, heatmapUrl, label }: HeatmapViewerProps) {
  const [opacity, setOpacity] = useState(0.5);
  const [showOverlay, setShowOverlay] = useState(true);

  return (
    <div className={clsx('viewbox-frame rounded-lg p-4', label === 'Pneumonia' && 'viewbox-frame--flag')}>
      <div className="relative overflow-hidden rounded-md bg-ink">
        <img src={originalImageUrl} alt="Chest X-ray" className="w-full object-contain" />
        {heatmapUrl && showOverlay && (
          <img
            src={heatmapUrl}
            alt="Grad-CAM attention heatmap overlay"
            className="absolute inset-0 w-full object-contain mix-blend-normal"
            style={{ opacity }}
          />
        )}
      </div>

      {heatmapUrl ? (
        <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <label className="flex items-center gap-2 text-sm text-steel">
            <input
              type="checkbox"
              checked={showOverlay}
              onChange={(e) => setShowOverlay(e.target.checked)}
              className="h-4 w-4 accent-cyan-500"
            />
            Show attention heatmap
          </label>
          <div className="flex items-center gap-3">
            <span className="text-xs font-medium text-steel">Overlay opacity</span>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={opacity}
              onChange={(e) => setOpacity(Number(e.target.value))}
              disabled={!showOverlay}
              className="w-32 accent-cyan-500"
              aria-label="Heatmap overlay opacity"
            />
            <span className="w-10 font-mono text-xs text-steel">{Math.round(opacity * 100)}%</span>
          </div>
        </div>
      ) : (
        <p className="mt-3 text-xs text-steel-light">
          No Grad-CAM heatmap available for this prediction yet.
        </p>
      )}
    </div>
  );
}
