import { Link } from 'react-router-dom';
import { ScanLine } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-lightbox px-4 text-center">
      <div className="viewbox-frame flex h-20 w-20 items-center justify-center rounded-lg bg-panel text-cyan-500">
        <ScanLine className="h-8 w-8" />
      </div>
      <div>
        <p className="font-mono text-sm text-steel">404</p>
        <h1 className="mt-1 font-display text-2xl font-semibold text-ink">This film isn&apos;t on file</h1>
        <p className="mt-2 max-w-sm text-sm text-steel">
          The page you're looking for doesn't exist or may have been moved.
        </p>
      </div>
      <Link to="/">
        <Button>Back to home</Button>
      </Link>
    </div>
  );
}
