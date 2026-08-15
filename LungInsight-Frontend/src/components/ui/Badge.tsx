import clsx from 'clsx';
import type { PredictionLabel } from '@/types';

interface BadgeProps {
  label: PredictionLabel;
  confidence?: number;
}

export function PredictionBadge({ label, confidence }: BadgeProps) {
  const isFlagged = label === 'Pneumonia';
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold',
        isFlagged ? 'bg-flag-50 text-flag-600' : 'bg-cyan-50 text-cyan-700'
      )}
    >
      <span className={clsx('h-1.5 w-1.5 rounded-full', isFlagged ? 'bg-flag-500' : 'bg-cyan-500')} />
      {label}
      {confidence !== undefined && (
        <span className="font-mono font-normal opacity-80">{confidence.toFixed(1)}%</span>
      )}
    </span>
  );
}
