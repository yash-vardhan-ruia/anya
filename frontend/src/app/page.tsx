'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/use-auth-store';

export default function Home() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      router.replace('/overview');
    } else {
      router.replace('/login');
    }
  }, [isAuthenticated, router]);

  // Loading skeleton while redirecting
  return (
    <div className="flex h-screen w-screen items-center justify-center bg-voxmed-surface">
      <div className="flex flex-col items-center gap-4">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-voxmed-primary border-t-transparent"></div>
        <p className="text-sm font-medium text-muted-foreground animate-pulse">
          Connecting to CareVoice AI...
        </p>
      </div>
    </div>
  );
}
