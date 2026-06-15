import type { NavItem } from '@/types/api';

// ── Sidebar Navigation ───────────────────────────────────────
export const NAV_ITEMS: NavItem[] = [
  { title: 'Overview', href: '/overview', icon: 'dashboard' },
  { title: 'Appointments', href: '/appointments', icon: 'calendar_month' },
  { title: 'Patients', href: '/patients', icon: 'group' },
  { title: 'Doctors', href: '/doctors', icon: 'stethoscope' },
  { title: 'Live Calls', href: '/calls', icon: 'call', badge: 'live' },
  { title: 'Billing', href: '/billing', icon: 'receipt_long' },
  { title: 'Analytics', href: '/analytics', icon: 'analytics' },
  { title: 'Settings', href: '/settings', icon: 'settings' },
];

// ── Status Colors ─────────────────────────────────────────────
export const APPOINTMENT_STATUS_COLORS: Record<string, { bg: string; text: string; dot: string }> = {
  scheduled:   { bg: 'bg-blue-100',   text: 'text-blue-700',   dot: 'bg-blue-500' },
  confirmed:   { bg: 'bg-indigo-100', text: 'text-indigo-700', dot: 'bg-indigo-500' },
  'checked-in':{ bg: 'bg-cyan-100',   text: 'text-cyan-700',   dot: 'bg-cyan-500' },
  'in-progress':{ bg: 'bg-amber-100', text: 'text-amber-700',  dot: 'bg-amber-500' },
  completed:   { bg: 'bg-green-100',  text: 'text-green-700',  dot: 'bg-green-500' },
  cancelled:   { bg: 'bg-red-100',    text: 'text-red-700',    dot: 'bg-red-500' },
  'no-show':   { bg: 'bg-gray-100',   text: 'text-gray-700',   dot: 'bg-gray-500' },
};

export const CALL_STATUS_COLORS: Record<string, { bg: string; text: string; dot: string }> = {
  ringing:      { bg: 'bg-amber-100',  text: 'text-amber-700',  dot: 'bg-amber-500' },
  active:       { bg: 'bg-green-100',  text: 'text-green-700',  dot: 'bg-green-500' },
  'on-hold':    { bg: 'bg-blue-100',   text: 'text-blue-700',   dot: 'bg-blue-500' },
  transferring: { bg: 'bg-purple-100', text: 'text-purple-700', dot: 'bg-purple-500' },
  completed:    { bg: 'bg-gray-100',   text: 'text-gray-700',   dot: 'bg-gray-500' },
  failed:       { bg: 'bg-red-100',    text: 'text-red-700',    dot: 'bg-red-500' },
};

export const INVOICE_STATUS_COLORS: Record<string, { bg: string; text: string; dot: string }> = {
  draft:     { bg: 'bg-gray-100',   text: 'text-gray-700',   dot: 'bg-gray-500' },
  pending:   { bg: 'bg-amber-100',  text: 'text-amber-700',  dot: 'bg-amber-500' },
  paid:      { bg: 'bg-green-100',  text: 'text-green-700',  dot: 'bg-green-500' },
  overdue:   { bg: 'bg-red-100',    text: 'text-red-700',    dot: 'bg-red-500' },
  cancelled: { bg: 'bg-gray-100',   text: 'text-gray-500',   dot: 'bg-gray-400' },
  refunded:  { bg: 'bg-purple-100', text: 'text-purple-700', dot: 'bg-purple-500' },
};

export const SENTIMENT_COLORS: Record<string, string> = {
  positive: 'text-green-600',
  neutral:  'text-gray-500',
  negative: 'text-red-600',
};

export const DOCTOR_STATUS_COLORS: Record<string, { bg: string; text: string; dot: string }> = {
  available: { bg: 'bg-green-100', text: 'text-green-700', dot: 'bg-green-500' },
  busy:      { bg: 'bg-red-100',   text: 'text-red-700',   dot: 'bg-red-500' },
  break:     { bg: 'bg-amber-100', text: 'text-amber-700', dot: 'bg-amber-500' },
  offline:   { bg: 'bg-gray-100',  text: 'text-gray-500',  dot: 'bg-gray-400' },
};



// ── API Config ────────────────────────────────────────────────
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
export const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
