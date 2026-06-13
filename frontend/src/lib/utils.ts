import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { format, formatDistanceToNow, parseISO } from 'date-fns';

/** Merge Tailwind classes with clsx */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Format a number as currency (INR) */
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

/** Format a number as USD currency */
export function formatUSD(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

/** Format an ISO date string safely */
export function formatDate(date: string | Date | null | undefined, fmt: string = 'MMM dd, yyyy'): string {
  if (!date) return '—';
  try {
    const d = typeof date === 'string' ? parseISO(date) : date;
    if (d instanceof Date && isNaN(d.getTime())) return '—';
    return format(d, fmt);
  } catch {
    return '—';
  }
}

/** Format date as relative time safely */
export function formatRelativeTime(date: string | Date | null | undefined): string {
  if (!date) return '—';
  try {
    const d = typeof date === 'string' ? parseISO(date) : date;
    if (d instanceof Date && isNaN(d.getTime())) return '—';
    return formatDistanceToNow(d, { addSuffix: true });
  } catch {
    return '—';
  }
}

/** Format seconds into mm:ss */
export function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/** Format a number with compact notation */
export function formatCompact(num: number): string {
  return new Intl.NumberFormat('en', { notation: 'compact' }).format(num);
}

/** Format percentage */
export function formatPercentage(value: number): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;
}

/** Generate initials from a name */
export function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

/** Capitalize first letter */
export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/** Slugify a status string for display */
export function statusLabel(status: string): string {
  return status
    .split('-')
    .map((s) => capitalize(s))
    .join(' ');
}
