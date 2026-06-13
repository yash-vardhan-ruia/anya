'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuthStore } from '@/stores/use-auth-store';
import { getInitials } from '@/lib/utils';
import api from '@/lib/api';

// ─── Role labels ─────────────────────────────────────────────────────────────
const ROLE_LABELS: Record<string, string> = {
  admin: 'Administrator',
};

const ROLE_COLORS: Record<string, string> = {
  admin: 'bg-blue-100 text-blue-700 border-blue-200',
};

export default function SettingsPage() {
  const { user, accessToken, updateUser } = useAuthStore();

  // ── Profile state ──────────────────────────────────────────
  const [fullName, setFullName] = useState(user?.name || '');
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMsg, setProfileMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // ── Password change state ──────────────────────────────────
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [passwordMsg, setPasswordMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [showPasswords, setShowPasswords] = useState(false);

  const roleLabel = ROLE_LABELS[user?.role || ''] || user?.role || 'Unknown';
  const roleColorClass = ROLE_COLORS[user?.role || ''] || 'bg-slate-100 text-slate-700 border-slate-200';

  // ── Save display name ──────────────────────────────────────
  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName.trim()) return;
    setProfileSaving(true);
    setProfileMsg(null);
    try {
      // Update the local auth store immediately (optimistic)
      updateUser({ name: fullName.trim() });
      setProfileMsg({ type: 'success', text: 'Display name updated successfully.' });
    } catch {
      setProfileMsg({ type: 'error', text: 'Failed to update profile.' });
    } finally {
      setProfileSaving(false);
    }
  };

  // ── Change password ────────────────────────────────────────
  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMsg(null);

    if (newPassword.length < 8) {
      setPasswordMsg({ type: 'error', text: 'New password must be at least 8 characters.' });
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordMsg({ type: 'error', text: 'Passwords do not match.' });
      return;
    }

    setPasswordSaving(true);
    try {
      // Re-authenticate with current credentials to verify, then update
      const formData = new FormData();
      formData.append('username', user?.email || '');
      formData.append('password', currentPassword);
      await api.post('/auth/login', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      // If login succeeds (current password correct), we know credentials are valid.
      // Note: a dedicated PATCH /auth/me/password endpoint would be ideal — for now,
      // we surface a message asking the user to have an admin update the credential.
      setPasswordMsg({
        type: 'success',
        text: 'Current password verified. To change your password, contact another Administrator to update your account.',
      });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setPasswordMsg({
        type: 'error',
        text: detail || 'Current password is incorrect.',
      });
    } finally {
      setPasswordSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl">
      {/* ── Header ── */}
      <div className="border-b pb-4">
        <h1 className="text-2xl font-extrabold tracking-tight">Account & Profile</h1>
        <p className="text-xs text-muted-foreground mt-1">
          Manage your personal information and account security.
        </p>
      </div>

      {/* ── Profile Overview Card ── */}
      <Card className="border shadow-sm">
        <CardContent className="pt-6">
          <div className="flex items-center gap-5">
            {/* Avatar */}
            <div className="h-16 w-16 rounded-full bg-voxmed-primary flex items-center justify-center text-white text-xl font-bold shadow-md shrink-0">
              {user?.name ? getInitials(user.name) : 'US'}
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-bold truncate">{user?.name || '—'}</h2>
              <p className="text-sm text-muted-foreground truncate">{user?.email || '—'}</p>
              <div className="flex items-center gap-2 mt-2">
                <span
                  className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full border ${roleColorClass}`}
                >
                  {roleLabel}
                </span>
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full border bg-emerald-50 text-emerald-700 border-emerald-200">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  Active
                </span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 mt-6 pt-4 border-t text-xs">
            <div>
              <span className="text-muted-foreground font-medium uppercase tracking-wider">User ID</span>
              <p className="font-mono text-slate-700 dark:text-zinc-300 mt-0.5 truncate">{user?.id || '—'}</p>
            </div>
            <div>
              <span className="text-muted-foreground font-medium uppercase tracking-wider">Member since</span>
              <p className="text-slate-700 dark:text-zinc-300 mt-0.5">
                {user?.createdAt ? new Date(user.createdAt).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' }) : '—'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ── Edit Display Name ── */}
      <Card className="border shadow-sm">
        <CardHeader>
          <CardTitle className="text-base font-bold">Display Name</CardTitle>
          <CardDescription className="text-xs">
            Update the name shown across the platform.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSaveProfile} className="space-y-4">
            {profileMsg && (
              <Alert variant={profileMsg.type === 'error' ? 'destructive' : 'default'} className={profileMsg.type === 'success' ? 'border-emerald-200 bg-emerald-50 text-emerald-800' : ''}>
                <span className="material-symbols-outlined text-sm shrink-0">
                  {profileMsg.type === 'success' ? 'check_circle' : 'error'}
                </span>
                <AlertDescription className="ml-2 text-xs">{profileMsg.text}</AlertDescription>
              </Alert>
            )}
            <div className="flex gap-3">
              <div className="relative flex-1">
                <span className="material-symbols-outlined absolute left-3 top-2.5 text-muted-foreground text-lg">person</span>
                <Input
                  className="pl-10"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Your full name"
                  required
                />
              </div>
              <Button
                type="submit"
                className="gradient-primary px-6 font-semibold"
                disabled={profileSaving || fullName.trim() === user?.name}
              >
                {profileSaving ? (
                  <span className="flex items-center gap-2">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    Saving...
                  </span>
                ) : 'Save'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* ── Change Password ── */}
      <Card className="border shadow-sm">
        <CardHeader>
          <CardTitle className="text-base font-bold">Security</CardTitle>
          <CardDescription className="text-xs">
            Verify your current password. To set a new password, contact another Administrator.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleChangePassword} className="space-y-4">
            {passwordMsg && (
              <Alert variant={passwordMsg.type === 'error' ? 'destructive' : 'default'} className={passwordMsg.type === 'success' ? 'border-emerald-200 bg-emerald-50 text-emerald-800' : ''}>
                <span className="material-symbols-outlined text-sm shrink-0">
                  {passwordMsg.type === 'success' ? 'check_circle' : 'error'}
                </span>
                <AlertDescription className="ml-2 text-xs">{passwordMsg.text}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Current Password
              </label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-2.5 text-muted-foreground text-lg">lock</span>
                <Input
                  className="pl-10 pr-10"
                  type={showPasswords ? 'text' : 'password'}
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="Enter current password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPasswords((v) => !v)}
                  className="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground"
                  tabIndex={-1}
                >
                  <span className="material-symbols-outlined text-lg">
                    {showPasswords ? 'visibility_off' : 'visibility'}
                  </span>
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  New Password
                </label>
                <Input
                  type={showPasswords ? 'text' : 'password'}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Min. 8 characters"
                  minLength={8}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Confirm Password
                </label>
                <Input
                  type={showPasswords ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Repeat new password"
                />
              </div>
            </div>

            <Button
              type="submit"
              variant="outline"
              className="font-semibold"
              disabled={passwordSaving || !currentPassword}
            >
              {passwordSaving ? (
                <span className="flex items-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  Verifying...
                </span>
              ) : 'Verify Password'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* ── Danger Zone ── */}
      <Card className="border border-red-200 shadow-sm">
        <CardHeader>
          <CardTitle className="text-base font-bold text-red-600">Session</CardTitle>
          <CardDescription className="text-xs">
            Sign out of the platform on this device.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            variant="outline"
            className="border-red-200 text-red-600 hover:bg-red-50 hover:text-red-700 font-semibold"
            onClick={() => {
              document.cookie = 'auth-token=; path=/; max-age=0';
              useAuthStore.getState().logout();
              window.location.href = '/login';
            }}
          >
            <span className="material-symbols-outlined text-base mr-2">logout</span>
            Sign Out
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
