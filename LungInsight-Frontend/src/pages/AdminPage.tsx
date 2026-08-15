import { AppShell } from '@/components/layout/AppShell';
import { ListSkeleton } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/States';
import { useAdminUsers } from '@/hooks/useResources';

export function AdminPage() {
  const { data: users, isLoading, isError, refetch } = useAdminUsers();

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="font-display text-2xl font-semibold text-ink">Admin</h1>
        <p className="text-sm text-steel">User accounts and prediction activity.</p>
      </div>

      {isLoading && <ListSkeleton rows={6} />}
      {isError && <ErrorState message="Couldn't load users." onRetry={() => refetch()} />}

      {users && (
        <div className="overflow-hidden rounded-lg border border-line bg-panel">
          <table className="w-full text-sm">
            <thead className="border-b border-line bg-lightbox-dim/50 text-left text-xs uppercase tracking-wide text-steel">
              <tr>
                <th className="px-4 py-3 font-medium">User</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Predictions</th>
                <th className="px-4 py-3 font-medium">Joined</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-lightbox-dim/40">
                  <td className="px-4 py-3">
                    <p className="font-medium text-ink">{u.full_name}</p>
                    <p className="text-xs text-steel-light">{u.email}</p>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={
                        u.is_active
                          ? 'inline-flex items-center gap-1.5 rounded-full bg-cyan-50 px-2.5 py-0.5 text-xs font-medium text-cyan-700'
                          : 'inline-flex items-center gap-1.5 rounded-full bg-lightbox-dim px-2.5 py-0.5 text-xs font-medium text-steel'
                      }
                    >
                      {u.is_active ? 'Active' : 'Deactivated'}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-ink">{u.predictionCount}</td>
                  <td className="px-4 py-3 text-steel">{new Date(u.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AppShell>
  );
}
