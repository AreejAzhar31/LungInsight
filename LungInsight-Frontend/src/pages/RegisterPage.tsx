import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Activity } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';

export function RegisterPage() {
  const { register, isLoading } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    try {
      await register(email, password, fullName || undefined);
      navigate('/dashboard');
    } catch {
      setError('Could not create an account with those details.');
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-lightbox px-4">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="w-full max-w-sm"
      >
        <div className="mb-8 flex flex-col items-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-md bg-cyan-500 text-white">
            <Activity className="h-5 w-5" />
          </div>
          <h1 className="font-display text-xl font-semibold text-ink">Create your account</h1>
          <p className="text-sm text-steel">Start using LungInsight AI</p>
        </div>

        <form onSubmit={handleSubmit} className="viewbox-frame space-y-4 rounded-lg p-6">
          <Input
            id="fullName"
            label="Full name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Jane Doe"
          />
          <Input
            id="email"
            label="Email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@hospital.org"
          />
          <Input
            id="password"
            label="Password"
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="At least 8 characters"
          />
          {error && <p className="text-sm text-flag-600">{error}</p>}
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? 'Creating account…' : 'Create account'}
          </Button>
        </form>

        <p className="mt-5 text-center text-sm text-steel">
          Already have an account?{' '}
          <Link to="/login" className="font-medium text-cyan-600 hover:underline">
            Log in
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
