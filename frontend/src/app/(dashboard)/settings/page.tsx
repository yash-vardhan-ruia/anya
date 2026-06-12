'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';

export default function SettingsPage() {
  const [isSaving, setIsSaving] = useState(false);

  // Hospital settings state
  const [hospitalName, setHospitalName] = useState('VoxMed Multispecialty Hospital Core');
  const [voipTrunk, setVoipTrunk] = useState('+91 80 4920 1800');
  const [timezone, setTimezone] = useState('Asia/Kolkata (IST)');

  // Voice engine state
  const [voiceProvider, setVoiceProvider] = useState('cartesia');
  const [voiceModel, setVoiceModel] = useState('sonic-english-v2');
  const [reassuranceLevel, setReassuranceLevel] = useState(85);
  const [speechRate, setSpeechRate] = useState(1.05);

  // Escalation limits
  const [csatThreshold, setCsatThreshold] = useState(3.5);
  const [confidenceFloor, setConfidenceFloor] = useState(70);
  const [maxQueueHold, setMaxQueueHold] = useState(45);

  const handleSaveSettings = () => {
    setIsSaving(true);
    setTimeout(() => {
      setIsSaving(false);
      alert('Clinical operations profiles saved successfully! Config synchronized with CareVoice AI speech engines.');
    }, 1000);
  };

  return (
    <div className="space-y-6 select-none max-w-4xl">
      {/* Header */}
      <div className="flex justify-between items-center border-b pb-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight">System Settings & AI Core</h1>
          <p className="text-xs text-muted-foreground mt-1">
            Configure hospital VoIP lines, select neural speech model nodes, and specify triage safety protocols.
          </p>
        </div>
        <Button
          onClick={handleSaveSettings}
          className="gradient-primary h-9 px-4 text-xs font-semibold"
          disabled={isSaving}
        >
          {isSaving ? 'Syncing Engine...' : 'Save Configurations'}
        </Button>
      </div>

      <Tabs defaultValue="general" className="w-full">
        <TabsList className="grid w-full grid-cols-3 h-10 bg-slate-100 dark:bg-zinc-800 p-1 rounded-lg">
          <TabsTrigger value="general" className="text-xs font-bold py-1.5 rounded-md">
            General EHR Details
          </TabsTrigger>
          <TabsTrigger value="voice" className="text-xs font-bold py-1.5 rounded-md">
            AI Speech Engine
          </TabsTrigger>
          <TabsTrigger value="escalation" className="text-xs font-bold py-1.5 rounded-md">
            Escalation Protocols
          </TabsTrigger>
        </TabsList>

        {/* Tab 1: General Details */}
        <TabsContent value="general" className="space-y-4 mt-4">
          <Card className="border shadow-sm">
            <CardHeader>
              <CardTitle className="text-base font-bold">Attending Facility Profile</CardTitle>
              <CardDescription className="text-xs">
                Timezones and telephone trunks registered for EHR direct scheduling integrations.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-xs">
              <div className="space-y-1.5">
                <label className="font-semibold text-slate-700">Hospital Facility Name</label>
                <Input
                  value={hospitalName}
                  onChange={(e) => setHospitalName(e.target.value)}
                  className="h-9 text-xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="font-semibold text-slate-700">SIP VoIP Telephone Trunk</label>
                  <Input
                    value={voipTrunk}
                    onChange={(e) => setVoipTrunk(e.target.value)}
                    className="h-9 text-xs font-mono"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="font-semibold text-slate-700">Active Shift Timezone</label>
                  <Input
                    value={timezone}
                    onChange={(e) => setTimezone(e.target.value)}
                    className="h-9 text-xs"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 2: Speech Synthesis Engine */}
        <TabsContent value="voice" className="space-y-4 mt-4">
          <Card className="border shadow-sm">
            <CardHeader>
              <CardTitle className="text-base font-bold">Neural Speech Synthesizer</CardTitle>
              <CardDescription className="text-xs">
                Manage low-latency vocoders, Attending Nurse vocal tones, and reassuring clinical rates.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-4">
                {/* Voice Provider selector */}
                <div className="space-y-1.5">
                  <label className="font-semibold text-slate-700">Speech Model Node</label>
                  <div className="relative">
                    <select
                      value={voiceProvider}
                      onChange={(e) => setVoiceProvider(e.target.value)}
                      className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-xs ring-offset-background appearance-none cursor-pointer font-medium pr-8"
                    >
                      <option value="cartesia">Cartesia Sonic (ultra low latency 85ms)</option>
                      <option value="elevenlabs">ElevenLabs Multilingual v2 (highly realistic)</option>
                      <option value="openai">OpenAI TTS Realtime Stream (natural tone)</option>
                    </select>
                    <span className="material-symbols-outlined absolute right-2 top-2 text-muted-foreground text-base pointer-events-none">
                      arrow_drop_down
                    </span>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="font-semibold text-slate-700">Attending Vocal Tone</label>
                  <div className="relative">
                    <select
                      value={voiceModel}
                      onChange={(e) => setVoiceModel(e.target.value)}
                      className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-xs ring-offset-background appearance-none cursor-pointer font-medium pr-8"
                    >
                      <option value="sonic-english-v2">Nurse Reassuring Clear Voice (Female)</option>
                      <option value="sonic-english-pediatric">Pediatric Reassuring Calm Voice (Female)</option>
                      <option value="sonic-english-senior">Attending Dr. Professional (Male)</option>
                    </select>
                    <span className="material-symbols-outlined absolute right-2 top-2 text-muted-foreground text-base pointer-events-none">
                      arrow_drop_down
                    </span>
                  </div>
                </div>
              </div>

              {/* Slider variables */}
              <div className="grid grid-cols-2 gap-6 pt-3 border-t border-dashed">
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <label className="font-semibold text-slate-700">Vocal Reassurance Amplitude</label>
                    <span className="font-bold text-voxmed-primary">{reassuranceLevel}%</span>
                  </div>
                  <input
                    type="range"
                    min="50"
                    max="100"
                    value={reassuranceLevel}
                    onChange={(e) => setReassuranceLevel(Number(e.target.value))}
                    className="w-full accent-voxmed-primary cursor-pointer"
                  />
                  <span className="text-[10px] text-slate-400 font-light block leading-none">
                    Controls soft/pitch frequency algorithms during pediatric/anxiety distress triages.
                  </span>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <label className="font-semibold text-slate-700">Speech Cadence / Rate</label>
                    <span className="font-bold text-voxmed-primary">{speechRate}x speed</span>
                  </div>
                  <input
                    type="range"
                    min="80"
                    max="150"
                    step="5"
                    value={speechRate * 100}
                    onChange={(e) => setSpeechRate(Number(e.target.value) / 100)}
                    className="w-full accent-voxmed-primary cursor-pointer"
                  />
                  <span className="text-[10px] text-slate-400 font-light block leading-none">
                    Calibrates words-per-minute tempo. Slower rates auto-trigger on emergency symptom triage inputs.
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 3: Escalation Thresholds */}
        <TabsContent value="escalation" className="space-y-4 mt-4">
          <Card className="border shadow-sm">
            <CardHeader>
              <CardTitle className="text-base font-bold">Active Call Safety Parameters</CardTitle>
              <CardDescription className="text-xs">
                Specify clinical emergency thresholds. CareVoice auto-escalates calls to live hospital operators under these bounds.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5 text-xs">
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-1.5">
                  <label className="font-semibold text-slate-700 block">CSAT Safety Floor</label>
                  <div className="relative">
                    <Input
                      type="number"
                      step="0.1"
                      min="1.0"
                      max="5.0"
                      value={csatThreshold}
                      onChange={(e) => setCsatThreshold(Number(e.target.value))}
                      className="h-9 text-xs"
                    />
                    <span className="text-[9px] text-slate-400 font-medium block mt-1 leading-normal">
                      Transfer call to staff if post-sentence NLP sentiment slips below this rating.
                    </span>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="font-semibold text-slate-700 block">EHR Confidence Floor</label>
                  <div className="relative">
                    <Input
                      type="number"
                      min="50"
                      max="100"
                      value={confidenceFloor}
                      onChange={(e) => setConfidenceFloor(Number(e.target.value))}
                      className="h-9 text-xs"
                    />
                    <span className="text-[9px] text-slate-400 font-medium block mt-1 leading-normal">
                      Auto-transfer to receptionist if patient demographic matching falls below this accuracy percentage.
                    </span>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="font-semibold text-slate-700 block">Max Trunk Queue Hold</label>
                  <div className="relative">
                    <Input
                      type="number"
                      min="10"
                      max="300"
                      value={maxQueueHold}
                      onChange={(e) => setMaxQueueHold(Number(e.target.value))}
                      className="h-9 text-xs font-mono"
                    />
                    <span className="text-[9px] text-slate-400 font-medium block mt-1 leading-normal">
                      Max seconds patient may wait in SIP queues before auto-routing to reception operators.
                    </span>
                  </div>
                </div>
              </div>

              <div className="p-3 bg-amber-50 rounded-lg border border-amber-200 flex gap-3 mt-4 text-[11px] leading-relaxed text-amber-800">
                <span className="material-symbols-outlined text-base shrink-0 mt-0.5">
                  gavel
                </span>
                <div>
                  <span className="font-bold block">EHR HIPAA & Medical Regulatory Notice</span>
                  <span>
                    Emergency symptom triage triggers (e.g. chest pain, breathing labor, severe anaphylaxis) bypass all settings, auto-routing instantly to clinical ER triage nurses while displaying emergency instructions on the recipient screen.
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
