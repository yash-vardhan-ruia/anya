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

export default function LoginPage() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  
  const [email, setEmail] = useState('admin@carevoice.ai');
  const [password, setPassword] = useState('password123');
  const [role, setRole] = useState<'admin' | 'doctor' | 'nurse' | 'receptionist'>('admin');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      // 1. Authenticate with the real FastAPI auth/login endpoint
      const formData = new FormData();
      formData.append('username', email); // FastAPI OAuth2 username field maps to email
      formData.append('password', password);

      const loginRes = await api.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const { access_token } = loginRes.data;

      // 2. Fetch authenticated user profile details from auth/me
      const meRes = await api.get('/auth/me', {
        headers: {
          Authorization: `Bearer ${access_token}`,
        },
      });

      const userData = meRes.data;

      // 3. Map user roles from backend format to frontend UI format
      // backend AdminRole values: SUPER_ADMIN, ADMIN, STAFF, CLINICIAN
      // frontend User role values: 'admin' | 'doctor' | 'nurse' | 'receptionist'
      let mappedRole: 'admin' | 'doctor' | 'nurse' | 'receptionist' = 'admin';
      if (userData.role === 'CLINICIAN') {
        mappedRole = 'doctor';
      } else if (userData.role === 'STAFF') {
        mappedRole = 'receptionist';
      }

      const verifiedUser: User = {
        id: userData.id,
        email: userData.email,
        name: userData.full_name,
        role: mappedRole,
        hospitalId: 'hosp-voxmed-core',
        createdAt: userData.created_at || new Date().toISOString(),
      };

      // 4. Save credentials dynamically to Zustand auth store
      setAuth(verifiedUser, access_token, access_token);

      // 5. Store authentication cookie for SSR route-guard alignment
      document.cookie = `auth-token=${access_token}; path=/; max-age=86400; SameSite=Strict`;

      // 6. Navigate securely to the overview console
      router.push('/overview');
    } catch (err: any) {
      console.error('Handshake verification failed:', err);
      const backendError = err.response?.data?.detail;
      setError(backendError || 'Invalid clinical credentials. Please check secure keys.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="border-border shadow-2xl relative overflow-hidden bg-white/75 dark:bg-zinc-900/75 backdrop-blur-md">
      {/* Top line accent */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-voxmed-primary via-blue-500 to-emerald-500"></div>

      <CardHeader className="space-y-1">
        <div className="flex items-center gap-2 mb-2 lg:hidden">
          <div className="h-7 w-7 rounded-lg bg-voxmed-primary flex items-center justify-center font-bold text-white text-sm">
            V
          </div>
          <span className="text-sm font-bold tracking-tight text-voxmed-primary">
            VoxMed CareVoice
          </span>
        </div>
        <CardTitle className="text-2xl font-bold tracking-tight">Admin Console Access</CardTitle>
        <CardDescription>
          Provide your hospital-issued credentials to unlock clinical dashboards
        </CardDescription>
      </CardHeader>

      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <span className="material-symbols-outlined shrink-0 text-sm">error</span>
              <AlertTitle className="ml-2">Access Denied</AlertTitle>
              <AlertDescription className="ml-2 text-xs font-light">
                {error}
              </AlertDescription>
            </Alert>
          )}

          <div className="space-y-2">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider" htmlFor="email">
              Professional Email
            </label>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-2.5 text-muted-foreground text-lg">
                mail
              </span>
              <Input
                className="pl-10"
                id="email"
                type="email"
                placeholder="doctor@voxmed.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider" htmlFor="password">
              Security Credentials
            </label>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-2.5 text-muted-foreground text-lg">
                lock
              </span>
              <Input
                className="pl-10"
                id="password"
                type="password"
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider" htmlFor="role">
              Department Role
            </label>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-2.5 text-muted-foreground text-lg z-10">
                assignment_ind
              </span>
              <select
                id="role"
                className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 pl-10 appearance-none font-medium focus:ring-voxmed-primary focus:border-voxmed-primary cursor-pointer text-slate-800 dark:text-zinc-200"
                value={role}
                onChange={(e: any) => setRole(e.target.value)}
              >
                <option value="admin">Platform Administrator</option>
              </select>
              <span className="material-symbols-outlined absolute right-3 top-2.5 text-muted-foreground text-lg pointer-events-none">
                arrow_drop_down
              </span>
            </div>
          </div>
        </CardContent>

        <CardFooter className="flex flex-col gap-3">
          <Button
            type="submit"
            className="w-full gradient-primary hover:opacity-95 font-medium transition-all"
            disabled={isLoading}
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
                Authorizing Gateway...
              </span>
            ) : (
              <span className="flex items-center gap-1 justify-center">
                Secure Log In
                <span className="material-symbols-outlined text-sm font-semibold">arrow_right_alt</span>
              </span>
            )}
          </Button>

          <div className="flex w-full items-center justify-between text-xs text-muted-foreground mt-2 border-t pt-4">
            <a href="#" className="hover:text-voxmed-primary hover:underline">Forgot passcode?</a>
            <span className="text-zinc-300 dark:text-zinc-700">|</span>
            <span className="font-light">Demo: admin@carevoice.ai / password123</span>
          </div>
        </CardFooter>
      </form>
    </Card>
  );
}
