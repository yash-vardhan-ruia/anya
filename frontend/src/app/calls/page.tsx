'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { useVoiceSession } from '@/hooks/use-voice-session';

const STATE_ORDER = [
  'greeting',
  'type_check',
  'new_info',
  'returning_lookup',
  'symptoms',
  'dept_routing',
  'doctor_select',
  'slot_select',
  'booking_review',
  'farewell',
  'complete'
];

const STATE_LABELS: Record<string, { title: string; color: string; desc: string; icon: string }> = {
  greeting: { title: 'Welcome', color: 'bg-blue-500/10 text-blue-400 border-blue-500/30', desc: 'Greeting and introducing Anya.', icon: 'waving_hand' },
  type_check: { title: 'New or Returning?', color: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30', desc: 'Determining visit type.', icon: 'people' },
  new_info: { title: 'Patient Details', color: 'bg-violet-500/10 text-violet-400 border-violet-500/30', desc: 'Collecting name, age, gender.', icon: 'person_add' },
  returning_lookup: { title: 'Patient Lookup', color: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30', desc: 'Finding existing patient record.', icon: 'manage_search' },
  symptoms: { title: 'Symptom Triage', color: 'bg-amber-500/10 text-amber-400 border-amber-500/30', desc: 'Recording symptoms and reason for visit.', icon: 'medical_information' },
  dept_routing: { title: 'Department Routing', color: 'bg-teal-500/10 text-teal-400 border-teal-500/30', desc: 'Matching symptoms to clinical specialty.', icon: 'lan' },
  doctor_select: { title: 'Doctor Selection', color: 'bg-purple-500/10 text-purple-400 border-purple-500/30', desc: 'Choosing from available doctors.', icon: 'doctor' },
  slot_select: { title: 'Slot Allocation', color: 'bg-pink-500/10 text-pink-400 border-pink-500/30', desc: 'Picking an appointment timeslot.', icon: 'calendar_month' },
  booking_review: { title: 'Booking Review', color: 'bg-orange-500/10 text-orange-400 border-orange-500/30', desc: 'Reviewing all appointment details.', icon: 'fact_check' },
  farewell: { title: 'Payment & Goodbye', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30', desc: 'Redirecting to payment and ending call.', icon: 'payments' },
  complete: { title: 'Booking Confirmed', color: 'bg-emerald-600 text-white border-transparent', desc: 'Appointment successfully booked!', icon: 'verified' },
};

export default function Home() {
  const [sessionKey, setSessionKey] = useState<string>('');
  const [callDuration, setCallDuration] = useState<number>(0);
  const [isOnHold, setIsOnHold] = useState<boolean>(false);
  const [emailInputValue, setEmailInputValue] = useState('');
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Generate session ID on mount
  useEffect(() => {
    setSessionKey(`web-${Math.random().toString(36).substring(2, 12)}-${Date.now()}`);
  }, []);

  const {
    isConnected,
    status,
    transcripts,
    sessionState,
    error,
    isMuted,
    startSession,
    stopSession,
    toggleMute,
    activeInput,
    doctorOptions,
    doctorDepartment,
    slotOptions,
    slotDoctorName,
    paymentUrl,
    paymentAmount,
    submitInput,
    selectDoctor,
    selectSlot,
  } = useVoiceSession(sessionKey);

  const transcriptsEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll transcripts
  useEffect(() => {
    transcriptsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcripts]);

  // Call duration timer
  useEffect(() => {
    const activeStates = ['connected', 'listening', 'speaking'];
    if (isConnected && activeStates.includes(status) && !isOnHold) {
      timerRef.current = setInterval(() => {
        setCallDuration((prev) => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      if (status === 'idle') {
        setCallDuration(0);
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isConnected, status, isOnHold]);

  const handleReset = () => {
    stopSession();
    setIsOnHold(false);
    setCallDuration(0);
    setEmailInputValue('');
    setSessionKey(`web-${Math.random().toString(36).substring(2, 12)}-${Date.now()}`);
  };

  const handleEndCall = () => {
    stopSession();
    setIsOnHold(false);
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const currentState = sessionState?.current_state || 'greeting';
  const stateInfo = STATE_LABELS[currentState] || { title: currentState, color: 'bg-slate-100 text-slate-700', desc: 'Undergoing triage.', icon: 'question_mark' };
  const currentIndex = STATE_ORDER.indexOf(currentState);

  // Helper to determine status color and text
  const getStatusDisplay = () => {
    if (isOnHold) {
      return { text: 'Call On Hold', badge: 'bg-amber-500/20 text-amber-300 border-amber-500/40' };
    }
    switch (status) {
      case 'idle':
        return { text: 'Ready to Connect', badge: 'bg-slate-500/10 text-slate-400 border-slate-500/20' };
      case 'connecting':
        return { text: 'Connecting to AI...', badge: 'bg-amber-500/20 text-amber-400 border-amber-500/40 animate-pulse' };
      case 'connected':
        return { text: 'Starting Session...', badge: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' };
      case 'listening':
        return { text: isMuted ? 'Muted (Listening)' : 'Listening...', badge: isMuted ? 'bg-amber-500/20 text-amber-400 border-amber-500/40 animate-pulse' : 'bg-blue-500/20 text-blue-400 border-blue-500/30 animate-pulse' };
      case 'speaking':
        return { text: 'Anya Speaking', badge: 'bg-emerald-500 text-white border-transparent' };
      case 'completed':
        return { text: 'Call Finished', badge: 'bg-zinc-600 text-zinc-300 border-zinc-500/30' };
      case 'error':
        return { text: 'Connection Error', badge: 'bg-red-500/20 text-red-400 border-red-500/30' };
      default:
        return { text: status, badge: 'bg-slate-100 text-slate-700' };
    }
  };

  const statusDisplay = getStatusDisplay();
  const showInteractivePanel = !!paymentUrl;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-zinc-950 font-sans flex flex-col">
      <style>{`
        @keyframes dance {
          0%, 100% { height: 8px; }
          50% { height: 42px; }
        }
        @keyframes subtle-dance {
          0%, 100% { height: 6px; }
          50% { height: 18px; }
        }
        @keyframes ring-pulse {
          0% { transform: scale(0.95); opacity: 0.5; }
          50% { transform: scale(1.15); opacity: 0.8; }
          100% { transform: scale(0.95); opacity: 0.5; }
        }
        .visualizer-bar {
          width: 4px;
          border-radius: 9999px;
        }
        .custom-scrollbar::-webkit-scrollbar {
          width: 5px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.02);
          border-radius: 9999px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 9999px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.2);
        }
      `}</style>

      {/* ── Top Brand Header ── */}
      <header className="bg-white dark:bg-zinc-900 border-b border-slate-200 dark:border-zinc-800 h-16 flex items-center justify-between px-6 md:px-12 z-20 shadow-sm shrink-0">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-voxmed-primary flex items-center justify-center font-bold text-white text-base shadow-lg shadow-voxmed-primary/20">
            V
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-bold tracking-tight text-slate-900 dark:text-white leading-none">VoxMed AI</span>
            <span className="text-[10px] text-emerald-500 font-medium tracking-wide mt-1 animate-pulse">
              Anya Assistant Core Active
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

      {/* ── Main Triage Workspace ── */}
      <main className="flex-1 p-6 md:p-12 overflow-y-auto max-w-7xl w-full mx-auto space-y-6">
        {/* Page Hero */}
        <div className="border-b border-slate-200 dark:border-zinc-800 pb-5 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-voxmed-primary to-indigo-500 bg-clip-text text-transparent">
              CareVoice Booking Portal
            </h1>
            <p className="text-sm text-muted-foreground mt-1.5 leading-relaxed max-w-2xl">
              Register and book medical appointments instantly. Speak aloud to Anya, our conversational voice agent, to share symptoms, select matching doctors, and secure scheduling slots.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className={cn("flex items-center gap-2 text-[10px] uppercase font-bold tracking-wider border px-3 py-2 rounded-lg backdrop-blur-md", statusDisplay.badge)}>
              <span className={cn("h-2 w-2 rounded-full", 
                status === 'listening' && !isMuted ? 'bg-blue-500 animate-ping' : 
                status === 'speaking' ? 'bg-emerald-500 animate-bounce' : 
                isMuted || isOnHold ? 'bg-amber-500' : 'bg-slate-400'
              )} />
              {statusDisplay.text}
            </div>
            {isConnected && (
              <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg text-white font-mono font-bold text-xs shadow-inner">
                <span className="material-symbols-outlined text-[14px] text-red-500 animate-pulse">timer</span>
                {formatDuration(callDuration)}
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: State Machine & Variables */}
          <div className="space-y-6 lg:col-span-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-1 gap-6 md:gap-6 lg:gap-0">
            {/* Active Triage State Card */}
            <Card className="border border-slate-200 dark:border-zinc-800 shadow-sm overflow-hidden bg-white dark:bg-zinc-900/50 backdrop-blur-md">
              <div className="h-1.5 bg-gradient-to-r from-voxmed-primary via-indigo-500 to-teal-500 w-full" />
              <CardHeader className="pb-3">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                  <span className="material-symbols-outlined text-[16px] text-voxmed-primary">route</span>
                  Active Triage Path
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className={cn("px-4 py-2.5 rounded-xl border text-xs font-bold flex items-center gap-2.5 shadow-sm", stateInfo.color)}>
                  <span className="material-symbols-outlined text-[16px]">{stateInfo.icon}</span>
                  {stateInfo.title}
                </div>
                
                {/* Triage Progress Tracker List */}
                <div className="space-y-2.5 pl-1.5 border-l border-slate-100 dark:border-zinc-800 relative">
                  {STATE_ORDER.map((state, index) => {
                    const label = STATE_LABELS[state]?.title || state;
                    const isCompleted = index < currentIndex;
                    const isActive = index === currentIndex;
                    
                    return (
                      <div key={state} className="flex items-center gap-3 relative group">
                        {/* Timeline dot */}
                        <div className={cn(
                          "h-2.5 w-2.5 rounded-full border-2 absolute -left-[11.5px] transition-all duration-300",
                          isCompleted ? "bg-emerald-500 border-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]" :
                          isActive ? "bg-indigo-500 border-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.5)] scale-110" :
                          "bg-white dark:bg-zinc-950 border-slate-300 dark:border-zinc-800"
                        )} />
                        <span className={cn(
                          "text-[10px] font-semibold transition-colors duration-200 pl-4",
                          isCompleted ? "text-emerald-500" :
                          isActive ? "text-indigo-500 dark:text-indigo-400 font-extrabold" :
                          "text-slate-400 dark:text-zinc-500"
                        )}>
                          {label}
                        </span>
                        {isCompleted && (
                          <span className="material-symbols-outlined text-[11px] text-emerald-500">check_circle</span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Session Variables Inspector */}
            <Card className="border border-slate-200 dark:border-zinc-800 shadow-sm bg-white dark:bg-zinc-900/50 backdrop-blur-md">
              <CardHeader className="pb-3">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                  <span className="material-symbols-outlined text-[16px] text-voxmed-primary">clinical_notes</span>
                  EHR Variables
                </CardTitle>
                <CardDescription className="text-[10px] leading-relaxed">
                  Extracted clinical and booking parameters synced from the live session.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y divide-slate-100 dark:divide-zinc-800 text-[10px]">
                  {/* Name */}
                  <div className={cn(
                    "flex justify-between items-center px-4 py-3 border-l-4 transition-all duration-300",
                    sessionState?.patient_name 
                      ? "border-emerald-500 bg-emerald-500/5 dark:bg-emerald-500/10" 
                      : "border-slate-200 dark:border-zinc-800"
                  )}>
                    <span className="text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[14px]">person</span>
                      Patient Name
                    </span>
                    <span className={cn(
                      "font-bold text-xs transition-colors",
                      sessionState?.patient_name ? "text-emerald-600 dark:text-emerald-400" : "text-slate-400"
                    )}>
                      {sessionState?.patient_name || 'Pending...'}
                    </span>
                  </div>

                  {/* Age */}
                  <div className={cn(
                    "flex justify-between items-center px-4 py-3 border-l-4 transition-all duration-300",
                    sessionState?.age 
                      ? "border-emerald-500 bg-emerald-500/5 dark:bg-emerald-500/10" 
                      : "border-slate-200 dark:border-zinc-800"
                  )}>
                    <span className="text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[14px]">cake</span>
                      Age
                    </span>
                    <span className={cn(
                      "font-bold text-xs transition-colors",
                      sessionState?.age ? "text-emerald-600 dark:text-emerald-400" : "text-slate-400"
                    )}>
                      {sessionState?.age || 'Pending...'}
                    </span>
                  </div>

                  {/* Gender */}
                  <div className={cn(
                    "flex justify-between items-center px-4 py-3 border-l-4 transition-all duration-300",
                    sessionState?.gender 
                      ? "border-emerald-500 bg-emerald-500/5 dark:bg-emerald-500/10" 
                      : "border-slate-200 dark:border-zinc-800"
                  )}>
                    <span className="text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[14px]">transgender</span>
                      Gender
                    </span>
                    <span className={cn(
                      "font-bold text-xs transition-colors",
                      sessionState?.gender ? "text-emerald-600 dark:text-emerald-400" : "text-slate-400"
                    )}>
                      {sessionState?.gender || 'Pending...'}
                    </span>
                  </div>

                  {/* Email */}
                  <div className={cn(
                    "flex justify-between items-center px-4 py-3 border-l-4 transition-all duration-300",
                    sessionState?.email 
                      ? "border-emerald-500 bg-emerald-500/5 dark:bg-emerald-500/10" 
                      : "border-slate-200 dark:border-zinc-800"
                  )}>
                    <span className="text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[14px]">mail</span>
                      Patient Email
                    </span>
                    <span className={cn(
                      "font-bold text-xs select-all transition-colors",
                      sessionState?.email ? "text-emerald-600 dark:text-emerald-400" : "text-slate-400"
                    )}>
                      {sessionState?.email || 'Pending...'}
                    </span>
                  </div>

                  {/* Visit Type */}
                  <div className={cn(
                    "flex justify-between items-center px-4 py-3 border-l-4 transition-all duration-300",
                    sessionState?.visit_type 
                      ? "border-emerald-500 bg-emerald-500/5 dark:bg-emerald-500/10" 
                      : "border-slate-200 dark:border-zinc-800"
                  )}>
                    <span className="text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[14px]">groups</span>
                      Visit Type
                    </span>
                    <span className={cn(
                      "font-bold text-xs transition-colors",
                      sessionState?.visit_type ? "text-emerald-600 dark:text-emerald-400" : "text-slate-400"
                    )}>
                      {sessionState?.visit_type || 'Pending...'}
                    </span>
                  </div>

                  {/* Department */}
                  <div className={cn(
                    "flex justify-between items-center px-4 py-3 border-l-4 transition-all duration-300",
                    sessionState?.department_name 
                      ? "border-emerald-500 bg-emerald-500/5 dark:bg-emerald-500/10" 
                      : "border-slate-200 dark:border-zinc-800"
                  )}>
                    <span className="text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[14px]">local_hospital</span>
                      Department
                    </span>
                    <span className={cn(
                      "font-bold text-xs transition-colors",
                      sessionState?.department_name ? "text-emerald-600 dark:text-emerald-400" : "text-slate-400"
                    )}>
                      {sessionState?.department_name || 'Pending...'}
                    </span>
                  </div>

                  {/* Doctor */}
                  <div className={cn(
                    "flex justify-between items-center px-4 py-3 border-l-4 transition-all duration-300",
                    sessionState?.doctor_name 
                      ? "border-emerald-500 bg-emerald-500/5 dark:bg-emerald-500/10" 
                      : "border-slate-200 dark:border-zinc-800"
                  )}>
                    <span className="text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[14px]">medical_services</span>
                      Doctor Selection
                    </span>
                    <span className={cn(
                      "font-bold text-xs transition-colors truncate max-w-[130px]",
                      sessionState?.doctor_name ? "text-emerald-600 dark:text-emerald-400" : "text-slate-400"
                    )}>
                      {sessionState?.doctor_name || 'Pending...'}
                    </span>
                  </div>

                  {/* Slot */}
                  <div className={cn(
                    "flex justify-between items-center px-4 py-3 border-l-4 transition-all duration-300",
                    sessionState?.slot_time_str 
                      ? "border-emerald-500 bg-emerald-500/5 dark:bg-emerald-500/10" 
                      : "border-slate-200 dark:border-zinc-800"
                  )}>
                    <span className="text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[14px]">schedule</span>
                      Selected Slot
                    </span>
                    <span className={cn(
                      "font-bold text-xs transition-colors",
                      sessionState?.slot_time_str ? "text-emerald-600 dark:text-emerald-400" : "text-slate-400"
                    )}>
                      {sessionState?.slot_time_str ? `${sessionState.slot_date_str} @ ${sessionState.slot_time_str}` : 'Pending...'}
                    </span>
                  </div>

                  {/* Amount */}
                  {sessionState?.amount_inr && (
                    <div className="flex justify-between items-center px-4 py-3 border-l-4 border-emerald-500 bg-emerald-500/5 dark:bg-emerald-500/10 transition-all">
                      <span className="text-muted-foreground uppercase tracking-wider flex items-center gap-1.5 text-[10px]">
                        <span className="material-symbols-outlined text-[14px]">receipt</span>
                        Consult Fee
                      </span>
                      <span className="font-bold text-xs text-emerald-600 dark:text-emerald-400">
                        ₹{Number(sessionState.amount_inr).toFixed(2)}
                      </span>
                    </div>
                  )}

                  {sessionState?.is_emergency && (
                    <div className="px-4 py-3 bg-red-500/10 text-red-500 font-bold text-center border-t border-red-500/20 flex items-center justify-center gap-1.5">
                      <span className="material-symbols-outlined text-[14px] animate-ping">warning</span>
                      Emergency Detected!
                    </div>
                  )}
                  {sessionState?.payment_link_url && (
                    <div className="px-4 py-4 bg-emerald-500/5 text-emerald-400 font-semibold border-t border-emerald-500/20 flex flex-col items-center gap-2">
                      <span className="text-[9px] uppercase font-bold text-center tracking-wider text-muted-foreground flex items-center gap-1">
                        <span className="material-symbols-outlined text-[11px] text-emerald-500">payments</span>
                        Razorpay Checkout Invoice
                      </span>
                      <a 
                        href={sessionState.payment_link_url} 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        className="text-xs text-indigo-400 hover:text-indigo-300 underline font-mono break-all text-center transition-colors py-1 px-3 bg-slate-900 border border-slate-800 rounded-lg hover:border-slate-700 w-full"
                      >
                        Click to Pay Test Fee
                      </a>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column: Animated Voice Panel & Real-time Transcript */}
          <div className="lg:col-span-8 space-y-6">
            <Card className="border border-slate-800 shadow-xl flex flex-col h-[580px] bg-slate-955/95 overflow-hidden text-white relative">
              {/* Radial gradient background */}
              <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-indigo-900/10 via-slate-950 to-slate-955 pointer-events-none" />

              <CardHeader className="border-b border-slate-900 py-3.5 px-5 flex flex-row items-center justify-between bg-slate-950/70 backdrop-blur-md z-10">
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-full bg-voxmed-primary flex items-center justify-center text-white text-xs font-black shadow-[0_0_12px_rgba(99,102,241,0.4)] shrink-0">
                    A
                  </div>
                  <div>
                    <CardTitle className="text-xs font-bold text-white leading-tight">
                      Clinical Voice Assistant
                    </CardTitle>
                    <CardDescription className="text-[10px] text-slate-400">
                      Anya Reception Agent (Gemini Multimodal Live API)
                    </CardDescription>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleReset}
                  className="h-8 text-[10px] font-bold text-slate-300 hover:text-red-400 border-slate-800 hover:bg-slate-900 hover:border-red-950/30"
                >
                  <span className="material-symbols-outlined text-xs mr-1">refresh</span>
                  Reset Call
                </Button>
              </CardHeader>

              {/* Interactive Panel (Payment Redirect Card only) */}
              {showInteractivePanel && paymentUrl && (
                <div className="border-b border-slate-900 bg-slate-950/80 p-4 z-10 max-h-[250px] overflow-y-auto custom-scrollbar">
                  <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="material-symbols-outlined text-emerald-400 text-[18px]">payments</span>
                      <span className="text-xs font-bold text-emerald-300">Payment Portal Ready</span>
                    </div>
                    <p className="text-[10px] text-slate-300">Your appointment is booked! Complete payment to confirm.</p>
                    {paymentAmount && (
                      <p className="text-xs text-white font-semibold">Amount due: <span className="text-emerald-400">₹{paymentAmount.toFixed(2)}</span></p>
                    )}
                    <a
                      href={paymentUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-lg transition-colors"
                    >
                      <span className="material-symbols-outlined text-[14px]">open_in_new</span>
                      Pay Now
                    </a>
                  </div>
                </div>
              )}

              <CardContent className={cn(
                "flex-1 flex overflow-hidden p-0 z-10",
                showInteractivePanel ? "flex-row divide-x divide-slate-900" : "flex-col md:flex-row md:divide-x divide-y md:divide-y-0 divide-slate-900"
              )}>
                {/* Voice Status & Mic button (Left) */}
                <div className={cn(
                  "flex flex-col items-center justify-center p-6 space-y-8 bg-slate-955/30 relative",
                  showInteractivePanel ? "w-[35%]" : "flex-[4]"
                )}>
                  {/* Visualizer audio equalizer wave */}
                  <div className="w-full">
                    <div className="flex items-end gap-1 h-12 justify-center">
                      {Array.from({ length: showInteractivePanel ? 10 : 16 }).map((_, i) => {
                        const isSpeaking = status === 'speaking' && !isOnHold;
                        const isListening = status === 'listening' && !isOnHold;
                        const delay = `${(i * 0.085).toFixed(2)}s`;
                        
                        return (
                          <div
                            key={i}
                            className={cn(
                              "visualizer-bar transition-colors duration-300",
                              isSpeaking ? "bg-emerald-500 animate-[dance_1.1s_ease-in-out_infinite]" : "",
                              isListening ? (isMuted ? "bg-amber-500/50 animate-[subtle-dance_2s_ease-in-out_infinite]" : "bg-blue-500/80 animate-[dance_1.8s_ease-in-out_infinite]") : "bg-slate-800"
                            )}
                            style={{
                              animationDelay: isSpeaking || isListening ? delay : undefined,
                              height: isSpeaking || isListening ? '8px' : '6px',
                              width: '4px',
                              borderRadius: '2px'
                            }}
                          />
                        );
                      })}
                    </div>
                  </div>

                  {/* Glowing microphone central button */}
                  <div className="relative flex items-center justify-center">
                    {status === 'listening' && !isMuted && !isOnHold && (
                      <>
                        <span className={cn("absolute rounded-full border border-blue-500/20 animate-ping pointer-events-none", showInteractivePanel ? "h-24 w-24" : "h-36 w-36")} />
                        <span className={cn("absolute rounded-full border border-blue-500/10 animate-[ring-pulse_2.5s_ease-in-out_infinite] pointer-events-none", showInteractivePanel ? "h-28 w-28" : "h-40 w-40")} style={{ animationDelay: '0.5s' }} />
                      </>
                    )}
                    {status === 'speaking' && !isOnHold && (
                      <>
                        <span className={cn("absolute rounded-full border border-emerald-500/20 animate-ping pointer-events-none", showInteractivePanel ? "h-24 w-24" : "h-36 w-36")} />
                        <span className={cn("absolute rounded-full border border-emerald-500/10 animate-[ring-pulse_2.5s_ease-in-out_infinite] pointer-events-none", showInteractivePanel ? "h-28 w-28" : "h-40 w-40")} style={{ animationDelay: '0.5s' }} />
                      </>
                    )}

                    {status === 'idle' ? (
                      <button
                        onClick={startSession}
                        className={cn("relative flex items-center justify-center rounded-full bg-gradient-to-r from-voxmed-primary to-indigo-600 hover:scale-105 transition-all shadow-[0_0_20px_rgba(99,102,241,0.3)] hover:shadow-indigo-500/40 group active:scale-95", showInteractivePanel ? "h-16 w-16" : "h-28 w-28")}
                      >
                        <span className={cn("material-symbols-outlined text-white group-hover:scale-110 transition-transform", showInteractivePanel ? "text-2xl" : "text-4xl")}>call</span>
                        {!showInteractivePanel && <span className="absolute -bottom-8 text-[9px] text-slate-400 font-bold uppercase tracking-wider">Start Call</span>}
                      </button>
                    ) : status === 'connecting' ? (
                      <div className={cn("relative flex items-center justify-center rounded-full bg-slate-900 border border-slate-800", showInteractivePanel ? "h-16 w-16" : "h-28 w-28")}>
                        <span className="absolute inset-0 rounded-full border-2 border-dashed border-amber-500 animate-[spin_3s_linear_infinite]" />
                        <span className={cn("material-symbols-outlined text-amber-500 animate-pulse", showInteractivePanel ? "text-2xl" : "text-3xl")}>hourglass_empty</span>
                        {!showInteractivePanel && <span className="absolute -bottom-8 text-[9px] text-slate-400 font-bold uppercase tracking-wider">Connecting</span>}
                      </div>
                    ) : status === 'connected' ? (
                      <div className={cn("relative flex items-center justify-center rounded-full bg-slate-900 border-2 border-dashed border-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.2)]", showInteractivePanel ? "h-16 w-16" : "h-28 w-28")}>
                        <span className={cn("material-symbols-outlined text-emerald-400", showInteractivePanel ? "text-2xl" : "text-3xl")}>check_circle</span>
                        {!showInteractivePanel && <span className="absolute -bottom-8 text-[9px] text-slate-400 font-bold uppercase tracking-wider">Connected</span>}
                      </div>
                    ) : (
                      <div className={cn("relative flex items-center justify-center rounded-full bg-slate-950 border border-slate-800 shadow-inner", showInteractivePanel ? "h-16 w-16" : "h-28 w-28")}>
                        <div className={cn(
                          "rounded-full flex items-center justify-center transition-all duration-300",
                          showInteractivePanel ? "h-14 w-14" : "h-24 w-24",
                          isOnHold ? "bg-amber-500/10 text-amber-400 border border-amber-500/30" :
                          status === 'listening' ? (isMuted ? "bg-amber-500/10 text-amber-400 border border-amber-500/30" : "bg-blue-500/10 text-blue-400 border border-blue-500/30") :
                          status === 'speaking' ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30" :
                          "bg-red-500/10 text-red-500 border border-red-500/30"
                        )}>
                          <span className={cn("material-symbols-outlined", showInteractivePanel ? "text-2xl" : "text-4xl")}>
                            {isOnHold ? 'pause' : (status === 'listening' ? (isMuted ? 'mic_off' : 'mic') : (status === 'speaking' ? 'volume_up' : 'error'))}
                          </span>
                        </div>
                        {!showInteractivePanel && <span className="absolute -bottom-8 text-[9px] text-slate-400 font-bold uppercase tracking-wider">
                          {isOnHold ? 'On Hold' : (status === 'listening' ? (isMuted ? 'Muted' : 'Listening') : (status === 'speaking' ? 'Speaking' : 'Error'))}
                        </span>}
                      </div>
                    )}
                  </div>

                  {/* Control Action Buttons (Mute, Hold, End Call) */}
                  {status !== 'idle' && status !== 'connecting' && status !== 'connected' && (
                    <div className={cn("flex items-center pt-2", showInteractivePanel ? "gap-2" : "gap-4 pt-6")}>
                      <button
                        onClick={toggleMute}
                        disabled={isOnHold}
                        className={cn(
                          "rounded-full flex items-center justify-center border transition-all duration-200 active:scale-90",
                          showInteractivePanel ? "h-8 w-8" : "h-10 w-10",
                          isMuted 
                            ? "bg-amber-500/20 border-amber-500 text-amber-400 shadow-[0_0_10px_rgba(245,158,11,0.2)]" 
                            : "bg-slate-900 border-slate-800 text-slate-400 hover:text-white hover:border-slate-700"
                        )}
                        title={isMuted ? "Unmute Mic" : "Mute Mic"}
                      >
                        <span className={cn("material-symbols-outlined", showInteractivePanel ? "text-xs" : "text-sm")}>{isMuted ? 'mic_off' : 'mic'}</span>
                      </button>

                      <button
                        onClick={handleEndCall}
                        className={cn(
                          "rounded-full flex items-center justify-center bg-red-600 hover:bg-red-500 text-white shadow-[0_0_15px_rgba(239,68,68,0.3)] hover:scale-105 active:scale-90 transition-all",
                          showInteractivePanel ? "h-10 w-10" : "h-12 w-12"
                        )}
                        title="End Call"
                      >
                        <span className={cn("material-symbols-outlined", showInteractivePanel ? "text-sm" : "text-base")}>call_end</span>
                      </button>

                      <button
                        onClick={() => setIsOnHold(!isOnHold)}
                        className={cn(
                          "rounded-full flex items-center justify-center border transition-all duration-200 active:scale-90",
                          showInteractivePanel ? "h-8 w-8" : "h-10 w-10",
                          isOnHold 
                            ? "bg-amber-500/20 border-amber-500 text-amber-400 shadow-[0_0_10px_rgba(245,158,11,0.2)]" 
                            : "bg-slate-900 border-slate-800 text-slate-400 hover:text-white hover:border-slate-700"
                        )}
                        title={isOnHold ? "Resume Call" : "Put on Hold"}
                      >
                        <span className={cn("material-symbols-outlined", showInteractivePanel ? "text-xs" : "text-sm")}>{isOnHold ? 'play_arrow' : 'pause'}</span>
                      </button>
                    </div>
                  )}
                </div>

                {/* Scrollable Transcript List (Right) */}
                <div className={cn(
                  "flex flex-col h-full bg-slate-950/50 overflow-hidden",
                  showInteractivePanel ? "w-[65%]" : "flex-[6]"
                )}>
                  <div className="px-5 py-3 border-b border-slate-900 bg-slate-955/60 flex justify-between items-center backdrop-blur-md">
                    <span className="text-[9px] font-bold uppercase text-slate-400 tracking-wider flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[13px] text-voxmed-primary">forum</span>
                      Live Transcript
                    </span>
                    {isConnected && !isOnHold && (
                      <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping" />
                    )}
                  </div>
                  <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar text-xs">
                    {transcripts.length === 0 ? (
                      <div className="h-full flex flex-col items-center justify-center text-center p-4 text-slate-650">
                        <span className="material-symbols-outlined text-3xl mb-1.5 text-slate-700 animate-pulse">mic_none</span>
                        <p className="text-[10px] max-w-[200px] leading-relaxed">Your real-time speech-to-text transcript and Anya's responses will stream here.</p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {transcripts.map((msg, index) => {
                          const isUser = msg.role === 'user';
                          return (
                            <div
                              key={index}
                              className={cn(
                                'flex flex-col max-w-[85%] p-3 rounded-2xl border transition-all duration-300',
                                isUser 
                                  ? 'ml-auto bg-slate-900 border-slate-800 text-white rounded-tr-none shadow-sm' 
                                  : 'mr-auto bg-slate-950/80 border-slate-900 text-slate-200 rounded-tl-none shadow-inner'
                              )}
                            >
                              <span className={cn(
                                "text-[8px] font-bold uppercase tracking-wider mb-1",
                                isUser ? "text-indigo-400" : "text-emerald-400"
                              )}>
                                {isUser ? 'Patient' : 'Anya'}
                              </span>
                              <p className="leading-relaxed text-[11px] whitespace-pre-wrap">{msg.text}</p>
                            </div>
                          );
                        })}
                        <div ref={transcriptsEndRef} />
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Guidelines info */}
            <div className="p-4 border border-slate-200 dark:border-zinc-800 rounded-xl bg-white dark:bg-zinc-900/40 text-[10px] text-muted-foreground flex gap-3 items-start leading-normal shadow-sm">
              <span className="material-symbols-outlined text-voxmed-primary text-base shrink-0 mt-0.5">info</span>
              <div>
                <strong className="text-slate-800 dark:text-zinc-300">Speech Guidelines</strong>: Act as a patient booking a hospital appointment. Follow Anya's instructions. Speak all your responses (name, age, gender, email, preferred doctor, and slot time) aloud. Anya will confirm each detail verbally and update the EHR panel in real time before redirecting you to payment.
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
