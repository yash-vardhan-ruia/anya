import { useState, useRef, useEffect, useCallback } from 'react';

export type DoctorCard = {
  id: string;
  name: string;
  specialization: string;
  qualification: string;
  experience_years: number;
  fee_inr: number;
};

export type SlotCard = {
  id: string;
  date: string;
  day: string;
  start_time: string;
  end_time: string;
  date_iso: string;
};

export type TranscriptEntry = {
  role: 'user' | 'assistant';
  text: string;
  timestamp: string;
};

export function useVoiceSession(sessionKey: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [status, setStatus] = useState<'idle' | 'connecting' | 'connected' | 'listening' | 'speaking' | 'completed' | 'error'>('idle');
  const [transcripts, setTranscripts] = useState<TranscriptEntry[]>([]);
  const [sessionState, setSessionState] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [isMuted, setIsMuted] = useState(false);

  // New Hybrid UX States
  const [activeInput, setActiveInput] = useState<{field: string, label: string, placeholder: string} | null>(null);
  const [doctorOptions, setDoctorOptions] = useState<DoctorCard[] | null>(null);
  const [doctorDepartment, setDoctorDepartment] = useState<string>('');
  const [slotOptions, setSlotOptions] = useState<SlotCard[] | null>(null);
  const [slotDoctorName, setSlotDoctorName] = useState<string>('');
  const [paymentUrl, setPaymentUrl] = useState<string | null>(null);
  const [paymentAmount, setPaymentAmount] = useState<number | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioProcessorRef = useRef<ScriptProcessorNode | null>(null);
  const sourceNodeRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const nextPlaybackTimeRef = useRef<number>(0);
  const activeSourcesRef = useRef<AudioBufferSourceNode[]>([]);

  const statusRef = useRef(status);
  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  const startSession = useCallback(async () => {
    try {
      setStatus('connecting');
      setError(null);
      setTranscripts([]);
      setSessionState(null);
      
      setActiveInput(null);
      setDoctorOptions(null);
      setSlotOptions(null);
      setPaymentUrl(null);
      setPaymentAmount(null);
      setDoctorDepartment('');
      setSlotDoctorName('');
      activeSourcesRef.current = [];
      nextPlaybackTimeRef.current = 0;

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      });
      mediaStreamRef.current = stream;

      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
      const ws = new WebSocket(`${wsUrl}/api/v1/ws/live-voice/${sessionKey}`);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        setStatus('connecting'); // wait for gemini setupComplete
      };

      ws.onmessage = async (event) => {
        const data = JSON.parse(event.data);
        const type = data.type;

        if (type === 'status') {
          setStatus(data.status);
        } else if (type === 'transcript') {
          setTranscripts(prev => {
            if (prev.length > 0 && prev[prev.length - 1].role === data.role) {
              const updated = [...prev];
              updated[updated.length - 1] = {
                ...updated[updated.length - 1],
                text: updated[updated.length - 1].text + data.text
              };
              return updated;
            } else {
              return [...prev, {
                role: data.role,
                text: data.text,
                timestamp: new Date().toISOString()
              }];
            }
          });
        } else if (type === 'state') {
          setSessionState(data.data);
          if (data.data && data.data.email) {
            setActiveInput(null);
          }
        } else if (type === 'audio') {
          setStatus('speaking');
          playAudio(data.data);
        } else if (type === 'control') {
          if (data.action === 'clear') {
            // Audio barge-in (interrupted)
            activeSourcesRef.current.forEach(source => {
              try { source.stop(); } catch (e) {}
            });
            activeSourcesRef.current = [];
            nextPlaybackTimeRef.current = 0;
            setStatus('listening');
          }
        } else if (type === 'request_input') {
          setActiveInput({
            field: data.field,
            label: data.label || 'Enter your information',
            placeholder: data.placeholder || '',
          });
        } else if (type === 'show_doctors') {
          setDoctorOptions(data.doctors);
          setDoctorDepartment(data.department || '');
          setSlotOptions(null);
        } else if (type === 'show_slots') {
          setSlotOptions(data.slots);
          setSlotDoctorName(data.doctor_name || '');
          setDoctorOptions(null);
        } else if (type === 'redirect_payment') {
          setPaymentUrl(data.payment_url);
          setPaymentAmount(data.amount_inr);
          if (data.payment_url) {
            window.open(data.payment_url, '_blank', 'noopener,noreferrer');
          }
        }
      };

      ws.onerror = () => {
        setError("WebSocket connection error");
        stopSession();
      };

      ws.onclose = () => {
        setIsConnected(false);
        stopSession();
      };

      // Audio setup
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
      audioContextRef.current = audioCtx;
      
      const source = audioCtx.createMediaStreamSource(stream);
      sourceNodeRef.current = source;
      
      // Highpass filter (cut off rumble below 80Hz)
      const hpFilter = audioCtx.createBiquadFilter();
      hpFilter.type = 'highpass';
      hpFilter.frequency.value = 80;
      
      // Lowpass filter (cut off high-frequency hiss/noise above 7000Hz)
      const lpFilter = audioCtx.createBiquadFilter();
      lpFilter.type = 'lowpass';
      lpFilter.frequency.value = 7000;
      
      const processor = audioCtx.createScriptProcessor(1024, 1, 1);
      audioProcessorRef.current = processor;
      
      // Connect filters in series: source -> highpass -> lowpass -> processor
      source.connect(hpFilter);
      hpFilter.connect(lpFilter);
      lpFilter.connect(processor);
      processor.connect(audioCtx.destination);
      
      processor.onaudioprocess = (e) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN || isMutedRef.current) return;
        
        const inputData = e.inputBuffer.getChannelData(0);
        // Convert Float32 to Int16
        const pcm16 = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          let s = Math.max(-1, Math.min(1, inputData[i]));
          pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        
        // Base64 encode
        const uint8Array = new Uint8Array(pcm16.buffer);
        let binary = '';
        for (let i = 0; i < uint8Array.byteLength; i++) {
          binary += String.fromCharCode(uint8Array[i]);
        }
        const b64 = btoa(binary);
        
        wsRef.current.send(JSON.stringify({ type: 'audio', data: b64 }));
      };

    } catch (err: any) {
      setError(err.message || "Could not access microphone");
      setStatus('error');
    }
  }, [sessionKey]);

  const isMutedRef = useRef(isMuted);
  useEffect(() => {
    isMutedRef.current = isMuted;
  }, [isMuted]);

  const toggleMute = useCallback(() => {
    setIsMuted(prev => !prev);
  }, []);

  const stopSession = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (audioProcessorRef.current) {
      audioProcessorRef.current.disconnect();
      audioProcessorRef.current = null;
    }
    if (sourceNodeRef.current) {
      sourceNodeRef.current.disconnect();
      sourceNodeRef.current = null;
    }
    activeSourcesRef.current.forEach(source => {
      try { source.stop(); } catch (e) {}
    });
    activeSourcesRef.current = [];
    nextPlaybackTimeRef.current = 0;
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }
    setIsConnected(false);
    if (status !== 'completed') {
      setStatus('idle');
    }
  }, [status]);

  const playAudio = async (base64Audio: string) => {
    if (!audioContextRef.current) return;
    try {
      const binaryStr = atob(base64Audio);
      const len = binaryStr.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) {
        bytes[i] = binaryStr.charCodeAt(i);
      }
      
      const buffer = bytes.buffer;
      // 24kHz Int16 from Gemini
      const int16Array = new Int16Array(buffer);
      
      const audioBuffer = audioContextRef.current.createBuffer(1, int16Array.length, 24000);
      const channelData = audioBuffer.getChannelData(0);
      
      for (let i = 0; i < int16Array.length; i++) {
        channelData[i] = int16Array[i] / 0x8000;
      }
      
      const source = audioContextRef.current.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContextRef.current.destination);
      
      // Schedule playback time sequentially
      const now = audioContextRef.current.currentTime;
      let playbackTime = nextPlaybackTimeRef.current;
      
      if (playbackTime < now) {
        playbackTime = now;
      }
      
      source.start(playbackTime);
      activeSourcesRef.current.push(source);
      
      nextPlaybackTimeRef.current = playbackTime + audioBuffer.duration;
      
      source.onended = () => {
        activeSourcesRef.current = activeSourcesRef.current.filter(src => src !== source);
        if (activeSourcesRef.current.length === 0 && statusRef.current === 'speaking') {
          setStatus('listening');
        }
      };
    } catch (e) {
      console.error("Audio playback error", e);
    }
  };

  const submitInput = (field: string, value: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'input_submit',
        field,
        value,
      }));
      setActiveInput(null);
    }
  };

  const selectDoctor = (doctor: DoctorCard) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'selection',
        field: 'doctor',
        value: { id: doctor.id, name: doctor.name },
      }));
      setDoctorOptions(null);
    }
  };

  const selectSlot = (slot: SlotCard) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'selection',
        field: 'slot',
        value: {
          id: slot.id,
          date: slot.date,
          start_time: slot.start_time,
          end_time: slot.end_time,
        },
      }));
      setSlotOptions(null);
    }
  };

  return {
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
  };
}
