import { useEffect, useRef, useState } from 'react';
import type { ChatMessage } from '../types';

const starterPrompts = [
  'Multimodal öğrenme makalelerini bul',
  'Yaklaşan yapay zeka konferanslarını göster',
  'Robotik için son tarihleri takip et',
  'Son siber güvenlik araştırmalarını özetle',
];

function ChatOverlay() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'model', text: 'Ben LearnExp araştırma yardımcınım. Makale, konferans, etkinlik, çağrı veya konu özeti sorabilirsin.' },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async (value?: string) => {
    const nextText = (value ?? input).trim();
    if (!nextText || isLoading) return;

    setInput('');
    setMessages((prev) => [...prev, { role: 'user', text: nextText }]);
    setIsLoading(true);

    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          role: 'model',
          text: `"${nextText}" için yayınlar, etkinlik zaman akışları ve akademik güncellemeler üzerinden sana yardımcı olabilirim. Sonraki aşamada bu panel gerçek copilot yanıtlarıyla bağlanabilir.`,
        },
      ]);
      setIsLoading(false);
    }, 900);
  };

  return (
    <>
      <div className="fixed bottom-4 right-4 z-30 sm:bottom-5 sm:right-5">
        <button
          onClick={() => setIsOpen((value) => !value)}
          className="flex h-14 w-14 items-center justify-center rounded-full border border-white/10 bg-[linear-gradient(135deg,#14315d,#254f99)] text-white shadow-[0_18px_40px_rgba(16,32,51,0.32)] transition-transform hover:-translate-y-0.5"
          aria-label="Araştırma yardımcısını aç"
        >
          {isOpen ? (
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : (
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          )}
        </button>
      </div>

      <div
        className={`fixed bottom-24 right-5 z-30 flex h-[560px] w-[390px] max-w-[calc(100vw-24px)] flex-col overflow-hidden rounded-[28px] border border-[var(--line-soft)] bg-[var(--surface)] shadow-[var(--shadow-lg)] transition-all duration-300 sm:right-6 ${
          isOpen ? 'pointer-events-auto translate-y-0 opacity-100' : 'pointer-events-none translate-y-6 opacity-0'
        }`}
      >
        <div className="border-b border-[var(--line-soft)] bg-[linear-gradient(135deg,#0d1828,#163056)] px-5 py-5 text-white">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/10">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-white/60">LearnExp AI</p>
              <h3 className="text-base font-semibold">Araştırma Yardımcısı</h3>
            </div>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {starterPrompts.map((prompt) => (
              <button
                key={prompt}
                onClick={() => handleSend(prompt)}
                className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-white/82 transition-colors hover:bg-white/10"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>

        <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto bg-[var(--surface-alt)] p-4">
          {messages.map((message, index) => (
            <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[86%] rounded-3xl px-4 py-3 text-sm leading-relaxed ${
                  message.role === 'user'
                    ? 'rounded-br-md bg-[var(--brand)] text-white'
                    : 'rounded-bl-md border border-[var(--line-soft)] bg-[var(--surface)] text-[var(--text-primary)]'
                }`}
              >
                {message.text}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="rounded-3xl rounded-bl-md border border-[var(--line-soft)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--text-muted)]">
                İsteğini değerlendiriyorum...
              </div>
            </div>
          )}
        </div>

        <div className="border-t border-[var(--line-soft)] bg-[var(--surface)] p-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => event.key === 'Enter' && handleSend()}
              placeholder="Makale, son tarih veya konferans trendi sor..."
              className="flex-1 rounded-2xl border border-[var(--line)] bg-[var(--surface-alt)] px-4 py-3 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-soft)]"
            />
            <button onClick={() => handleSend()} className="btn-primary px-4">
              Gönder
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

export default ChatOverlay;
