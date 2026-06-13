'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuthStore } from '@/stores/use-auth-store';
import { useDashboardStore } from '@/stores/use-dashboard-store';
import { useWebsocket } from '@/hooks/use-websocket';
import { NAV_ITEMS } from '@/lib/constants';
import { cn, getInitials } from '@/lib/utils';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';

export function AppSidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();
  const { sidebarCollapsed, toggleSidebarCollapse } = useDashboardStore();
  const { activeCall } = useWebsocket();

  const handleSignOut = () => {
    // delete cookie and log out
    document.cookie = `auth-token=; path=/; max-age=0`;
    logout();
    window.location.href = '/login';
  };

  return (
    <aside
      className={cn(
        'bg-voxmed-inverse-surface text-[#c8cdd6] h-screen fixed left-0 top-0 z-40 border-r border-[#3a4252] flex flex-col justify-between transition-all duration-300 select-none shadow-2xl',
        sidebarCollapsed ? 'w-[70px]' : 'w-[260px]'
      )}
    >
      {/* ── TOP SECTION: BRAND LOGO & COLLAPSE BUTTON ── */}
      <div>
        <div className={cn('h-16 flex items-center justify-between px-4 border-b border-[#3a4252]')}>
          {!sidebarCollapsed && (
            <Link href="/overview" className="flex items-center gap-3 transition-opacity duration-200">
              <div className="h-8 w-8 rounded-lg bg-voxmed-primary flex items-center justify-center font-bold text-white text-base shadow-lg shadow-voxmed-primary/20">
                V
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-bold tracking-tight text-white leading-none">VoxMed AI</span>
                <span className="text-[10px] text-emerald-400 font-medium tracking-wide mt-1 animate-pulse">
                  CALL CORE ACTIVE
                </span>
              </div>
            </Link>
          )}

          {sidebarCollapsed && (
            <div className="h-8 w-8 rounded-lg bg-voxmed-primary flex items-center justify-center font-bold text-white text-base shadow-lg mx-auto">
              V
            </div>
          )}

          {!sidebarCollapsed && (
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleSidebarCollapse}
              className="text-[#c8cdd6] hover:bg-[#353d4b] hover:text-white h-8 w-8"
            >
              <span className="material-symbols-outlined text-lg">menu_open</span>
            </Button>
          )}
        </div>

        {/* Collapsed sidebar trigger trigger */}
        {sidebarCollapsed && (
          <div className="flex justify-center py-2 border-b border-[#3a4252]">
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleSidebarCollapse}
              className="text-[#c8cdd6] hover:bg-[#353d4b] hover:text-white h-8 w-8"
            >
              <span className="material-symbols-outlined text-lg">menu</span>
            </Button>
          </div>
        )}

        {/* ── MIDDLE SECTION: NAVIGATION ITEMS ── */}
        <nav className="p-3 space-y-1.5 flex-1">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            const isLiveCalls = item.href === '/calls';
            const hasPulse = isLiveCalls && activeCall;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all group relative cursor-pointer',
                  isActive
                    ? 'bg-voxmed-primary text-white font-semibold shadow-md shadow-voxmed-primary/20'
                    : 'hover:bg-[#353d4b] hover:text-white text-[#c8cdd6]'
                )}
              >
                {/* Visual marker bar for active item */}
                {isActive && !sidebarCollapsed && (
                  <span className="absolute left-0 top-2.5 bottom-2.5 w-1 rounded-r-md bg-white"></span>
                )}

                {/* Animated active-call green pulse ring on icon background */}
                <div className="relative flex items-center justify-center">
                  <span
                    className={cn(
                      'material-symbols-outlined text-[22px]',
                      isActive ? 'text-white' : 'text-[#8b92a0] group-hover:text-white',
                      hasPulse && 'pulse-ring text-emerald-400'
                    )}
                  >
                    {item.icon}
                  </span>
                </div>

                {/* Nav text */}
                {!sidebarCollapsed && (
                  <span className="flex-1 truncate tracking-wide">{item.title}</span>
                )}

                {/* Badge notifications: Live, or count, etc. */}
                {!sidebarCollapsed && item.badge && (
                  <span
                    className={cn(
                      'text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full select-none',
                      isLiveCalls
                        ? hasPulse
                          ? 'bg-emerald-600/90 text-white animate-bounce'
                          : 'bg-[#353d4b] text-[#8b92a0]'
                        : 'bg-voxmed-primary text-white'
                    )}
                  >
                    {isLiveCalls && hasPulse ? 'active' : item.badge}
                  </span>
                )}

                {/* Hover Tooltip when sidebar is collapsed */}
                {sidebarCollapsed && (
                  <div className="absolute left-16 scale-0 rounded bg-[#111318] px-2.5 py-1.5 text-xs text-white group-hover:scale-100 transition-all duration-150 z-50 whitespace-nowrap shadow-xl border border-[#2a313d] pointer-events-none">
                    {item.title}
                    {item.badge && ` (${item.badge})`}
                  </div>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* ── BOTTOM SECTION: USER PROFILE & SIGN OUT ── */}
      <div className="p-3 border-t border-[#3a4252] bg-[#1f2633]/40">
        <div className={cn('flex items-center gap-3', sidebarCollapsed ? 'justify-center' : 'px-1')}>
          <Avatar className="h-9 w-9 border-2 border-voxmed-primary/30 shadow-md">
            <AvatarImage src={user?.avatar} alt={user?.name || 'User'} />
            <AvatarFallback className="bg-voxmed-primary text-white font-semibold text-xs">
              {user?.name ? getInitials(user.name) : 'US'}
            </AvatarFallback>
          </Avatar>

          {!sidebarCollapsed && (
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-semibold text-white truncate leading-tight">
                {user?.name || 'Loading Staff...'}
              </h4>
              <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider mt-0.5">
                {user?.role === 'admin' ? 'Administrator' : (user?.role || 'Administrator')}
              </p>
            </div>
          )}

          {!sidebarCollapsed && (
            <Button
              variant="ghost"
              size="icon"
              onClick={handleSignOut}
              className="text-[#8b92a0] hover:text-red-400 hover:bg-red-500/10 h-8 w-8"
              title="Sign Out"
            >
              <span className="material-symbols-outlined text-lg">logout</span>
            </Button>
          )}
        </div>

        {sidebarCollapsed && (
          <div className="flex justify-center mt-3 border-t border-[#3a4252]/50 pt-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={handleSignOut}
              className="text-[#8b92a0] hover:text-red-400 hover:bg-red-500/10 h-7 w-7"
              title="Sign Out"
            >
              <span className="material-symbols-outlined text-base">logout</span>
            </Button>
          </div>
        )}
      </div>
    </aside>
  );
}
