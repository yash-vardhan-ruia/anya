'use client';

import { useState, useEffect } from 'react';
import { useDashboardStore } from '@/stores/use-dashboard-store';
import { useAuthStore } from '@/stores/use-auth-store';
import api from '@/lib/api';
import { cn, getInitials } from '@/lib/utils';
import { Input } from '@/components/ui/input';
import { Button, buttonVariants } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import { format } from 'date-fns';

export function Header() {
  const { user } = useAuthStore();
  const {
    searchQuery,
    setSearchQuery,
    selectedDepartment,
    setSelectedDepartment,
    dateRange,
    setDateRange,
  } = useDashboardStore();

  // Dynamic departments state
  const [departments, setDepartments] = useState<string[]>([]);

  useEffect(() => {
    let active = true;
    const fetchDepts = async () => {
      try {
        const res = await api.get('/departments');
        const items = res.data?.items || [];
        const names = items.map((d: any) => d.name);
        if (active) {
          setDepartments(names);
        }
      } catch (err) {
        console.error('Failed to fetch departments in header:', err);
      }
    };
    fetchDepts();
    return () => {
      active = false;
    };
  }, []);

  // Notifications start empty — will be populated from real backend events
  const [notifications, setNotifications] = useState<
    { id: string; title: string; desc: string; type: string; time: string; read: boolean }[]
  >([]);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const markAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  return (
    <header className="h-16 border-b border-border bg-white dark:bg-zinc-900 px-6 flex items-center justify-between sticky top-0 z-30 select-none shadow-sm">
      {/* ── LEFT SECTION: SEARCH BAR ── */}
      <div className="flex items-center gap-4 w-96">
        <div className="relative w-full">
          <span className="material-symbols-outlined absolute left-3 top-2.5 text-muted-foreground text-lg pointer-events-none">
            search
          </span>
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search patients, medical records, invoices..."
            className="pl-10 w-full bg-slate-50 border-slate-200 dark:bg-zinc-800 dark:border-zinc-700 h-9 rounded-lg text-sm"
          />
        </div>
      </div>

      {/* ── RIGHT SECTION: FILTERS & CLINICAL UTILITIES ── */}
      <div className="flex items-center gap-4">
        {/* Active Department Selector */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] uppercase font-bold tracking-wider text-muted-foreground">Dept:</span>
          <DropdownMenu>
            <DropdownMenuTrigger
              className={cn(
                buttonVariants({ variant: 'outline', size: 'sm' }),
                "h-9 gap-1.5 px-3 font-medium bg-slate-50 border-slate-200 dark:bg-zinc-800 dark:border-zinc-700 text-xs hover:bg-slate-100 cursor-pointer"
              )}
            >
              <span className="material-symbols-outlined text-base text-voxmed-primary">
                medical_services
              </span>
              {selectedDepartment === 'all' ? 'All Departments' : selectedDepartment}
              <span className="material-symbols-outlined text-xs">keyboard_arrow_down</span>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56 max-h-80 overflow-y-auto custom-scrollbar">
              <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground select-none">Filter Operational Scope</div>
              <div className="-mx-1 my-1 h-px bg-border" />
              <DropdownMenuItem
                className={cn('text-xs cursor-pointer', selectedDepartment === 'all' && 'bg-voxmed-primary/10 font-bold')}
                onClick={() => setSelectedDepartment('all')}
              >
                All Departments
              </DropdownMenuItem>
              {departments.map((dept) => (
                <DropdownMenuItem
                  key={dept}
                  className={cn(
                    'text-xs cursor-pointer',
                    selectedDepartment === dept && 'bg-voxmed-primary/10 font-bold'
                  )}
                  onClick={() => setSelectedDepartment(dept)}
                >
                  {dept}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Date Range Picker */}
        <div className="flex items-center gap-2">
          <Popover>
            <PopoverTrigger
              className={cn(
                buttonVariants({ variant: 'outline', size: 'sm' }),
                "h-9 gap-1.5 px-3 font-medium bg-slate-50 border-slate-200 dark:bg-zinc-800 dark:border-zinc-700 text-xs cursor-pointer"
              )}
            >
              <span className="material-symbols-outlined text-base text-voxmed-primary">
                date_range
              </span>
              {dateRange.from ? (
                dateRange.to ? (
                  <>
                    {format(dateRange.from, 'LLL dd')} - {format(dateRange.to, 'LLL dd')}
                  </>
                ) : (
                  format(dateRange.from, 'LLL dd, y')
                )
              ) : (
                <span>Today (Live)</span>
              )}
              <span className="material-symbols-outlined text-xs">keyboard_arrow_down</span>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0 z-50 shadow-2xl border" align="end">
              <div className="p-3 bg-slate-50 dark:bg-zinc-950 border-b flex justify-between items-center">
                <h4 className="text-xs font-bold text-slate-800 dark:text-zinc-200">Select Date Span</h4>
                <Button
                  variant="ghost"
                  onClick={() => setDateRange({ from: undefined, to: undefined })}
                  className="h-6 px-2 text-[10px] text-muted-foreground hover:text-red-500"
                >
                  Reset (Today)
                </Button>
              </div>
              <Calendar
                mode="range"
                defaultMonth={dateRange.from}
                selected={dateRange}
                onSelect={(val: any) => setDateRange(val || { from: undefined, to: undefined })}
                numberOfMonths={2}
              />
            </PopoverContent>
          </Popover>
        </div>

        {/* Notification bell dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger
            className={cn(
              buttonVariants({ variant: 'ghost', size: 'icon' }),
              "relative h-9 w-9 hover:bg-slate-100 rounded-lg cursor-pointer flex items-center justify-center"
            )}
          >
            <span className="material-symbols-outlined text-[22px] text-slate-700 dark:text-zinc-300">
              notifications
            </span>
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-voxmed-error text-[9px] font-bold text-white leading-none ring-2 ring-white">
                {unreadCount}
              </span>
            )}
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80 p-0 shadow-2xl border">
            <div className="flex items-center justify-between p-3 border-b bg-slate-50 dark:bg-zinc-950">
              <span className="text-xs font-bold">Clinical Notifications</span>
              {unreadCount > 0 && (
                <button
                  onClick={markAllRead}
                  className="text-[10px] font-semibold text-voxmed-primary hover:underline cursor-pointer"
                >
                  Mark all read
                </button>
              )}
            </div>
            <div className="max-h-64 overflow-y-auto custom-scrollbar">
              {notifications.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 gap-2 text-muted-foreground">
                  <span className="material-symbols-outlined text-3xl opacity-40">notifications_none</span>
                  <p className="text-xs">No notifications</p>
                </div>
              ) : (
                notifications.map((notif) => (
                  <div
                    key={notif.id}
                    className={cn(
                      'p-3 border-b text-xs flex gap-3 transition-colors hover:bg-slate-50 dark:hover:bg-zinc-800/50 cursor-default',
                      !notif.read && 'bg-slate-50/50 dark:bg-zinc-800/20'
                    )}
                  >
                    <div
                      className={cn(
                        'h-2 w-2 rounded-full shrink-0 mt-1.5',
                        notif.type === 'warning' && 'bg-amber-500',
                        notif.type === 'success' && 'bg-emerald-500',
                        notif.type === 'info' && 'bg-blue-500'
                      )}
                    />
                    <div className="flex-1 min-w-0">
                      <h5 className={cn('font-semibold truncate', !notif.read && 'text-slate-950 dark:text-white')}>
                        {notif.title}
                      </h5>
                      <p className="text-muted-foreground text-[11px] font-light mt-0.5 leading-normal">
                        {notif.desc}
                      </p>
                      <span className="text-[9px] text-zinc-400 mt-1 block font-light">{notif.time}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </DropdownMenuContent>
        </DropdownMenu>

        <div className="hidden md:block w-px bg-border h-6 shrink-0" />

        {/* User Mini Profile dropdown */}
        <div className="hidden md:flex items-center gap-2">
          <Avatar className="h-8 w-8 ring-2 ring-slate-100">
            <AvatarImage src={user?.avatar} />
            <AvatarFallback className="bg-voxmed-primary text-white text-xs font-semibold">
              {user?.name ? getInitials(user.name) : 'US'}
            </AvatarFallback>
          </Avatar>
          <div className="flex flex-col text-left shrink-0">
            <span className="text-xs font-semibold leading-tight text-slate-800 dark:text-zinc-200">
              {user?.name || 'Loading...'}
            </span>
            <span className="text-[9px] text-muted-foreground font-bold tracking-wider uppercase">
              {user?.role === 'admin' ? 'Administrator' : (user?.role || 'Administrator')}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
