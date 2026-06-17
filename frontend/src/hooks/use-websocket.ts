'use client';

import { useState, useEffect, useRef } from 'react';
import type { VoiceSession } from '@/types/api';
import { WS_URL } from '@/lib/constants';

interface WebSocketMessage {
  type: 'call_start' | 'call_update' | 'call_end' | 'transcript_chunk' | 'waveform_pulse' | 'node_change' | 'sentiment_change';
  payload: any;
}

export type ConversationNode = 'GREETING' | 'PATIENT_IDENTIFICATION' | 'SYMPTOM_TRIAGE' | 'CLINIC_ROUTING' | 'SLOT_LOOKUP' | 'CONFIRMATION' | 'BOOKING_SUCCESS';

export interface RealtimeCallState {
  activeCall: VoiceSession | null;
  currentNode: ConversationNode;
  waveform: number[];
  liveTranscript: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  sentimentScore: number; // 0 to 100
}

const DIALOGUE_FLOW = [
  {
    node: 'GREETING' as ConversationNode,
    sentiment: 'neutral' as const,
    score: 50,
    text: "AI: Thank you for calling VoxMed Hospital. I am CareVoice, your virtual clinical assistant. How can I help you today?"
  },
  {
    node: 'PATIENT_IDENTIFICATION' as ConversationNode,
    sentiment: 'neutral' as const,
    score: 55,
    text: "\nPatient: Yes, hello. I need to book a clinical appointment for my daughter. Her name is Zoya Patel."
  },
  {
    node: 'PATIENT_IDENTIFICATION' as ConversationNode,
    sentiment: 'positive' as const,
    score: 75,
    text: "\nAI: I have retrieved Zoya Patel's electronic patient record. For confirmation, could you please state Zoya's date of birth or the last four digits of the registered mobile number?"
  },
  {
    node: 'PATIENT_IDENTIFICATION' as ConversationNode,
    sentiment: 'neutral' as const,
    score: 60,
    text: "\nPatient: Sure, her date of birth is July 4th, 2018."
  },
  {
    node: 'SYMPTOM_TRIAGE' as ConversationNode,
    sentiment: 'positive' as const,
    score: 80,
    text: "\nAI: Verification successful. Thank you. How is Zoya feeling, and what symptoms is she experiencing?"
  },
  {
    node: 'SYMPTOM_TRIAGE' as ConversationNode,
    sentiment: 'negative' as const,
    score: 35,
    text: "\nPatient: She has a low-grade fever that's been hovering around 99.8 degrees for the last four days, and she has this persistent dry cough that gets worse at night. I am getting really worried."
  },
  {
    node: 'CLINIC_ROUTING' as ConversationNode,
    sentiment: 'neutral' as const,
    score: 55,
    text: "\nAI: I understand your concern, and I am here to help. A persistent fever over four days with a nocturnal cough indicates she should be evaluated by a pediatrician. Let me connect to our pediatric scheduling coordinator. One moment."
  },
  {
    node: 'SLOT_LOOKUP' as ConversationNode,
    sentiment: 'neutral' as const,
    score: 60,
    text: "\nAI: I see that our primary pediatrician, Dr. Rajesh Nair, is available in the Pediatric Clinic today. I have two available slots: one at 2:30 PM this afternoon, and another at 4:15 PM. Do either of these work for you?"
  },
  {
    node: 'SLOT_LOOKUP' as ConversationNode,
    sentiment: 'positive' as const,
    score: 78,
    text: "\nPatient: Yes! The 2:30 PM slot is perfect. Let's take that."
  },
  {
    node: 'CONFIRMATION' as ConversationNode,
    sentiment: 'positive' as const,
    score: 85,
    text: "\nAI: Excellent. I am booking a Pediatric Consultation for Zoya Patel with Dr. Rajesh Nair today, May 29th, at 2:30 PM. I am adding her clinical symptoms (fever of 4 days, nighttime cough) to the physician notes. Is this correct?"
  },
  {
    node: 'CONFIRMATION' as ConversationNode,
    sentiment: 'positive' as const,
    score: 90,
    text: "\nPatient: Yes, that is completely correct. Thank you so much, CareVoice."
  },
  {
    node: 'BOOKING_SUCCESS' as ConversationNode,
    sentiment: 'positive' as const,
    score: 98,
    text: "\nAI: Done! The appointment has been successfully scheduled. Zoya is booked for 2:30 PM today in Pediatric Clinic Cabin 4. I have sent a confirmation email with map directions and a parking pass to your email. Please arrive 10 minutes early. Is there anything else I can assist you with?"
  },
  {
    node: 'BOOKING_SUCCESS' as ConversationNode,
    sentiment: 'positive' as const,
    score: 99,
    text: "\nPatient: No, that's all. You've been extremely helpful. Thank you!"
  },
  {
    node: 'BOOKING_SUCCESS' as ConversationNode,
    sentiment: 'positive' as const,
    score: 100,
    text: "\nAI: You're very welcome. I hope Zoya feels much better soon. Thank you for calling VoxMed. Goodbye!"
  }
];

