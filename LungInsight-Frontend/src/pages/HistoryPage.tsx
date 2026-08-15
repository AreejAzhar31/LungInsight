import { useState } from 'react';
import { Link } from 'react-router-dom';
import { History as HistoryIcon } from 'lucide-react';
import { AppShell } from '@/components/layout/AppShell';
import { PredictionBadge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { ListSkeleton } from '@/components/ui/Skeleton';
import { ErrorState, EmptyState } from '@/components/ui/States';
import { useHistory } from '@/hooks/useResources';

const PAGE_SIZE = 10;

export function HistoryPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, refetch } = useHistory(page, PAGE_SIZE);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="font-display text-2xl font-semibold text-ink">History</h1>
        <p className="text-sm text-steel">Every prediction made on your account.</p>
      </div>

      {isLoading && <ListSkeleton />}
      {isError && <ErrorState message="Couldn't load history." onRetry={() => refetch()} />}

      {data && data.items.length === 0 && (
        <EmptyState
          title="No predictions yet"
          message="Upload a chest X-ray to see your prediction history here."
          icon={<HistoryIcon className="h-8 w-8" />}
        />
      )}

      {data && data.items.length > 0 && (
        <>
          <div className="overflow-hidden rounded-lg border border-line bg-panel">
            <table className="w-full text-sm">
              <thead className="border-b border-line bg-lightbox-dim/50 text-left text-xs uppercase tracking-wide text-steel">
                <tr>
                  <th className="px-4 py-3 font-medium">Image</th>
                  <th className="px-4 py-3 font-medium">Result</th>
                  <th className="px-4 py-3 font-medium">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {data.items.map((item) => (
                  <tr key={item.prediction_id} className="hover:bg-lightbox-dim/40">
                    <td className="px-4 py-3">
                      <Link
                        to={`/prediction/${item.prediction_id}`}
                        className="font-medium text-ink hover:text-cyan-600 hover:underline"
                      >
                        {item.image_filename}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <PredictionBadge label={item.label} confidence={item.confidence} />
                    </td>
                    <td className="px-4 py-3 text-steel">
                      {new Date(item.created_at).toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-4 flex items-center justify-between text-sm text-steel">
            <span>
              Page {page} of {totalPages} &middot; {data.total} total
            </span>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Previous
              </Button>
              <Button
                variant="secondary"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              >
                Next
              </Button>
            </div>
          </div>
        </>
      )}
    </AppShell>
  );
}
