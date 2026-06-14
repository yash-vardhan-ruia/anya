'use client';

import { useState } from 'react';

type Message = {
  role: 'user' | 'assistant';
  text: string;
};

export default function VoiceAgentPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [input, setInput] = useState('');

  const API_URL =
    process.env.NEXT_PUBLIC_API_URL ||
    'http://localhost:8000/api/v1';

  const sendMessage = async (message: string) => {
    if (!message.trim()) return;

    try {
      setIsLoading(true);

      setMessages((prev) => [
        ...prev,
        {
          role: 'user',
          text: message,
        },
      ]);

      setInput('');

      const response = await fetch(
        `${API_URL}/voice-chat/message`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            session_id: sessionId,
            message,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('API Error');
      }

      const data = await response.json();

      setSessionId(data.session_id);

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: data.reply,
        },
      ]);
    } catch (error) {
      console.error(error);

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text:
            'Sorry, I could not connect to the hospital server.',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 p-6">
      <div className="mx-auto max-w-4xl">
        <h1 className="text-3xl font-bold mb-6">
          CareVoice Chat Test
        </h1>

        <div className="bg-white rounded-xl shadow h-[600px] overflow-y-auto p-4 mb-4">
          {messages.length === 0 && (
            <div className="text-center text-slate-500 mt-20">
              Start chatting with Anya
            </div>
          )}

          <div className="space-y-4">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`flex ${
                  msg.role === 'user'
                    ? 'justify-end'
                    : 'justify-start'
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-xl px-4 py-3 ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-200 text-black'
                  }`}
                >
                  <div className="text-xs font-bold mb-1">
                    {msg.role === 'user'
                      ? 'You'
                      : 'Anya'}
                  </div>

                  <div>{msg.text}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow p-4">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              placeholder="Type your message..."
              onChange={(e) =>
                setInput(e.target.value)
              }
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  sendMessage(input);
                }
              }}
              className="flex-1 border rounded-lg px-4 py-2"
            />

            <button
              onClick={() => sendMessage(input)}
              disabled={isLoading}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg"
            >
              {isLoading ? 'Sending...' : 'Send'}
            </button>

            <button
              onClick={() => {
                setMessages([]);
                setSessionId(null);
              }}
              className="bg-gray-600 text-white px-6 py-2 rounded-lg"
            >
              Reset
            </button>
          </div>

          {sessionId && (
            <p className="text-xs text-slate-500 mt-3">
              Session: {sessionId}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}