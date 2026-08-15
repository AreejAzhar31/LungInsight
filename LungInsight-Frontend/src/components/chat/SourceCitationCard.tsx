import { BookOpen } from 'lucide-react';
import type { SourceCitation } from '@/types';

export function SourceCitationCard({ citation }: { citation: SourceCitation }) {
  return (
    <div className="flex gap-2.5 rounded-md border border-line bg-lightbox px-3 py-2.5">
      <BookOpen className="mt-0.5 h-3.5 w-3.5 shrink-0 text-cyan-500" aria-hidden />
      <div className="min-w-0">
        <p className="text-xs font-medium text-ink">{citation.title}</p>
        <p className="mt-0.5 line-clamp-2 text-xs text-steel">{citation.snippet}</p>
      </div>
    </div>
  );
}
