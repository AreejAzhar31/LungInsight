import { Link } from 'react-router-dom';
import clsx from 'clsx';
import { PredictionBadge } from '@/components/ui/Badge';
import type { Prediction } from '@/types';

interface PredictionCardProps {
  prediction: Prediction;
  imageFilename?: string;
}

export function PredictionCard({ prediction, imageFilename }: PredictionCardProps) {
  const isFlagged = prediction.label === 'Pneumonia';
  const date = new Date(prediction.created_at);

  return (
    <Link
      to={`/prediction/${prediction.id}`}
      className={clsx(
        'viewbox-frame block rounded-lg p-4 transition-shadow hover:shadow-md',
        isFlagged && 'viewbox-frame--flag'
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="truncate text-sm font-medium text-ink">{imageFilename ?? 'Chest X-ray'}</p>
          <p className="mt-0.5 text-xs text-steel-light">
            {date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
          </p>
        </div>
        <PredictionBadge label={prediction.label} confidence={prediction.confidence} />
      </div>
    </Link>
  );
}
