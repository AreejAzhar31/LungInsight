import { useState, type ReactNode, type FormEvent } from 'react';
import { ShieldCheck } from 'lucide-react';

// Simple client-side PIN gate for the Admin page. This is a lightweight
// deterrent (matches the current mocked admin.ts, which has no real
// backend authorization yet) — NOT real access control. Real role-based
// access would check an is_admin flag on the authenticated user, enforced
// server-side. Revisit once admin.ts is wired to a real backend.
const ADMIN_PIN = '0000';
const SESSION_KEY = 'lunginsight_admin_unlocked';

export function AdminPinGate({ children }: { children: ReactNode }) {
  const [unlocked, setUnlocked] = useState(() => sessionStorage.getItem(SESSION_KEY) === 'true');
  const [pin, setPin] = useState('');
  const [error, setError] = useState(false);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (pin === ADMIN_PIN) {
      sessionStorage.setItem(SESSION_KEY, 'true');
      setUnlocked(true);
      setError(false);
    } else {
      setError(true);
      setPin('');
    }
  }

  if (unlocked) return <>{children}</>;

  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm rounded-lg border border-line bg-panel p-6 text-center"
      >
        <ShieldCheck className="mx-auto mb-3 h-8 w-8 text-cyan-600" />
        <h2 className="font-display text-lg font-semibold text-ink">Admin access</h2>
        <p className="mt-1 text-sm text-steel">Enter the admin PIN to continue.</p>

        <input
          type="password"
          inputMode="numeric"
          autoFocus
          value={pin}
          onChange={(e) => {
            setPin(e.target.value);
            setError(false);
          }}
          className="mt-4 w-full rounded-md border border-line bg-lightbox px-3 py-2 text-center text-sm tracking-widest text-ink outline-none focus:border-cyan-500"
          placeholder="Enter PIN"
        />
        {error && <p className="mt-2 text-xs text-red-600">Incorrect PIN. Try again.</p>}

        <button
          type="submit"
          className="mt-4 w-full rounded-md bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-700"
        >
          Unlock
        </button>
      </form>
    </div>
  );
}