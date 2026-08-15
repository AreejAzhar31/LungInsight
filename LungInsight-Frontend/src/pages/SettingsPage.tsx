import { useState, type FormEvent } from 'react';
import { Check, AlertCircle } from 'lucide-react';
import { AppShell } from '@/components/layout/AppShell';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { useAuth } from '@/context/AuthContext';

export function SettingsPage() {
  const { user, updateProfile } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name ?? '');
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSaving(true);
    try {
      await updateProfile(fullName);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch {
      setError("Couldn't save your changes. Please try again.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="font-display text-2xl font-semibold text-ink">Settings</h1>
        <p className="text-sm text-steel">Manage your account details.</p>
      </div>

      <div className="max-w-lg space-y-6">
        <Card as="section">
          <h2 className="font-display text-sm font-semibold text-ink">Profile</h2>
          <form onSubmit={handleSubmit} className="mt-4 space-y-4">
            <Input id="settings-email" label="Email" value={user?.email ?? ''} disabled />
            <Input
              id="settings-name"
              label="Full name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              disabled={isSaving}
            />
            <div className="flex items-center gap-3">
              <Button type="submit" size="sm" disabled={isSaving}>
                {isSaving ? 'Saving…' : 'Save changes'}
              </Button>
              {saved && (
                <span className="flex items-center gap-1 text-sm text-cyan-600">
                  <Check className="h-4 w-4" />
                  Saved
                </span>
              )}
              {error && (
                <span className="flex items-center gap-1 text-sm text-red-600">
                  <AlertCircle className="h-4 w-4" />
                  {error}
                </span>
              )}
            </div>
          </form>
        </Card>

        <Card as="section">
          <h2 className="font-display text-sm font-semibold text-ink">Notifications</h2>
          <p className="mt-1 text-sm text-steel">
            Notification preferences will be available once the backend supports them.
          </p>
        </Card>
      </div>
    </AppShell>
  );
}
