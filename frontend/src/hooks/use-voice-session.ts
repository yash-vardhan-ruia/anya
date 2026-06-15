'use client';

import { useState, useEffect, useRef } from 'react';

export type VoiceMessage = {
  role: 'user' | 'assistant';
  text: string;
};

export type VoiceStatus = 'idle' | 'connecting' | 'connected' | 'listening' | 'speaking' | 'completed' | 'error';

export function useVoiceSession(sessionId: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [status, setStatus] = useState<VoiceStatus>('idle');
  const [transcripts, setTranscripts] = useState<VoiceMessage[]>([]);
  const [sessionState, setSessionState] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [isMuted, setIsMuted] = useState(false);
  const isMutedRef = useRef(false);

  const toggleMute = () => {
    const newVal = !isMutedRef.current;
    isMutedRef.current = newVal;
    setIsMuted(newVal);
    loggerDebug(`Muted state toggled to: ${newVal}`);
  };

  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const microphoneStreamRef = useRef<MediaStream | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const playSourcesRef = useRef<AudioBufferSourceNode[]>([]);
  const nextStartTimeRef = useRef<number>(0);

  // Playback sample rate from Gemini is 24kHz
  const GEMINI_OUTPUT_SAMPLE_RATE = 24000;

  // URL setup
  const wsBaseUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
  const wsUrl = `${wsBaseUrl}/ws/live-voice/${sessionId}`;

  const stopAllPlayback = () => {
    playSourcesRef.current.forEach((source) => {
      try {
        source.stop();
      } catch (err) {
        // Already stopped or not started
      }
    });
    playSourcesRef.current = [];
    nextStartTimeRef.current = 0;
  };

  const playAudioChunk = (float32Data: Float32Array) => {
    if (!audioContextRef.current) return;

    const ctx = audioContextRef.current;
    
    // Create AudioBuffer for 24kHz Mono PCM
    const buffer = ctx.createBuffer(1, float32Data.length, GEMINI_OUTPUT_SAMPLE_RATE);
    buffer.getChannelData(0).set(float32Data);

    const source = ctx.createBufferSource();
    source.buffer = buffer;
    source.connect(ctx.destination);

    const currentTime = ctx.currentTime;
    if (nextStartTimeRef.current < currentTime) {
      nextStartTimeRef.current = currentTime;
    }

    source.start(nextStartTimeRef.current);
    nextStartTimeRef.current += buffer.duration;

    // Track active sources for barge-in stopping
    playSourcesRef.current.push(source);
    source.onended = () => {
      playSourcesRef.current = playSourcesRef.current.filter((s) => s !== source);
    };

    // Update status to speaking while audio is queued
    setStatus('speaking');
    
    // Clear speaking status back to listening shortly after last chunk finishes playing
    const checkListening = () => {
      if (ctx.currentTime >= nextStartTimeRef.current && wsRef.current) {
        setStatus('listening');
      }
    };
    setTimeout(checkListening, (nextStartTimeRef.current - ctx.currentTime) * 1000 + 100);
  };

  const startSession = async () => {
    try {
      setStatus('connecting');
      setError(null);
      setTranscripts([]);
      setIsMuted(false);
      isMutedRef.current = false;

      // 1. Initialize Audio Context
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      audioContextRef.current = audioCtx;
      nextStartTimeRef.current = 0;

      // 2. Request Mic Permission and capture stream
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
      microphoneStreamRef.current = stream;

      // 3. Load AudioWorklet for downsampling (Float32 -> Int16 PCM 16kHz)
      await audioCtx.audioWorklet.addModule('/pcm-processor.js');
      const workletNode = new AudioWorkletNode(audioCtx, 'pcm-processor');
      workletNodeRef.current = workletNode;

      const sourceNode = audioCtx.createMediaStreamSource(stream);
      sourceNode.connect(workletNode);
      workletNode.connect(audioCtx.destination); // Required to keep processor alive

      // 4. Establish WebSocket connection
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        setStatus('connected');
        loggerDebug('WebSocket connected to live-voice proxy.');
      };

      ws.onmessage = async (event) => {
        const data = JSON.parse(event.data);
        const type = data.type;

        if (type === 'status') {
          const wsStatus = data.status;
          loggerDebug(`Proxy Status: ${wsStatus} - ${data.message || ''}`);
          if (wsStatus === 'completed') {
            setStatus('completed');
            stopSession();
          } else if (wsStatus === 'listening') {
            setStatus('listening');
          }
        } else if (type === 'state') {
          setSessionState(data.data);
        } else if (type === 'transcript') {
          const role = data.role;
          const text = data.text;
          
          setTranscripts((prev) => {
            // Check if last message is same role, merge or append
            if (prev.length > 0 && prev[prev.length - 1].role === role) {
              const updated = [...prev];
              updated[updated.length - 1] = {
                role,
                text: updated[updated.length - 1].text + text,
              };
              return updated;
            } else {
              return [...prev, { role, text }];
            }
          });
        } else if (type === 'audio') {
          // Playback 24kHz audio from Gemini
          const base64Data = data.data;
          const arrayBuffer = base64ToArrayBuffer(base64Data);
          const int16Array = new Int16Array(arrayBuffer);
          
          // Convert Int16 PCM back to Float32 for Web Audio API
          const float32Array = new Float32Array(int16Array.length);
          for (let i = 0; i < int16Array.length; i++) {
            float32Array[i] = int16Array[i] / 32768.0;
          }
          
          playAudioChunk(float32Array);
        } else if (type === 'control') {
          if (data.action === 'clear') {
            loggerDebug('User Barge-in. Clearing audio queue.');
            stopAllPlayback();
            setStatus('listening');
          }
        }
      };

      ws.onerror = (err) => {
        console.error('WebSocket Live Voice Error:', err);
        setError('Connection error occurred.');
        setStatus('error');
      };

      ws.onclose = () => {
        setIsConnected(false);
        if (status !== 'completed' && status !== 'idle') {
          setStatus('idle');
        }
        loggerDebug('WebSocket closed.');
      };

      // Handle Worklet messages (mic input ready to stream)
      workletNode.port.onmessage = (event) => {
        if (isMutedRef.current) return;
        const int16Buffer = new Int16Array(event.data);
        const base64Pcm = int16ToBase64(int16Buffer);

        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: 'audio',
            data: base64Pcm,
          }));
        }
      };

    } catch (err: any) {
      console.error('Failed to initialize live voice session:', err);
      setError(err.message || 'Microphone access denied or audio device configuration failed.');
      setStatus('error');
    }
  };

  const stopSession = () => {
    // Stop recording
    if (microphoneStreamRef.current) {
      microphoneStreamRef.current.getTracks().forEach((track) => track.stop());
      microphoneStreamRef.current = null;
    }
    if (workletNodeRef.current) {
      workletNodeRef.current.disconnect();
      workletNodeRef.current = null;
    }

    // Stop playback
    stopAllPlayback();

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    // Close socket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
    if (status !== 'completed') {
      setStatus('idle');
    }
  };

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (microphoneStreamRef.current) {
        microphoneStreamRef.current.getTracks().forEach((track) => track.stop());
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  // Helper conversions
  const base64ToArrayBuffer = (base64: string): ArrayBuffer => {
    const binaryString = window.atob(base64);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
  };

  const int16ToBase64 = (buffer: Int16Array): string => {
    let binary = '';
    const bytes = new Uint8Array(buffer.buffer);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
  };

  const loggerDebug = (msg: string) => {
    console.log(`[VoiceSessionHook] ${msg}`);
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
  };
}
