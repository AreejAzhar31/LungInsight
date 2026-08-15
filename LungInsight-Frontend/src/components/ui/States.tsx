import type { ReactNode } from 'react';
import { AlertTriangle, Inbox } from 'lucide-react';
import { Button } from '@/components/ui/Button';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ title = 'Something went wrong', message, onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-flag-50 bg-flag-50/40 px-6 py-12 text-center">
      <AlertTriangle className="h-8 w-8 text-flag-500" aria-hidden />
      <div>
        <p className="font-display font-semibold text-ink">{title}</p>
        <p className="mt-1 text-sm text-steel">{message}</p>
      </div>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}

interface EmptyStateProps {
  title: string;
  message: string;
  action?: ReactNode;
  icon?: ReactNode;
}

export function EmptyState({ title, message, action, icon }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-line px-6 py-16 text-center">
      <div className="text-steel-light">{icon ?? <Inbox className="h-8 w-8" aria-hidden />}</div>
      <div>
        <p className="font-display font-semibold text-ink">{title}</p>
        <p className="mt-1 text-sm text-steel">{message}</p>
      </div>
      {action}
    </div>
  );
}
