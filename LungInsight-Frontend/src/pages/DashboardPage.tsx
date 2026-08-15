import { Link } from 'react-router-dom';
import { Activity, Percent, Upload as UploadIcon, MessageSquare } from 'lucide-react';
import { AppShell } from '@/components/layout/AppShell';
import { StatCard } from '@/components/ui/Card';
import { StatCardSkeleton, CardSkeleton } from '@/components/ui/Skeleton';
import { ErrorState, EmptyState } from '@/components/ui/States';
import { ConfidenceTrendChart, DistributionChart } from '@/components/dashboard/Charts';
import { PredictionBadge } from '@/components/ui/Badge';
import { useDashboardSummary } from '@/hooks/useResources';

export function DashboardPage() {
  const { data, isLoading, isError, refetch } = useDashboardSummary();

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="font-display text-2xl font-semibold text-ink">Dashboard</h1>
        <p className="text-sm text-steel">An overview of predictions and clinical chats.</p>
      </div>

      {isError && <ErrorState message="Couldn't load dashboard data." onRetry={() => refetch()} />}

      {isLoading && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-2">
            <StatCardSkeleton />
            <StatCardSkeleton />
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <CardSkeleton />
            <CardSkeleton />
          </div>
        </div>
      )}

      {data && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <StatCard
              label="Total predictions"
              value={data.totalPredictions.toLocaleString()}
              hint="All time"
              icon={<Activity className="h-4.5 w-4.5" />}
            />
            <StatCard
              label="Average confidence"
              value={`${data.averageConfidence.toFixed(1)}%`}
              hint="Across all predictions"
              icon={<Percent className="h-4.5 w-4.5" />}
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <ConfidenceTrendChart data={data.confidenceTrend} />
            <DistributionChart data={data.distribution} />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-lg border border-line bg-panel p-5">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="font-display text-sm font-semibold text-ink">Recent uploads</h3>
                <Link to="/history" className="text-xs font-medium text-cyan-600 hover:underline">
                  View all
                </Link>
              </div>
              {data.recentUploads.length === 0 ? (
                <EmptyState
                  title="No uploads yet"
                  message="Upload a chest X-ray to see it appear here."
                  icon={<UploadIcon className="h-8 w-8" />}
                />
              ) : (
                <ul className="divide-y divide-line">
                  {data.recentUploads.map((item) => (
                    <li key={item.prediction_id} className="flex items-center justify-between py-2.5 text-sm">
                      <span className="truncate text-ink">{item.image_filename}</span>
                      <PredictionBadge label={item.label} confidence={item.confidence} />
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="rounded-lg border border-line bg-panel p-5">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="font-display text-sm font-semibold text-ink">Recent chats</h3>
                <Link to="/chat" className="text-xs font-medium text-cyan-600 hover:underline">
                  Open chat
                </Link>
              </div>
              {data.recentChats.length === 0 ? (
                <EmptyState
                  title="No conversations yet"
                  message="Start a chat about a prediction to see it here."
                  icon={<MessageSquare className="h-8 w-8" />}
                />
              ) : (
                <ul className="divide-y divide-line">
                  {data.recentChats.map((session) => (
                    <li key={session.id} className="py-2.5 text-sm">
                      <p className="truncate text-ink">{session.title}</p>
                      <p className="text-xs text-steel-light">
                        {new Date(session.updated_at).toLocaleDateString()}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
