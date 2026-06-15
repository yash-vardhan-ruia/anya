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
  admin: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/30 dark:text-blue-400 dark:border-blue-800',
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
      const res = await api.put('/auth/me', { full_name: fullName.trim() }, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      const updatedUser = res.data;
      updateUser({ name: updatedUser.full_name });
      setProfileMsg({ type: 'success', text: 'Display name updated successfully.' });
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setProfileMsg({ type: 'error', text: detail || 'Failed to update profile.' });
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
      await api.put('/auth/me/password', {
        current_password: currentPassword,
        new_password: newPassword,
      }, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });

      setPasswordMsg({
        type: 'success',
        text: 'Password updated successfully.',
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
    <div className="max-w-5xl mx-auto space-y-6">
      {/* ── Header ── */}
      <div className="border-b pb-4 flex flex-col md:flex-row md:items-center md:justify-between gap-2">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight">Account & Settings</h1>
          <p className="text-xs text-muted-foreground mt-1">
            Manage your personal profile, security configuration, and active sessions.
          </p>
        </div>
        <div className="flex items-center gap-2 text-[10px] uppercase font-bold tracking-wider text-muted-foreground bg-slate-50 dark:bg-zinc-900 border px-3 py-1.5 rounded-lg w-fit">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
          Secured Session
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Left Side: Profile Overview & Actions */}
        <div className="space-y-6 lg:col-span-1">
          {/* ── Profile Overview Card ── */}
          <Card className="border shadow-sm overflow-hidden bg-white dark:bg-zinc-900">
            <div className="h-2 bg-gradient-to-r from-voxmed-primary to-indigo-600 w-full" />
            <CardContent className="pt-6">
              <div className="flex flex-col items-center text-center pb-5 border-b border-slate-100 dark:border-zinc-800">
                {/* Avatar with absolute placeholder photo upload overlay */}
                <div className="relative group cursor-pointer mb-4">
                  <div className="h-20 w-20 rounded-full bg-voxmed-primary flex items-center justify-center text-white text-2xl font-black shadow-lg ring-4 ring-offset-2 ring-voxmed-primary/10 transition-transform duration-200 group-hover:scale-105">
                    {user?.name ? getInitials(user.name) : 'US'}
                  </div>
                  <div className="absolute inset-0 rounded-full bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                    <span className="material-symbols-outlined text-white text-lg">photo_camera</span>
                  </div>
                </div>
                
                <h2 className="text-base font-black tracking-tight text-slate-900 dark:text-white truncate max-w-full">
                  {user?.name || '—'}
                </h2>
                <p className="text-xs text-muted-foreground truncate max-w-full mt-0.5">
                  {user?.email || '—'}
                </p>

                <div className="flex items-center justify-center gap-2 mt-3.5">
                  <span className={`inline-flex items-center gap-1 text-[10px] font-bold px-2.5 py-0.5 rounded-full border uppercase tracking-wider ${roleColorClass}`}>
                    {roleLabel}
                  </span>
                  <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2.5 py-0.5 rounded-full border bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/20 dark:text-emerald-400 dark:border-emerald-800 uppercase tracking-wider">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-ping" />
                    Active
                  </span>
                </div>
              </div>

              <div className="space-y-4 pt-5 text-[11px]">
                <div className="flex justify-between items-center py-1">
                  <span className="text-muted-foreground font-semibold uppercase tracking-wider">User ID</span>
                  <span className="font-mono text-slate-650 dark:text-zinc-400 font-medium truncate max-w-[150px]" title={user?.id || ''}>
                    {user?.id || '—'}
                  </span>
                </div>
                <div className="flex justify-between items-center py-1 border-t border-slate-50 dark:border-zinc-800/40">
                  <span className="text-muted-foreground font-semibold uppercase tracking-wider">Member since</span>
                  <span className="text-slate-800 dark:text-zinc-300 font-medium">
                    {user?.createdAt ? new Date(user.createdAt).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' }) : '—'}
                  </span>
                </div>
                <div className="flex justify-between items-center py-1 border-t border-slate-50 dark:border-zinc-800/40">
                  <span className="text-muted-foreground font-semibold uppercase tracking-wider">MFA Security</span>
                  <Badge variant="outline" className="text-[9px] px-1.5 py-0 font-bold text-amber-600 bg-amber-50 border-amber-100 dark:bg-amber-950/20 dark:text-amber-400 dark:border-amber-900 uppercase">
                    Not Set
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* ── Active Sessions Info Card ── */}
          <Card className="border shadow-sm bg-white dark:bg-zinc-900">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-black flex items-center gap-2">
                <span className="material-symbols-outlined text-base text-voxmed-primary">devices</span>
                Session Context
              </CardTitle>
              <CardDescription className="text-[11px] leading-relaxed">
                Your current active browser connection session status.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-[11px]">
              <div className="p-3 bg-slate-50 dark:bg-zinc-800/30 rounded-lg border border-slate-100 dark:border-zinc-850 flex items-start gap-3">
                <span className="material-symbols-outlined text-voxmed-primary text-lg mt-0.5">desktop_windows</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 justify-between">
                    <span className="font-bold text-slate-800 dark:text-zinc-200">Chrome on Windows</span>
                    <span className="text-[9px] text-emerald-600 bg-emerald-50 dark:bg-emerald-950/30 dark:text-emerald-400 font-bold px-1.5 py-0.5 rounded border border-emerald-100 dark:border-emerald-900 uppercase tracking-wide">
                      Active
                    </span>
                  </div>
                  <p className="text-muted-foreground text-[10px] mt-0.5">
                    IP Address: 127.0.0.1 (Localhost)
                  </p>
                  <p className="text-[9px] text-muted-foreground/85 font-light mt-1">
                    Last active: Just now
                  </p>
                </div>
              </div>

              <Button
                variant="outline"
                className="border-red-205 text-red-600 hover:bg-red-50 hover:text-red-700 font-semibold w-full flex justify-center text-xs h-9"
                onClick={() => {
                  document.cookie = 'auth-token=; path=/; max-age=0';
                  useAuthStore.getState().logout();
                  window.location.href = '/login';
                }}
              >
                <span className="material-symbols-outlined text-base mr-2">logout</span>
                Sign Out from Console
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Right Side: Account Forms */}
        <div className="space-y-6 lg:col-span-2">
          {/* ── Edit Display Name ── */}
          <Card className="border shadow-sm bg-white dark:bg-zinc-900">
            <CardHeader className="pb-4">
              <CardTitle className="text-sm font-black flex items-center gap-2">
                <span className="material-symbols-outlined text-base text-voxmed-primary">person</span>
                Display Identity
              </CardTitle>
              <CardDescription className="text-[11px] leading-relaxed">
                Update your public profile display name shown in conversations, logs, and clinical audit records.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              <form onSubmit={handleSaveProfile} className="space-y-4 max-w-xl">
                {profileMsg && (
                  <Alert variant={profileMsg.type === 'error' ? 'destructive' : 'default'} className={profileMsg.type === 'success' ? 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:bg-emerald-950/20 dark:text-emerald-400 dark:border-emerald-900' : ''}>
                    <span className="material-symbols-outlined text-sm shrink-0">
                      {profileMsg.type === 'success' ? 'check_circle' : 'error'}
                    </span>
                    <AlertDescription className="ml-2 text-xs">{profileMsg.text}</AlertDescription>
                  </Alert>
                )}

                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                    Full Name
                  </label>
                  <div className="relative">
                    <span className="material-symbols-outlined absolute left-3 top-2.5 text-muted-foreground text-base">person</span>
                    <Input
                      className="pl-9 h-9 text-xs"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Your full name"
                      required
                    />
                  </div>
                  <p className="text-[10px] text-muted-foreground font-light">
                    Avoid initials or clinical shortcuts to maintain clean audit records.
                  </p>
                </div>

                <div className="pt-2">
                  <Button
                    type="submit"
                    className="gradient-primary px-6 text-xs font-semibold h-9"
                    disabled={profileSaving || fullName.trim() === user?.name || !fullName.trim()}
                  >
                    {profileSaving ? (
                      <span className="flex items-center gap-2">
                        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                        Saving Profile...
                      </span>
                    ) : 'Save Display Identity'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* ── Change Password ── */}
          <Card className="border shadow-sm bg-white dark:bg-zinc-900">
            <CardHeader className="pb-4">
              <CardTitle className="text-sm font-black flex items-center gap-2">
                <span className="material-symbols-outlined text-base text-voxmed-primary">security</span>
                Password Security
              </CardTitle>
              <CardDescription className="text-[11px] leading-relaxed">
                Update your account password. We recommend using a unique phrase of at least 8 characters.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              <form onSubmit={handleChangePassword} className="space-y-4 max-w-xl">
                {passwordMsg && (
                  <Alert variant={passwordMsg.type === 'error' ? 'destructive' : 'default'} className={passwordMsg.type === 'success' ? 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:bg-emerald-950/20 dark:text-emerald-400 dark:border-emerald-900' : ''}>
                    <span className="material-symbols-outlined text-sm shrink-0">
                      {passwordMsg.type === 'success' ? 'check_circle' : 'error'}
                    </span>
                    <AlertDescription className="ml-2 text-xs">{passwordMsg.text}</AlertDescription>
                  </Alert>
                )}

                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                    Current Password
                  </label>
                  <div className="relative">
                    <span className="material-symbols-outlined absolute left-3 top-2.5 text-muted-foreground text-base">lock</span>
                    <Input
                      className="pl-9 pr-9 h-9 text-xs"
                      type={showPasswords ? 'text' : 'password'}
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      placeholder="Enter current password"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPasswords((v) => !v)}
                      className="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground flex items-center"
                      tabIndex={-1}
                    >
                      <span className="material-symbols-outlined text-base">
                        {showPasswords ? 'visibility_off' : 'visibility'}
                      </span>
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                      New Password
                    </label>
                    <Input
                      className="h-9 text-xs"
                      type={showPasswords ? 'text' : 'password'}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="Min. 8 characters"
                      minLength={8}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                      Confirm Password
                    </label>
                    <Input
                      className="h-9 text-xs"
                      type={showPasswords ? 'text' : 'password'}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Repeat new password"
                    />
                  </div>
                </div>

                <div className="pt-2">
                  <Button
                    type="submit"
                    className="gradient-primary px-6 text-xs font-semibold h-9"
                    disabled={passwordSaving || !currentPassword}
                  >
                    {passwordSaving ? (
                      <span className="flex items-center gap-2">
                        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                        Updating Security...
                      </span>
                    ) : 'Update Password'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

