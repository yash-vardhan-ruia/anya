import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Authentication - CareVoice AI',
  description: 'Access the CareVoice AI Hospital Platform admin portal',
};

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-slate-50 dark:bg-zinc-950 font-sans">
      {/* Left side: Premium branding & decorative waveform */}
      <div className="hidden lg:flex w-1/2 gradient-primary text-white flex-col justify-between p-16 relative overflow-hidden select-none">
        {/* Glow effect overlays */}
        <div className="absolute top-[-20%] left-[-20%] w-[80%] h-[80%] rounded-full bg-voxmed-primary-container blur-[150px] opacity-60"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] rounded-full bg-blue-400/20 blur-[120px] opacity-40"></div>

        {/* Header */}
        <div className="z-10 flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center font-bold text-white text-xl tracking-wider">
            V
          </div>
          <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white to-blue-200 bg-clip-text text-transparent">
            VoxMed CareVoice
          </span>
        </div>

        {/* Content */}
        <div className="z-10 my-auto flex flex-col gap-6 max-w-lg">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md border border-white/10 self-start text-xs font-semibold tracking-wider uppercase text-blue-200">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Version 2.4 Active
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight leading-[1.2]">
            AI-Driven Patient Voice Triage & Scheduling
          </h1>
          <p className="text-lg text-blue-100/90 leading-relaxed font-light">
            Automating patient reception, symptom collection, and clinical appointments with human-grade conversational voice response.
          </p>

          {/* Features checkmark list */}
          <div className="mt-8 flex flex-col gap-4">
            {[
              { title: 'Clinical Intent Extraction', desc: 'Symptom matching with 94.8% AI accuracy' },
              { title: 'Bi-directional EHR Syncing', desc: 'Writes real-time notes directly to clinical systems' },
              { title: 'Automated Billing & Copays', desc: 'Processes claims and schedules payments on-call' },
            ].map((feat, index) => (
              <div key={index} className="flex gap-4 items-start">
                <div className="h-6 w-6 rounded-full bg-white/10 flex items-center justify-center border border-white/20 shrink-0">
                  <span className="material-symbols-outlined text-sm font-bold text-emerald-400">check</span>
                </div>
                <div>
                  <h4 className="font-semibold text-white text-sm">{feat.title}</h4>
                  <p className="text-xs text-blue-200 font-light mt-0.5">{feat.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="z-10 flex justify-between items-center text-xs text-blue-200/60 font-light border-t border-white/10 pt-6">
          <p>© 2026 VoxMed Inc. All rights reserved.</p>
          <div className="flex gap-4">
            <a href="#" className="hover:underline">Privacy Policy</a>
            <span>•</span>
            <a href="#" className="hover:underline">Support Portal</a>
          </div>
        </div>
      </div>

      {/* Right side: Login form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 md:p-16 relative">
        {/* Background micro-aesthetics */}
        <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-voxmed-primary/5 rounded-full blur-[100px] pointer-events-none"></div>
        <div className="absolute bottom-1/4 left-1/4 w-80 h-80 bg-emerald-500/5 rounded-full blur-[80px] pointer-events-none"></div>
        
        <div className="w-full max-w-md z-10">
          {children}
        </div>
      </div>
    </div>
  );
}
