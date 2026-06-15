'use client';

import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

type Message = {
  role: 'user' | 'assistant';
  text: string;
};

const STATE_LABELS: Record<string, { title: string; color: string; desc: string }> = {
  greeting: { title: 'Welcome Greeting', color: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/20 dark:text-blue-400 dark:border-blue-900', desc: 'Greeting the patient and collecting name.' },
  identity: { title: 'Patient Profile', color: 'bg-indigo-50 text-indigo-700 border-indigo-200 dark:bg-indigo-950/20 dark:text-indigo-400 dark:border-indigo-900', desc: 'Retrieving patient contact and age details.' },
  symptoms: { title: 'Symptom Triage', color: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/20 dark:text-amber-400 dark:border-amber-900', desc: 'Analyzing symptoms and urgency.' },
  dept: { title: 'Department Match', color: 'bg-teal-50 text-teal-700 border-teal-200 dark:bg-teal-950/20 dark:text-teal-400 dark:border-teal-900', desc: 'Routing patient to the correct clinical specialty.' },
  doctor: { title: 'Doctor Selection', color: 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/20 dark:text-purple-400 dark:border-purple-900', desc: 'Selecting a doctor from on-duty staff.' },
  slot: { title: 'Slot Allocation', color: 'bg-pink-50 text-pink-700 border-pink-200 dark:bg-pink-950/20 dark:text-pink-400 dark:border-pink-900', desc: 'Locking an available appointment timeslot.' },
  review: { title: 'Details Verification', color: 'bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-950/20 dark:text-orange-400 dark:border-orange-900', desc: 'Reviewing slot and patient details.' },
  payment: { title: 'Payment Processing', color: 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/20 dark:text-emerald-400 dark:border-emerald-900', desc: 'Generating payment link and verifying invoice.' },
  confirm: { title: 'Confirming Booking', color: 'bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-900/30 dark:text-emerald-350 dark:border-emerald-800', desc: 'Confirming appointment status.' },
  complete: { title: 'Booking Confirmed', color: 'bg-emerald-600 text-white border-transparent', desc: 'Appointment successfully created in EHR!' },
};

const SUGGESTIONS = [
  { text: 'I want to book a doctor appointment', label: 'Book Consult' },
  { text: 'I am suffering from severe chest pain and sweat', label: 'Heart Emergency' },
  { text: 'I have a high fever, cough and joint pain', label: 'Fever Consult' },
  { text: 'Need a pediatrician appointment for my baby', label: 'Pediatrics' },
];

export default function VoiceAgentPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionData, setSessionData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [input, setInput] = useState('');
  
  const chatEndRef = useRef<HTMLDivElement>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchSessionData = async (sid: string) => {
    try {
      const res = await fetch(`${API_URL}/voice-chat/session/${sid}`);
      if (res.ok) {
        const data = await res.json();
        setSessionData(data);
      }
    } catch (err) {
      console.error('Error fetching session data:', err);
    }
  };

  const sendMessage = async (messageText: string) => {
    if (!messageText.trim()) return;

    try {
      setIsLoading(true);
      setMessages((prev) => [...prev, { role: 'user', text: messageText }]);
      setInput('');

      const response = await fetch(`${API_URL}/voice-chat/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: messageText,
        }),
      });

      if (!response.ok) {
        throw new Error('API Error');
      }

      const data = await response.json();
      setSessionId(data.session_id);
      
      setMessages((prev) => [...prev, { role: 'assistant', text: data.reply }]);
      
      // Fetch state machine variables from Redis
      await fetchSessionData(data.session_id);
    } catch (error) {
      console.error(error);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: 'Sorry, I could not connect to the clinical voice orchestrator.' },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setMessages([]);
    setSessionId(null);
    setSessionData(null);
    setInput('');
  };

  const currentState = sessionData?.current_state || 'greeting';
  const stateInfo = STATE_LABELS[currentState] || { title: currentState, color: 'bg-slate-100 text-slate-700', desc: 'Undergoing triage.' };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* ── Page Header ── */}
      <div className="border-b pb-4 flex flex-col md:flex-row md:items-center md:justify-between gap-2">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight">Conversational Sandbox</h1>
          <p className="text-xs text-muted-foreground mt-1">
            Interact with Anya, our AI clinical receptionist, to test real-time EHR integration, triage states, and slot-booking.
          </p>
        </div>
        <div className="flex items-center gap-2 text-[10px] uppercase font-bold tracking-wider text-muted-foreground bg-slate-50 dark:bg-zinc-900 border px-3 py-1.5 rounded-lg w-fit">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
          NLP Core active
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
        {/* ── Left Sidebar: State Machine Inspector ── */}
        <div className="space-y-6 lg:col-span-1">
          {/* Active Triage State Card */}
          <Card className="border shadow-sm overflow-hidden bg-white dark:bg-zinc-900">
            <div className="h-1.5 bg-gradient-to-r from-voxmed-primary to-indigo-600 w-full" />
            <CardHeader className="pb-3">
              <CardTitle className="text-xs font-black uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                <span className="material-symbols-outlined text-sm text-voxmed-primary">route</span>
                Triage State
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className={cn("px-3 py-2 rounded-lg border text-xs font-bold text-center", stateInfo.color)}>
                {stateInfo.title}
              </div>
              <p className="text-[10px] text-muted-foreground leading-relaxed">
                {stateInfo.desc}
              </p>
            </CardContent>
          </Card>

          {/* Session Variables Inspector */}
          <Card className="border shadow-sm bg-white dark:bg-zinc-900">
            <CardHeader className="pb-3">
              <CardTitle className="text-xs font-black uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                <span className="material-symbols-outlined text-sm text-voxmed-primary">clinical_notes</span>
                EHR Variables
              </CardTitle>
              <CardDescription className="text-[10px] leading-relaxed">
                Key data parsed by NLP parsing from your message stream.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-slate-100 dark:divide-zinc-800 text-[10px] select-none">
                <div className="flex justify-between items-center px-4 py-2.5">
                  <span className="text-muted-foreground uppercase tracking-wider">Patient Name</span>
                  <span className="font-bold text-slate-805 dark:text-zinc-200">
                    {sessionData?.patient_name || '—'}
                  </span>
                </div>
                <div className="flex justify-between items-center px-4 py-2.5">
                  <span className="text-muted-foreground uppercase tracking-wider">Age</span>
                  <span className="font-bold text-slate-805 dark:text-zinc-200">
                    {sessionData?.age || '—'}
                  </span>
                </div>
                <div className="flex justify-between items-center px-4 py-2.5">
                  <span className="text-muted-foreground uppercase tracking-wider">Contact Phone</span>
                  <span className="font-mono text-slate-700 dark:text-zinc-300">
                    {sessionData?.phone || '—'}
                  </span>
                </div>
                <div className="flex justify-between items-center px-4 py-2.5">
                  <span className="text-muted-foreground uppercase tracking-wider">Department</span>
                  <span className="font-bold text-voxmed-primary">
                    {sessionData?.department_name || '—'}
                  </span>
                </div>
                <div className="flex justify-between items-center px-4 py-2.5">
                  <span className="text-muted-foreground uppercase tracking-wider">Doctor Selection</span>
                  <span className="font-semibold text-slate-805 dark:text-zinc-200 truncate max-w-[110px]">
                    {sessionData?.doctor_name || '—'}
                  </span>
                </div>
                <div className="flex justify-between items-center px-4 py-2.5">
                  <span className="text-muted-foreground uppercase tracking-wider">Selected Slot</span>
                  <span className="font-semibold text-slate-805 dark:text-zinc-200">
                    {sessionData?.slot_time_str ? `${sessionData.slot_time_str}` : '—'}
                  </span>
                </div>
                {sessionData?.is_emergency && (
                  <div className="px-4 py-2 bg-red-50 dark:bg-red-950/20 text-red-700 dark:text-red-400 font-bold text-center border-t border-red-100 dark:border-red-900">
                    Emergency Flagged!
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Session Details Footer */}
          {sessionId && (
            <Card className="border border-dashed bg-slate-50/50 dark:bg-zinc-900/30 text-[10px]">
              <CardContent className="p-3 space-y-1">
                <div className="text-muted-foreground font-semibold">Active Session Key</div>
                <div className="font-mono text-slate-550 break-all select-all select-none bg-white dark:bg-zinc-950 border p-1 rounded">
                  {sessionId}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* ── Right Column: Interactive Chat Sandbox ── */}
        <div className="lg:col-span-3 space-y-4">
          <Card className="border shadow-sm flex flex-col h-[520px] bg-white dark:bg-zinc-900 overflow-hidden">
            <CardHeader className="border-b py-3 px-4 flex flex-row items-center justify-between bg-slate-50/50 dark:bg-zinc-955/30">
              <div className="flex items-center gap-2">
                <div className="h-7 w-7 rounded-full bg-voxmed-primary flex items-center justify-center text-white text-xs font-black shadow-md shrink-0">
                  A
                </div>
                <div>
                  <CardTitle className="text-xs font-black text-slate-900 dark:text-white leading-tight">
                    Reception Sandbox Dialogue
                  </CardTitle>
                  <CardDescription className="text-[10px]">
                    Anya AI Agent
                  </CardDescription>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleReset}
                className="h-8 text-[10px] font-semibold text-muted-foreground hover:text-red-500 border border-slate-205 hover:bg-slate-50"
              >
                <span className="material-symbols-outlined text-xs mr-1">refresh</span>
                Reset Session
              </Button>
            </CardHeader>

            <CardContent
              className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar bg-slate-50/30 dark:bg-zinc-955/10 text-xs"
            >
              {messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4">
                  <div className="h-12 w-12 rounded-2xl bg-voxmed-primary/10 flex items-center justify-center text-voxmed-primary mb-2 shadow-inner">
                    <span className="material-symbols-outlined text-2xl">chat_bubble</span>
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-800 dark:text-zinc-200 text-sm">Dialogue Sandbox is Ready</h3>
                    <p className="text-[10px] text-muted-foreground max-w-sm mt-1">
                      Start typing a request or click a prompt helper below to interact with our virtual triage and booking coordinator.
                    </p>
                  </div>
                  
                  {/* Suggestions block */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg w-full pt-4">
                    {SUGGESTIONS.map((item, idx) => (
                      <button
                        key={idx}
                        onClick={() => sendMessage(item.text)}
                        className="p-2.5 text-left border rounded-lg hover:border-voxmed-primary hover:bg-voxmed-primary/5 transition bg-white dark:bg-zinc-900 text-slate-750 dark:text-zinc-300 flex flex-col gap-0.5"
                      >
                        <span className="text-[9px] uppercase font-black text-voxmed-primary tracking-wide">
                          {item.label}
                        </span>
                        <span className="text-[10px] truncate max-w-full">
                          {item.text}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {messages.map((msg, index) => {
                    const isUser = msg.role === 'user';
                    return (
                      <div
                        key={index}
                        className={cn(
                          'flex items-start gap-2.5 max-w-[85%]',
                          isUser ? 'ml-auto justify-end' : 'mr-auto justify-start'
                        )}
                      >
                        {!isUser && (
                          <div className="h-7 w-7 rounded-full bg-voxmed-primary flex items-center justify-center text-white text-[10px] font-black shrink-0 mt-0.5">
                            A
                          </div>
                        )}
                        <div
                          className={cn(
                            'rounded-2xl px-3.5 py-2.5 border text-xs shadow-sm leading-relaxed',
                            isUser
                              ? 'bg-voxmed-primary border-transparent text-white rounded-tr-none'
                              : 'bg-white border-slate-100 text-slate-800 dark:bg-zinc-900 dark:border-zinc-800 dark:text-zinc-200 rounded-tl-none'
                          )}
                        >
                          <div className="text-[9px] font-black uppercase tracking-wider mb-1 opacity-80">
                            {isUser ? 'Attending Patient' : 'Anya AI Receptionist'}
                          </div>
                          <div>{msg.text}</div>
                        </div>
                        {isUser && (
                          <div className="h-7 w-7 rounded-full bg-slate-200 dark:bg-zinc-800 flex items-center justify-center text-slate-655 dark:text-zinc-400 text-[10px] font-black shrink-0 mt-0.5">
                            P
                          </div>
                        )}
                      </div>
                    );
                  })}
                  {isLoading && (
                    <div className="flex items-start gap-2.5 mr-auto justify-start">
                      <div className="h-7 w-7 rounded-full bg-voxmed-primary flex items-center justify-center text-white text-[10px] font-black shrink-0 animate-pulse mt-0.5">
                        A
                      </div>
                      <div className="bg-white border border-slate-100 rounded-2xl rounded-tl-none px-3.5 py-2.5 text-slate-500 dark:bg-zinc-900 dark:border-zinc-800 flex items-center gap-2">
                        <span className="h-1.5 w-1.5 rounded-full bg-voxmed-primary animate-bounce" style={{ animationDelay: '0ms' }} />
                        <span className="h-1.5 w-1.5 rounded-full bg-voxmed-primary animate-bounce" style={{ animationDelay: '150ms' }} />
                        <span className="h-1.5 w-1.5 rounded-full bg-voxmed-primary animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                  )}
                  <div ref={chatEndRef} />
                </div>
              )}
            </CardContent>
          </Card>

          {/* ── Input Box Panel ── */}
          <Card className="border shadow-sm bg-white dark:bg-zinc-900">
            <CardContent className="p-3">
              <div className="flex gap-2 items-center">
                <div className="relative flex-1">
                  <span className="material-symbols-outlined absolute left-3 top-2.5 text-muted-foreground text-base pointer-events-none">
                    keyboard
                  </span>
                  <Input
                    type="text"
                    value={input}
                    placeholder={isLoading ? "Anya is thinking..." : "Ask Anya to schedule a visit, report symptoms, select doctor..."}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        sendMessage(input);
                      }
                    }}
                    className="pl-9 h-9 text-xs"
                    disabled={isLoading}
                  />
                </div>
                <Button
                  onClick={() => sendMessage(input)}
                  disabled={isLoading || !input.trim()}
                  className="gradient-primary h-9 px-4 text-xs font-semibold flex items-center gap-1 shrink-0"
                >
                  <span className="material-symbols-outlined text-sm">send</span>
                  Send
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}