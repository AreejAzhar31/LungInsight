import clsx from 'clsx';

export function Skeleton({ className }: { className?: string }) {
  return <div className={clsx('animate-pulse rounded-md bg-lightbox-dim', className)} />;
}

export function StatCardSkeleton() {
  return (
    <div className="rounded-lg border border-line bg-panel p-5">
      <Skeleton className="h-3 w-24" />
      <Skeleton className="mt-3 h-8 w-16" />
      <Skeleton className="mt-2 h-3 w-32" />
    </div>
  );
}

export function CardSkeleton({ className }: { className?: string }) {
  return (
    <div className={clsx('rounded-lg border border-line bg-panel p-5', className)}>
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="mt-4 h-40 w-full" />
    </div>
  );
}

export function TableRowSkeleton() {
  return (
    <div className="flex items-center gap-4 border-b border-line px-4 py-3">
      <Skeleton className="h-10 w-10 shrink-0 rounded-md" />
      <Skeleton className="h-4 w-1/4" />
      <Skeleton className="h-4 w-20" />
      <Skeleton className="h-4 w-16" />
    </div>
  );
}

export function ListSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="overflow-hidden rounded-lg border border-line bg-panel">
      {Array.from({ length: rows }, (_, i) => (
        <TableRowSkeleton key={i} />
      ))}
    </div>
  );
}
