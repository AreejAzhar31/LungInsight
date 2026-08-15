import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, MessageSquareText } from 'lucide-react';
import { AppShell } from '@/components/layout/AppShell';
import { HeatmapViewer } from '@/components/prediction/HeatmapViewer';
import { PredictionBadge } from '@/components/ui/Badge';
import { FeedbackForm } from '@/components/feedback/FeedbackForm';
import { CardSkeleton } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/States';
import { usePrediction, usePredictionImageUrl } from '@/hooks/usePredictions';
import { useStartChatSession } from '@/hooks/useResources';
import { resolveBackendUrl, resolveImageUrl } from '@/lib/urls';

export function PredictionPage() {
  const { id } = useParams<{ id: string }>();
  const { data: prediction, isLoading, isError, refetch } = usePrediction(id);
  const { data: imageUrl } = usePredictionImageUrl(id);
  const navigate = useNavigate();
  const { mutate: startSession, isPending: isStartingChat } = useStartChatSession();

  const askAboutResult = () => {
    if (!prediction) return;
    startSession(prediction.id, {
      onSuccess: (session) =>
        navigate('/chat', { state: { sessionId: session.id, predictionId: prediction.id } }),
    });
  };

  return (
    <AppShell>
      <Link to="/history" className="mb-4 inline-flex items-center gap-1.5 text-sm text-steel hover:text-ink">
        <ArrowLeft className="h-4 w-4" />
        Back to history
      </Link>

      {isLoading && <CardSkeleton />}
      {isError && <ErrorState message="Couldn't load this prediction." onRetry={() => refetch()} />}

      {prediction && (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <HeatmapViewer
              originalImageUrl={resolveImageUrl(imageUrl)}
              heatmapUrl={resolveBackendUrl(prediction.heatmap_path)}
              label={prediction.label}
            />
          </div>

          <div className="space-y-4">
            <div className="rounded-lg border border-line bg-panel p-5">
              <p className="text-xs font-medium uppercase tracking-wide text-steel">Prediction</p>
              <div className="mt-2">
                <PredictionBadge label={prediction.label} confidence={prediction.confidence} />
              </div>
              <dl className="mt-4 space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-steel">Prediction ID</dt>
                  <dd className="font-mono text-xs text-ink">{prediction.id.slice(0, 12)}&hellip;</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-steel">Date</dt>
                  <dd className="text-ink">{new Date(prediction.created_at).toLocaleString()}</dd>
                </div>
              </dl>
            </div>

            <div className="rounded-lg border border-line bg-panel p-5">
              <h3 className="mb-3 font-display text-sm font-semibold text-ink">Leave feedback</h3>
              <FeedbackForm predictionId={prediction.id} />
            </div>

            <button
              onClick={askAboutResult}
              disabled={isStartingChat}
              className="flex w-full items-center justify-center gap-2 rounded-lg border border-line bg-panel px-4 py-3 text-sm font-medium text-cyan-600 hover:bg-lightbox-dim disabled:opacity-50"
            >
              <MessageSquareText className="h-4 w-4" />
              {isStartingChat ? 'Starting…' : 'Ask about this result'}
            </button>
          </div>
        </div>
      )}
    </AppShell>
  );
}
