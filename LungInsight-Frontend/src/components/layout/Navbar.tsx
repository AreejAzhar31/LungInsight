import { useNavigate } from 'react-router-dom';
import { LogOut, User as UserIcon } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/Button';

export function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  return (
    <header className="flex h-16 items-center justify-between border-b border-line bg-panel px-6">
      <div />
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm text-steel">
          <UserIcon className="h-4 w-4" aria-hidden />
          <span>{user?.full_name ?? user?.email ?? 'Guest'}</span>
        </div>
        <Button variant="ghost" size="sm" onClick={handleLogout}>
          <LogOut className="h-4 w-4" aria-hidden />
          Log out
        </Button>
      </div>
    </header>
  );
}