export function useWebsocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [callState, setCallState] = useState<RealtimeCallState>({
    activeCall: null,
    currentNode: 'GREETING',
    waveform: Array(30).fill(10),
    liveTranscript: '',
    sentiment: 'neutral',
    sentimentScore: 50,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const simIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const dialogueIndexRef = useRef(0);

  useEffect(() => {
    // ── Attempt WebSocket Connection ──────────────────────────
    try {
      const socket = new WebSocket(WS_URL);
      wsRef.current = socket;

      socket.onopen = () => {
        setIsConnected(true);
        console.log('Successfully connected to CareVoice AI Live Call Stream');
      };

      socket.onmessage = (event) => {
        try {
          const msg: WebSocketMessage = JSON.parse(event.data);
          handleWebSocketMessage(msg);
        } catch (e) {
          console.error('Failed to parse WebSocket message', e);
        }
      };

      socket.onerror = (err) => {
        console.warn('WebSocket encountered error, falling back to simulated stream...', err);
        startSimulation();
      };

      socket.onclose = () => {
        setIsConnected(false);
        console.log('WebSocket closed, starting simulation...');
        startSimulation();
      };
    } catch (err) {
      console.warn('Unable to initialize WebSocket connection, starting simulation...', err);
      startSimulation();
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      stopSimulation();
    };
  }, []);

  const handleWebSocketMessage = (msg: WebSocketMessage) => {
    switch (msg.type) {
      case 'call_start':
        setCallState((prev) => ({
          ...prev,
          activeCall: msg.payload,
          liveTranscript: '',
          currentNode: 'GREETING',
        }));
        break;
      case 'call_update':
        setCallState((prev) => ({
          ...prev,
          activeCall: { ...prev.activeCall, ...msg.payload },
        }));
        break;
      case 'call_end':
        setCallState((prev) => ({
          ...prev,
          activeCall: null,
        }));
        break;
      case 'transcript_chunk':
        setCallState((prev) => ({
          ...prev,
          liveTranscript: prev.liveTranscript + msg.payload.text,
        }));
        break;
      case 'waveform_pulse':
        setCallState((prev) => ({
          ...prev,
          waveform: msg.payload.waveform,
        }));
        break;
      case 'node_change':
        setCallState((prev) => ({
          ...prev,
          currentNode: msg.payload.node,
        }));
        break;
      case 'sentiment_change':
        setCallState((prev) => ({
          ...prev,
          sentiment: msg.payload.sentiment,
          sentimentScore: msg.payload.score,
        }));
        break;
    }
  };

  // ── Simulated Live Call Generator ──────────────────────────
  const startSimulation = () => {
    setIsConnected(true); // Treat as connected in mock mode
    dialogueIndexRef.current = 0;

    // Create a mock active session
    const mockCall: VoiceSession = {
      id: 'live-sim-call',
      callerId: 'pat-4',
      callerName: 'Zoya Patel (Father: Rohan)',
      callerEmail: 'zoya.patel@example.com',
      agentId: 'voice-agent-primary',
      agentName: 'CareVoice AI Primary',
      type: 'inbound',
      status: 'active',
      intent: 'Book Pediatrician Appointment',
      duration: 0,
      startedAt: new Date().toISOString(),
      sentiment: 'neutral',
      aiConfidence: 0.96,
      department: 'Pediatrics',
    };

    setCallState({
      activeCall: mockCall,
      currentNode: 'GREETING',
      waveform: Array(30).fill(10),
      liveTranscript: DIALOGUE_FLOW[0].text,
      sentiment: 'neutral',
      sentimentScore: 50,
    });

    let elapsedSeconds = 0;

    simIntervalRef.current = setInterval(() => {
      elapsedSeconds += 1;

      // 1. Update duration
      setCallState((prev) => {
        if (!prev.activeCall) return prev;
        return {
          ...prev,
          activeCall: {
            ...prev.activeCall,
            duration: elapsedSeconds,
          },
        };
      });

      // 2. Generate dancing audio waveform
      setCallState((prev) => {
        const isAISpeaking = prev.liveTranscript.trim().endsWith('?') || prev.liveTranscript.includes('AI:');
        const count = 35;
        const newWave = Array.from({ length: count }, () => {
          // If active voice, generate beautiful amplitudes, else background hum
          const base = isAISpeaking ? 25 : 8;
          const variance = isAISpeaking ? 65 : 12;
          return Math.floor(Math.random() * variance) + base;
        });
        return { ...prev, waveform: newWave };
      });

      // 3. Dialogue flow typewriter stream
      if (elapsedSeconds % 6 === 0) {
        dialogueIndexRef.current += 1;
        if (dialogueIndexRef.current >= DIALOGUE_FLOW.length) {
          // Loop dialogue flow back to greeting with a new ID
          dialogueIndexRef.current = 0;
          elapsedSeconds = 0;
          setCallState((prev) => ({
            ...prev,
            activeCall: {
              ...prev.activeCall!,
              id: `live-sim-call-${Date.now()}`,
              duration: 0,
            },
            liveTranscript: DIALOGUE_FLOW[0].text,
            currentNode: 'GREETING',
            sentiment: 'neutral',
            sentimentScore: 50,
          }));
        } else {
          const currentLine = DIALOGUE_FLOW[dialogueIndexRef.current];
          setCallState((prev) => ({
            ...prev,
            currentNode: currentLine.node,
            sentiment: currentLine.sentiment,
            sentimentScore: currentLine.score,
            liveTranscript: prev.liveTranscript + '\n' + currentLine.text,
          }));
        }
      }
    }, 1000);
  };

  const stopSimulation = () => {
    if (simIntervalRef.current) {
      clearInterval(simIntervalRef.current);
    }
  };

  return {
    isConnected,
    ...callState,
  };
}
