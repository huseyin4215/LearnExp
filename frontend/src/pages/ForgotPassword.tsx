import React, { useState } from 'react';
import { Link } from 'react-router-dom';

const ForgotPassword: React.FC = () => {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsLoading(true);
    setError('');
    try {
      await new Promise((resolve) => setTimeout(resolve, 1200));
      setSent(true);
    } catch {
      setError('Bir hata oluştu. Lütfen tekrar deneyin.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--page-bg)]">
      <div className="grid min-h-screen lg:grid-cols-2">
        <section className="relative hidden overflow-hidden lg:flex">
          <div className="absolute inset-0 bg-[linear-gradient(135deg,#091221,#11243b_55%,#16335b)]" />
          <div className="absolute left-20 top-20 h-72 w-72 rounded-full bg-blue-500/18 blur-3xl" />
          <div className="absolute bottom-16 right-20 h-80 w-80 rounded-full bg-cyan-400/12 blur-3xl" />

          <div className="relative z-10 flex w-full flex-col justify-between p-12 text-white">
            <div>
              <p className="eyebrow text-white/70">Hesap kurtarma</p>
              <h1 className="mt-6 font-heading text-6xl leading-tight">Şifreni sıfırla ve araştırma alanına geri dön.</h1>
              <p className="mt-5 max-w-xl text-base leading-8 text-white/72">
                Şifre yenileme akışı da ürünün geri kalanı gibi güven veren, sade ama güçlü görünmeli.
              </p>
            </div>
          </div>
        </section>

        <section className="flex items-center justify-center p-8">
          <div className="w-full max-w-md">
            <div className="rounded-[30px] border border-[var(--line-soft)] bg-[var(--surface)] p-8 shadow-[var(--shadow-lg)]">
              {sent ? (
                <div className="space-y-5 text-center">
                  <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-[rgba(31,143,88,0.08)] text-[var(--success)]">
                    <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <p className="eyebrow mb-2">Bağlantı gönderildi</p>
                    <h2 className="font-heading text-4xl text-[var(--text-strong)]">E-postanı kontrol et</h2>
                    <p className="mt-2 text-sm text-[var(--text-muted)]">{email} adresine bir sıfırlama bağlantısı hazırlandı.</p>
                  </div>
                  <Link to="/login" className="btn-primary">
                    Giriş ekranına dön
                  </Link>
                </div>
              ) : (
                <>
                  <div className="mb-8 text-center">
                    <p className="eyebrow mb-2">Şifre sıfırla</p>
                    <h2 className="font-heading text-4xl text-[var(--text-strong)]">Şifreni yenile</h2>
                    <p className="mt-2 text-sm text-[var(--text-muted)]">E-posta adresini gir, sana sıfırlama bağlantısı gönderelim.</p>
                  </div>

                  <form onSubmit={handleSubmit} className="space-y-5">
                    {error && <div className="rounded-[18px] border border-[rgba(198,69,69,0.2)] bg-[rgba(198,69,69,0.08)] px-4 py-3 text-sm text-[var(--danger)]">{error}</div>}

                    <div>
                      <label htmlFor="email" className="mb-2 block text-sm font-semibold text-[var(--text-strong)]">E-posta adresi</label>
                      <input
                        id="email"
                        type="email"
                        value={email}
                        onChange={(event) => setEmail(event.target.value)}
                        className="w-full rounded-[18px] border border-[var(--line)] bg-[var(--surface-alt)] px-4 py-3 text-sm text-[var(--text-primary)]"
                        placeholder="ornek@universite.edu.tr"
                        required
                      />
                    </div>

                    <button type="submit" disabled={isLoading} className="btn-primary w-full justify-center disabled:cursor-not-allowed disabled:opacity-60">
                      {isLoading ? 'Bağlantı hazırlanıyor...' : 'Sıfırlama bağlantısı gönder'}
                    </button>
                  </form>

                  <div className="mt-8 rounded-[22px] border border-[var(--line-soft)] bg-[var(--surface-alt)] p-4">
                    <Link to="/login" className="text-sm font-semibold text-[var(--brand)]">Giriş ekranına dön</Link>
                  </div>
                </>
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default ForgotPassword;
