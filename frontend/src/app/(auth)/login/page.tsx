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

// ─── Register staff form (only shown when mode === 'register') ────────────────
function RegisterForm({ onBack }: { onBack: () => void }) {
  const { accessToken } = useAuthStore();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const role = 'admin';
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      await api.post(
        '/auth/register',
        { full_name: fullName, email, password, role },
        { headers: { Authorization: `Bearer ${accessToken}` } },
      );
      setSuccess(true);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(detail || 'Failed to create account. Ensure you are logged in as an Administrator.');
    } finally {
      setIsLoading(false);
    }
  };

  if (success) {
    return (
      <div className="text-center space-y-4 py-6">
        <div className="h-14 w-14 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center mx-auto">
          <span className="material-symbols-outlined text-3xl text-emerald-600">check_circle</span>
        </div>
        <div>
          <h3 className="font-bold text-lg">Account Created</h3>
          <p className="text-sm text-muted-foreground mt-1">
            <span className="font-medium">{email}</span> can now log in with their credentials.
          </p>
        </div>
        <Button
          variant="outline"
          className="w-full"
          onClick={onBack}
        >
          Back to Login
        </Button>
      </div>
    );
  }

  return (
    <form onSubmit={handleRegister} className="space-y-4">
      <CardHeader className="px-0 pt-0">
        <CardTitle className="text-2xl font-bold tracking-tight">Register Administrator</CardTitle>
        <CardDescription>
          Create a new Administrator account. Requires a logged-in Administrator.
        </CardDescription>
      </CardHeader>

      {error && (
        <Alert variant="destructive">
          <span className="material-symbols-outlined shrink-0 text-sm">error</span>
          <AlertTitle className="ml-2">Registration Failed</AlertTitle>
          <AlertDescription className="ml-2 text-xs font-light">{error}</AlertDescription>
        </Alert>
      )}

      <div className="space-y-2">
        <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider" htmlFor="reg-name">
          Full Name
        </label>
        <div className="relative">
          <span className="material-symbols-outlined absolute left-3 top-2.5 text-muted-foreground text-lg">person</span>
          <Input
            id="reg-name"
            className="pl-10"
            type="text"
            placeholder="Dr. Aisha Sharma"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
          />
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider" htmlFor="reg-email">
          Email Address
        </label>
        <div className="relative">
          <span className="material-symbols-outlined absolute left-3 top-2.5 text-muted-foreground text-lg">mail</span>
          <Input
            id="reg-email"
            className="pl-10"
            type="email"
            placeholder="staff@hospital.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider" htmlFor="reg-password">
          Password
        </label>
        <div className="relative">
          <span className="material-symbols-outlined absolute left-3 top-2.5 text-muted-foreground text-lg">lock</span>
          <Input
            id="reg-password"
            className="pl-10"
            type="password"
            placeholder="Min. 8 characters"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
          />
        </div>
      </div>



      <div className="flex gap-3 pt-2">
        <Button type="button" variant="outline" className="flex-1" onClick={onBack}>
          Cancel
        </Button>
        <Button
          type="submit"
          className="flex-1 gradient-primary hover:opacity-95 font-medium"
          disabled={isLoading}
        >
          {isLoading ? (
            <span className="flex items-center gap-2">
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              Creating...
            </span>
          ) : 'Create Account'}
        </Button>
      </div>
    </form>
  );
}

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

      {mode === 'register' ? (
        <CardContent className="pt-6">
          <RegisterForm onBack={() => { setMode('login'); setError(null); }} />
        </CardContent>
      ) : (
        <>
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

              <div className="w-full flex items-center justify-center pt-2 border-t">
                <button
                  type="button"
                  onClick={() => { setMode('register'); setError(null); }}
                  className="text-xs text-muted-foreground hover:text-voxmed-primary hover:underline transition-colors"
                >
                  Register a new Administrator account
                </button>
              </div>
            </CardFooter>
          </form>
        </>
      )}
    </Card>
  );
}
