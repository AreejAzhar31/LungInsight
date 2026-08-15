import { useState } from 'react';
import { Star, Check } from 'lucide-react';
import clsx from 'clsx';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Input';
import { useSubmitFeedback } from '@/hooks/useResources';

interface FeedbackFormProps {
  predictionId: string;
}

export function FeedbackForm({ predictionId }: FeedbackFormProps) {
  const [rating, setRating] = useState(0);
  const [hoveredRating, setHoveredRating] = useState(0);
  const [comment, setComment] = useState('');
  const { mutate, isPending, isSuccess } = useSubmitFeedback();

  if (isSuccess) {
    return (
      <div className="flex items-center gap-2 rounded-md bg-cyan-50 px-4 py-3 text-sm text-cyan-700">
        <Check className="h-4 w-4" />
        Thanks — your feedback has been recorded.
      </div>
    );
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (rating === 0) return;
        mutate({ prediction_id: predictionId, rating, comment: comment.trim() || undefined });
      }}
      className="space-y-3"
    >
      <div>
        <p className="mb-1.5 text-sm font-medium text-ink">How accurate was this prediction?</p>
        <div className="flex gap-1" role="radiogroup" aria-label="Rating">
          {[1, 2, 3, 4, 5].map((value) => (
            <button
              key={value}
              type="button"
              role="radio"
              aria-checked={rating === value}
              aria-label={`${value} star${value > 1 ? 's' : ''}`}
              onClick={() => setRating(value)}
              onMouseEnter={() => setHoveredRating(value)}
              onMouseLeave={() => setHoveredRating(0)}
              className="p-0.5"
            >
              <Star
                className={clsx(
                  'h-5 w-5 transition-colors',
                  (hoveredRating || rating) >= value ? 'fill-amber-400 text-amber-400' : 'text-line'
                )}
              />
            </button>
          ))}
        </div>
      </div>
      <Textarea
        placeholder="Optional comment for the clinical team..."
        rows={3}
        value={comment}
        onChange={(e) => setComment(e.target.value)}
      />
      <Button type="submit" size="sm" disabled={rating === 0 || isPending}>
        {isPending ? 'Submitting…' : 'Submit feedback'}
      </Button>
    </form>
  );
}
