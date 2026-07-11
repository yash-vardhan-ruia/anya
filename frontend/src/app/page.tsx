'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-zinc-950 font-sans flex flex-col overflow-x-hidden">
      {/* Glow aesthetic backgrounds */}
      <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-voxmed-primary/5 rounded-full blur-[120px] pointer-events-none z-0"></div>
      <div className="absolute bottom-10 right-1/4 w-[400px] h-[400px] bg-indigo-500/5 rounded-full blur-[100px] pointer-events-none z-0"></div>

      {/* ── Header Navbar ── */}
      <header className="bg-white/70 dark:bg-zinc-900/70 border-b border-slate-200 dark:border-zinc-800 h-16 flex items-center justify-between px-6 md:px-12 backdrop-blur-md sticky top-0 z-30 shadow-sm shrink-0">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-voxmed-primary flex items-center justify-center font-bold text-white text-base shadow-lg shadow-voxmed-primary/20">
            V
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-bold tracking-tight text-slate-900 dark:text-white leading-none">VoxMed AI</span>
            <span className="text-[10px] text-emerald-500 font-medium tracking-wide mt-1 animate-pulse">
              Anya Core Operational
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <Link href="/login">
            <Button variant="outline" size="sm" className="h-9 text-xs font-semibold px-4 border-slate-200 hover:bg-slate-50 dark:border-zinc-800 dark:hover:bg-zinc-800">
              <span className="material-symbols-outlined text-[16px] mr-1.5">admin_panel_settings</span>
              Staff Portal
            </Button>
          </Link>
        </div>
      </header>

      {/* ── Hero Section ── */}
      <section className="relative flex-1 flex flex-col justify-center items-center text-center px-6 py-16 md:py-24 max-w-5xl mx-auto z-10 space-y-8">
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-voxmed-primary/10 border border-voxmed-primary/20 text-xs font-semibold tracking-wider uppercase text-voxmed-primary">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
          Clinical Voice Reception Active
        </div>

        <div className="space-y-4">
          <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight leading-[1.15] text-slate-900 dark:text-white">
            Meet Anya, Your Automated{' '}
            <span className="bg-gradient-to-r from-voxmed-primary via-indigo-500 to-teal-500 bg-clip-text text-transparent">
              Clinical Voice Assistant
            </span>
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground leading-relaxed max-w-3xl mx-auto font-light">
            Streamline patient registration, symptom intake, doctor matches, and booking checkout instantly with human-grade conversational voice response.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center w-full max-w-md pt-4">
          <Link href="/calls" className="w-full sm:w-auto">
            <Button size="lg" className="w-full bg-gradient-to-r from-voxmed-primary to-indigo-600 hover:from-voxmed-primary hover:to-indigo-500 text-white font-bold tracking-wide shadow-lg shadow-voxmed-primary/20 hover:shadow-indigo-500/30 py-6 px-8 rounded-xl transition-all">
              <span className="material-symbols-outlined text-[20px] mr-2">call</span>
              Start Voice Booking
            </Button>
          </Link>
          <Link href="/login" className="w-full sm:w-auto">
            <Button size="lg" variant="outline" className="w-full hover:bg-slate-100 dark:hover:bg-zinc-800 py-6 px-8 rounded-xl border-slate-200 dark:border-zinc-800 font-semibold">
              <span className="material-symbols-outlined text-[20px] mr-2">dashboard</span>
              Clinical Dashboard
            </Button>
          </Link>
        </div>

        {/* Dynamic Voice Indicator Element */}
        <div className="flex justify-center items-center gap-1.5 pt-8 h-10">
          {Array.from({ length: 9 }).map((_, i) => (
            <div
              key={i}
              className="w-1 rounded-full bg-voxmed-primary animate-pulse"
              style={{
                height: `${[12, 24, 36, 20, 42, 16, 30, 24, 12][i]}px`,
                animationDelay: `${i * 0.1}s`,
                animationDuration: '1.2s',
              }}
            />
          ))}
        </div>
      </section>

      {/* ── Key Capabilities Section ── */}
      <section className="bg-white dark:bg-zinc-900 border-t border-slate-200 dark:border-zinc-800 py-16 px-6 md:px-12 z-10 shrink-0">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white uppercase text-xs text-voxmed-primary">
              System Capabilities
            </h2>
            <p className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              EHR Integrated voice workflow
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Triage */}
            <Card className="border border-slate-200 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-950/40 p-5 rounded-xl hover:border-slate-300 dark:hover:border-zinc-700 transition-colors shadow-sm">
              <CardContent className="p-0 space-y-4">
                <div className="h-10 w-10 bg-voxmed-primary/10 text-voxmed-primary rounded-xl flex items-center justify-center">
                  <span className="material-symbols-outlined text-lg">forum</span>
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 dark:text-white text-sm">Clinical Intent Extraction</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed mt-1.5">
                    Anya identifies symptoms, assesses urgency levels, and maps them to clinical departments in real-time.
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Doctors */}
            <Card className="border border-slate-200 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-950/40 p-5 rounded-xl hover:border-slate-300 dark:hover:border-zinc-700 transition-colors shadow-sm">
              <CardContent className="p-0 space-y-4">
                <div className="h-10 w-10 bg-indigo-500/10 text-indigo-500 rounded-xl flex items-center justify-center">
                  <span className="material-symbols-outlined text-lg">stethoscope</span>
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 dark:text-white text-sm">Specialty Routing</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed mt-1.5">
                    Match with 28+ leading specialists across 14 operational hospital departments based on triage assessment.
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Slots */}
            <Card className="border border-slate-200 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-950/40 p-5 rounded-xl hover:border-slate-300 dark:hover:border-zinc-700 transition-colors shadow-sm">
              <CardContent className="p-0 space-y-4">
                <div className="h-10 w-10 bg-teal-500/10 text-teal-500 rounded-xl flex items-center justify-center">
                  <span className="material-symbols-outlined text-lg">calendar_month</span>
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 dark:text-white text-sm">Instant Slot Reservation</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed mt-1.5">
                    Dynamically queries doctor calendars, locks availability slots, and creates clinical EHR appointments.
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Billing */}
            <Card className="border border-slate-200 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-950/40 p-5 rounded-xl hover:border-slate-300 dark:hover:border-zinc-700 transition-colors shadow-sm">
              <CardContent className="p-0 space-y-4">
                <div className="h-10 w-10 bg-emerald-500/10 text-emerald-500 rounded-xl flex items-center justify-center">
                  <span className="material-symbols-outlined text-lg">payments</span>
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 dark:text-white text-sm">Digital Bill Checkout</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed mt-1.5">
                    Generates secure digital payment links dynamically at checkout, integrating instant Razorpay processing.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-slate-200 dark:border-zinc-800 py-6 px-6 md:px-12 text-center text-xs text-muted-foreground bg-slate-50 dark:bg-zinc-950 shrink-0">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">
          <p>© 2026 VoxMed CareVoice AI Hospital Platform. All rights reserved.</p>
          <div className="flex gap-4">
            <Link href="/login" className="hover:underline">Staff Login</Link>
            <span>•</span>
            <Link href="/calls" className="hover:underline">Start Voice Session</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
