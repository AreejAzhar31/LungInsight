import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Upload, History, MessageSquare, Settings, ShieldCheck, Activity } from 'lucide-react';
import clsx from 'clsx';

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/upload', label: 'Upload', icon: Upload },
  { to: '/history', label: 'History', icon: History },
  { to: '/chat', label: 'Chat', icon: MessageSquare },
  { to: '/settings', label: 'Settings', icon: Settings },
  { to: '/admin', label: 'Admin', icon: ShieldCheck },
];

export function Sidebar() {
  return (
    <aside className="hidden w-60 shrink-0 flex-col border-r border-line bg-panel md:flex">
      <div className="flex items-center gap-2 px-5 py-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-cyan-500 text-white">
          <Activity className="h-4.5 w-4.5" aria-hidden />
        </div>
        <span className="font-display text-lg font-semibold text-ink">LungInsight</span>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-2" aria-label="Main navigation">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-cyan-50 text-cyan-700'
                  : 'text-steel hover:bg-lightbox-dim hover:text-ink'
              )
            }
          >
            <Icon className="h-4.5 w-4.5" aria-hidden />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-line px-5 py-4">
        <p className="text-xs text-steel-light">LungInsight AI &copy; 2026</p>
      </div>
    </aside>
  );
}
