'use client';

import { useEffect, useRef } from 'react';
import { useWebsocket } from '@/hooks/use-websocket';
import { useAnalytics } from '@/hooks/use-analytics';
import { SENTIMENT_COLORS, CALL_STATUS_COLORS } from '@/lib/constants';
import { cn, formatDuration, formatDate } from '@/lib/utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

export default function CallsPage() {
  const {
    isConnected,
    activeCall,
    currentNode,
    waveform,
    liveTranscript,
    sentiment,
    sentimentScore,
  } = useWebsocket();

  const { calls } = useAnalytics();

  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll the live transcript container on new updates
  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  }, [liveTranscript]);

  // Define conversational progress nodes
  const nodes = [
    { key: 'GREETING', label: 'Greeting', icon: 'waving_hand' },
    { key: 'PATIENT_IDENTIFICATION', label: 'Auth Record', icon: 'badge' },
    { key: 'SYMPTOM_TRIAGE', label: 'Triage Triage', icon: 'thermostat' },
    { key: 'CLINIC_ROUTING', label: 'Routing', icon: 'lan' },
    { key: 'SLOT_LOOKUP', label: 'Slot Finder', icon: 'event_upcoming' },
    { key: 'CONFIRMATION', label: 'Validation', icon: 'rate_review' },
    { key: 'BOOKING_SUCCESS', label: 'EHR Sync', icon: 'task_alt' },
  ];

  return (
    <div className="space-y-6 select-none">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight">CareVoice Live Call Stream</h1>
          <p className="text-xs text-muted-foreground mt-1">
            Real-time visual monitoring of neural speech synthesis, interactive sentiment gauges, and live triage sessions.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={cn(
              'h-2.5 w-2.5 rounded-full pulse-ring',
              isConnected ? 'bg-emerald-500' : 'bg-red-500'
            )}
          ></span>
          <span
            className={cn(
              'text-xs font-bold uppercase tracking-wider',
              isConnected ? 'text-emerald-600' : 'text-red-500'
            )}
          >
            {isConnected ? 'Stream Link Active' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* ── CENTRAL SPLIT VIEW ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Visual Telemetry (Waveform, Nodes, Sentiment) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Active Call Panel & Dancing Waveform */}
          <Card className="border shadow-sm overflow-hidden bg-white dark:bg-zinc-900">
            <CardHeader className="p-5 pb-0 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base font-bold flex items-center gap-2">
                  <span className="material-symbols-outlined text-voxmed-primary animate-pulse">
                    settings_voice
                  </span>
                  Neural Audio Waveform
                </CardTitle>
                <CardDescription className="text-xs">
                  Decibel frequency amplitude of real-time speech synthesis signals
                </CardDescription>
              </div>

              {activeCall && (
                <div className="flex items-center gap-2">
                  <Badge className="bg-emerald-50 text-emerald-700 hover:bg-emerald-50 border border-emerald-200 text-[10px] font-black uppercase tracking-wider py-0.5 px-2.5 animate-bounce">
                    Speaking
                  </Badge>
                  <span className="text-xs font-bold text-slate-700 font-mono">
                    {formatDuration(activeCall.duration)}
                  </span>
                </div>
              )}
            </CardHeader>

            <CardContent className="p-6">
              {activeCall ? (
                <div className="space-y-6">
                  {/* Dancing Waveform Box */}
                  <div className="h-28 bg-slate-950 rounded-xl flex items-center justify-center gap-[3px] px-8 relative overflow-hidden select-none border border-slate-800">
                    {/* Visual glowing grids */}
                    <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:14px_14px]"></div>

                    {waveform.map((amp, idx) => (
                      <div
                        key={idx}
                        className="w-1 bg-gradient-to-t from-voxmed-primary via-blue-400 to-emerald-400 rounded-full transition-all duration-150 min-h-[4px]"
                        style={{ height: `${amp}%` }}
                      ></div>
                    ))}
                  </div>

                  {/* Active caller details */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-slate-50 dark:bg-zinc-800/30 rounded-xl border border-dashed text-xs">
                    <div className="space-y-0.5">
                      <span className="text-slate-400 font-medium">Patient Contact</span>
                      <p className="font-bold text-slate-800 dark:text-zinc-200">{activeCall.callerName}</p>
                    </div>
                    <div className="space-y-0.5">
                      <span className="text-slate-400 font-medium">Caller Number</span>
                      <p className="font-semibold text-slate-800 font-mono">{activeCall.callerPhone}</p>
                    </div>
                    <div className="space-y-0.5">
                      <span className="text-slate-400 font-medium">Identified Intent</span>
                      <p className="font-semibold text-slate-800 capitalize">{activeCall.intent}</p>
                    </div>
                    <div className="space-y-0.5">
                      <span className="text-slate-400 font-medium">Confidence Scale</span>
                      <p className="font-black text-voxmed-primary">
                        {Math.round(activeCall.aiConfidence * 100)}% Match
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-44 flex flex-col items-center justify-center text-center text-xs text-muted-foreground bg-slate-50/50 rounded-xl border border-dashed p-6">
                  <span className="material-symbols-outlined text-3xl text-slate-300 animate-pulse mb-2">
                    phone_disabled
                  </span>
                  <p className="font-semibold text-slate-600">No Active Speech Session</p>
                  <p className="font-light mt-1">Waiting for incoming SIP clinical routing calls...</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Conversation State Machine progress nodes flowchart */}
          <Card className="border shadow-sm bg-white">
            <CardHeader className="p-5 pb-0">
              <CardTitle className="text-base font-bold">Conversational State Broker</CardTitle>
              <CardDescription className="text-xs">
                Active workflow node mapping the AI voice agent dialogue logic progression
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              {activeCall ? (
                <div className="relative flex flex-col md:flex-row justify-between items-center gap-4 md:gap-2">
                  {/* Flow connection bar */}
                  <div className="hidden md:block absolute top-[22px] left-[5%] right-[5%] h-0.5 bg-slate-100 dark:bg-zinc-800 z-0"></div>

                  {nodes.map((nd, idx) => {
                    const isActive = currentNode === nd.key;
                    const isPassed =
                      nodes.findIndex((n) => n.key === currentNode) >
                      nodes.findIndex((n) => n.key === nd.key);

                    return (
                      <div
                        key={nd.key}
                        className="relative z-10 flex flex-col items-center gap-1.5 select-none"
                      >
                        <div
                          className={cn(
                            'h-11 w-11 rounded-full flex items-center justify-center transition-all border duration-300 shadow-sm',
                            isActive
                              ? 'bg-voxmed-primary border-transparent text-white ring-4 ring-voxmed-primary/20 scale-110 font-bold'
                              : isPassed
                              ? 'bg-emerald-50 border-emerald-200 text-emerald-600'
                              : 'bg-white border-slate-200 text-slate-400'
                          )}
                          title={nd.label}
                        >
                          <span className={cn('material-symbols-outlined text-lg', isActive && 'animate-pulse')}>
                            {nd.icon}
                          </span>
                        </div>
                        <span
                          className={cn(
                            'text-[9px] font-bold uppercase tracking-wider text-center max-w-[80px]',
                            isActive
                              ? 'text-voxmed-primary font-black'
                              : isPassed
                              ? 'text-emerald-600'
                              : 'text-slate-400'
                          )}
                        >
                          {nd.label}
                        </span>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="py-6 text-center text-xs text-muted-foreground italic">
                  Connect a telephone call to review live dialog routing.
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Live Transcription & Sentiment Gauges */}
        <div className="space-y-6">
          {/* Live Sentiment Gauge */}
          <Card className="border shadow-sm bg-white">
            <CardHeader className="p-5 pb-0">
              <CardTitle className="text-base font-bold">Real-time Sentiment Gauge</CardTitle>
              <CardDescription className="text-xs">
                Clinical NLP text matching sentiment value metrics
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5 pt-6 text-xs space-y-4">
              {activeCall ? (
                <div className="space-y-4">
                  {/* Circular/Gauge visual fallback - Thermometer */}
                  <div className="space-y-1">
                    <div className="flex justify-between items-center text-[10px] font-bold text-slate-600">
                      <span>Sentiment Score</span>
                      <span className={cn('font-black uppercase', SENTIMENT_COLORS[sentiment])}>
                        {sentiment} ({sentimentScore}%)
                      </span>
                    </div>
                    {/* Gauge bar */}
                    <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden border">
                      <div
                        className={cn(
                          'h-full rounded-full transition-all duration-500',
                          sentiment === 'positive'
                            ? 'bg-emerald-500'
                            : sentiment === 'negative'
                            ? 'bg-rose-500'
                            : 'bg-slate-400'
                        )}
                        style={{ width: `${sentimentScore}%` }}
                      ></div>
                    </div>
                  </div>

                  <div className="text-[10px] text-muted-foreground leading-normal font-light">
                    NLP analysis detects voice fluctuations and response vocabulary keywords to map patient anxiety.
                  </div>
                </div>
              ) : (
                <div className="py-6 text-center text-muted-foreground italic">
                  Waiting for active speech logs.
                </div>
              )}
            </CardContent>
          </Card>

          {/* AI Call Transcript Stream */}
          <Card className="border shadow-sm flex flex-col h-[350px] bg-slate-950 text-slate-100 border-slate-800">
            <CardHeader className="p-4 border-b border-slate-800 shrink-0">
              <CardTitle className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-red-500 animate-ping"></span>
                Typewriter Transcript Stream
              </CardTitle>
            </CardHeader>

            <CardContent
              ref={scrollContainerRef}
              className="p-4 flex-1 overflow-y-auto custom-scrollbar font-mono text-[11px] leading-relaxed space-y-3 bg-black/40 text-slate-300"
            >
              {liveTranscript ? (
                liveTranscript.split('\n').map((line, idx) => {
                  const isAI = line.startsWith('AI:');
                  return (
                    <div
                      key={idx}
                      className={cn(
                        'p-2 rounded-lg border text-left',
                        isAI
                          ? 'bg-voxmed-primary/10 border-voxmed-primary/20 text-blue-200 ml-1 mr-6'
                          : 'bg-slate-800/40 border-slate-800 text-slate-100 mr-1 ml-6'
                      )}
                    >
                      <span className="font-bold block text-[9px] uppercase tracking-wider mb-0.5 text-slate-400">
                        {isAI ? 'CareVoice AI Speech' : 'Attending Patient'}
                      </span>
                      {line.replace(/^(AI:|Patient:)\s*/, '')}
                    </div>
                  );
                })
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center text-slate-500">
                  <span className="material-symbols-outlined text-2xl animate-spin mb-1">
                    sync
                  </span>
                  <span>Connecting to Live Transcript...</span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Historical calls logs log */}
      <Card className="border shadow-sm bg-white">
        <CardHeader className="p-5 pb-0 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-base font-bold">Speech Session History Log</CardTitle>
            <CardDescription className="text-xs">
              Archive records of preceding CareVoice AI calls and routing outcomes
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto custom-scrollbar">
            <table className="w-full text-left border-collapse mt-4">
              <thead>
                <tr className="border-y border-border text-[10px] font-bold text-muted-foreground uppercase bg-slate-50/50 dark:bg-zinc-800/20 select-none">
                  <th className="px-5 py-3 font-semibold">Session ID</th>
                  <th className="px-5 py-3 font-semibold">Caller Contact</th>
                  <th className="px-5 py-3 font-semibold">Intent</th>
                  <th className="px-5 py-3 font-semibold">Routing Clinic</th>
                  <th className="px-5 py-3 font-semibold">Evaluated CSAT</th>
                  <th className="px-5 py-3 font-semibold">Evaluation Outcome</th>
                  <th className="px-5 py-3 font-semibold text-right">Duration</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-xs">
                {calls
                  .filter((c) => c.status === 'completed' || c.status === 'failed')
                  .map((c) => (
                    <tr key={c.id} className="hover:bg-slate-50/50 dark:hover:bg-zinc-800/20">
                      <td className="px-5 py-3.5 font-bold text-slate-500">#{c.id.slice(0, 12)}</td>
                      <td className="px-5 py-3.5">
                        <div className="flex flex-col">
                          <span className="font-bold text-slate-800">{c.callerName}</span>
                          <span className="text-[10px] text-muted-foreground font-mono mt-0.5">{c.callerPhone}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5 font-semibold text-slate-700">{c.intent}</td>
                      <td className="px-5 py-3.5 font-medium text-slate-800">{c.department || 'Not Routed'}</td>
                      <td className="px-5 py-3.5 font-bold">
                        <span className={cn('capitalize text-[11px]', SENTIMENT_COLORS[c.sentiment])}>
                          {c.sentiment}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-muted-foreground max-w-xs truncate" title={c.resolution}>
                        {c.resolution || 'Call did not reach resolution phase.'}
                      </td>
                      <td className="px-5 py-3.5 text-right font-medium text-slate-600">
                        {formatDuration(c.duration)}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
