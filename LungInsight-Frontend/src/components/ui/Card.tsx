import type { ReactNode } from 'react';
import clsx from 'clsx';

interface CardProps {
  children: ReactNode;
  className?: string;
  as?: 'div' | 'section';
}

export function Card({ children, className, as: Tag = 'div' }: CardProps) {
  return (
    <Tag className={clsx('rounded-lg border border-line bg-panel p-5 shadow-sm', className)}>
      {children}
    </Tag>
  );
}

interface StatCardProps {
  label: string;
  value: string;
  hint?: string;
  icon?: ReactNode;
}

export function StatCard({ label, value, hint, icon }: StatCardProps) {
  return (
    <Card className="flex items-start justify-between">
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-steel">{label}</p>
        <p className="mt-2 font-mono text-3xl font-semibold text-ink">{value}</p>
        {hint && <p className="mt-1 text-xs text-steel-light">{hint}</p>}
      </div>
      {icon && <div className="rounded-md bg-cyan-50 p-2 text-cyan-600">{icon}</div>}
    </Card>
  );
}
