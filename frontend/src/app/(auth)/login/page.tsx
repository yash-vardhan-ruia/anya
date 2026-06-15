'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/use-auth-store';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import type { User } from '@/types/api';
import api from '@/lib/api';

// ─── Role labels ─────────────────────────────────────────────────────────────
const ROLE_LABELS: Record<string, string> = {
  super_admin: 'Super Administrator',
  admin: 'Administrator',
  staff: 'Clinical Staff',
};



// ─── Main Login Page ──────────────────────────────────────────────────────────
export default function LoginPage() {
  const router = useRouter();
  const { setAuth, isAuthenticated } = useAuthStore();

  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      // FastAPI OAuth2 form-based login
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);

      const loginRes = await api.post('/auth/login', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const { access_token } = loginRes.data;

      // Fetch authenticated user profile
      const meRes = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${access_token}` },
      });
      const userData = meRes.data;

      // Map backend AdminRole to frontend User role
      const mappedRole: 'admin' | 'doctor' | 'nurse' | 'receptionist' = 'admin';

      const verifiedUser: User = {
        id: userData.id,
        email: userData.email,
        name: userData.full_name,
        role: mappedRole,
        hospitalId: userData.id, // use user's own ID — no hardcoded value
        createdAt: userData.created_at || new Date().toISOString(),
      };

      setAuth(verifiedUser, access_token, access_token);
      document.cookie = `auth-token=${access_token}; path=/; max-age=86400; SameSite=Strict`;
      router.push('/overview');
    } catch (err: any) {
      const backendError = err.response?.data?.detail;
      setError(backendError || 'Invalid email or password. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="border-border shadow-2xl relative overflow-hidden bg-white/75 dark:bg-zinc-900/75 backdrop-blur-md">
      {/* Top accent line */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-voxmed-primary via-blue-500 to-emerald-500" />

      {/* Mobile brand mark */}
      <div className="flex items-center gap-2 mb-0 lg:hidden px-6 pt-6">
        <div className="h-7 w-7 rounded-lg bg-voxmed-primary flex items-center justify-center font-bold text-white text-sm">V</div>
        <span className="text-sm font-bold tracking-tight text-voxmed-primary">VoxMed CareVoice</span>
      </div>

          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-bold tracking-tight">Sign In</CardTitle>
            <CardDescription>
              Enter your hospital-issued credentials to access the platform
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <span className="material-symbols-outlined shrink-0 text-sm">error</span>
                  <AlertTitle className="ml-2">Authentication Failed</AlertTitle>
                  <AlertDescription className="ml-2 text-xs font-light">{error}</AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider" htmlFor="email">
                  Email Address
                </label>
                <div className="relative">
                  <span className="material-symbols-outlined absolute left-3 top-2.5 text-muted-foreground text-lg">mail</span>
                  <Input
                    id="email"
                    className="pl-10"
                    type="email"
                    placeholder="you@hospital.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    autoComplete="email"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider" htmlFor="password">
                  Password
                </label>
                <div className="relative">
                  <span className="material-symbols-outlined absolute left-3 top-2.5 text-muted-foreground text-lg">lock</span>
                  <Input
                    id="password"
                    className="pl-10 pr-10"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="current-password"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((p) => !p)}
                    className="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground transition-colors"
                    tabIndex={-1}
                  >
                    <span className="material-symbols-outlined text-lg">
                      {showPassword ? 'visibility_off' : 'visibility'}
                    </span>
                  </button>
                </div>
              </div>
            </CardContent>

            <CardFooter className="flex flex-col gap-3">
              <Button
                type="submit"
                id="login-submit-btn"
                className="w-full gradient-primary hover:opacity-95 font-medium transition-all"
                disabled={isLoading}
              >
                {isLoading ? (
                  <span className="flex items-center gap-2">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    Signing in...
                  </span>
                ) : (
                  <span className="flex items-center gap-1 justify-center">
                    Sign In
                    <span className="material-symbols-outlined text-sm font-semibold">arrow_right_alt</span>
                  </span>
                )}
              </Button>
            </CardFooter>
          </form>
    </Card>
  );
}
