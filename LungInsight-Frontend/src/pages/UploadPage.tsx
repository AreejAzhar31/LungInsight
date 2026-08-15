import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { AppShell } from '@/components/layout/AppShell';
import { Uploader } from '@/components/prediction/Uploader';
import { PredictionBadge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { ErrorState } from '@/components/ui/States';
import { useCreatePrediction } from '@/hooks/usePredictions';

export function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const navigate = useNavigate();
  const { mutate, data: result, isPending, isError, reset } = useCreatePrediction();

  function handleClear() {
    setFile(null);
    reset();
  }

  function handleAnalyze() {
    if (!file) return;
    mutate(file);
  }

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="font-display text-2xl font-semibold text-ink">Upload</h1>
        <p className="text-sm text-steel">
          Upload a chest X-ray to run a prediction. Image → preview → analysis → result.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <Uploader
            onFileSelected={setFile}
            selectedFile={file}
            onClear={handleClear}
            disabled={isPending}
          />

          {file && !result && (
            <Button className="mt-4 w-full" onClick={handleAnalyze} disabled={isPending}>
              {isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Analyzing…
                </>
              ) : (
                'Run prediction'
              )}
            </Button>
          )}

          {isError && (
            <div className="mt-4">
              <ErrorState message="The prediction request failed." onRetry={handleAnalyze} />
            </div>
          )}
        </div>

        <div>
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div
                key="result"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className={
                  'viewbox-frame rounded-lg p-6' + (result.label === 'Pneumonia' ? ' viewbox-frame--flag' : '')
                }
              >
                <p className="text-xs font-medium uppercase tracking-wide text-steel">Result</p>
                <div className="mt-2">
                  <PredictionBadge label={result.label} confidence={result.confidence} />
                </div>
                <p className="mt-4 text-sm text-steel">
                  Prediction ID <span className="font-mono text-ink">{result.id}</span>
                </p>
                <p className="mt-1 text-xs text-steel-light">
                  This result is from a mock API call — connect{' '}
                  <code className="font-mono">POST /api/v1/prediction</code> in{' '}
                  <code className="font-mono">src/api/predictions.ts</code> to a live backend to
                  replace it.
                </p>
                <Button
                  variant="secondary"
                  size="sm"
                  className="mt-4"
                  onClick={() => navigate(`/prediction/${result.id}`)}
                >
                  View full details
                </Button>
              </motion.div>
            ) : (
              <motion.div
                key="placeholder"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex h-full min-h-[220px] items-center justify-center rounded-lg border border-dashed border-line px-6 text-center text-sm text-steel-light"
              >
                {isPending
                  ? 'Analyzing X-ray — running inference and generating the Grad-CAM heatmap…'
                  : 'Your prediction result will appear here.'}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </AppShell>
  );
}
