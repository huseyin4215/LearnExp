import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { authApi } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const location = useLocation();
  const auth = useAuth();
  const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname || '/';

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const response = await authApi.login({ email, password });
      if (response.success && response.user) {
        auth.login(response.user);
        if (!response.user.isProfileComplete) navigate('/complete-profile');
        else navigate(from, { replace: true });
      } else {
        setError(response.message || 'Giriş başarısız.');
      }
    } catch {
      setError('Sunucuya bağlanılamadı.');
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
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(255,255,255,0.08),transparent_20%)]" />

          <div className="relative z-10 flex w-full flex-col justify-between p-12 text-white">
            <div>
              <p className="eyebrow text-white/70">LearnExp</p>
              <h1 className="mt-6 font-heading text-6xl leading-tight">Akademik keşif için güvenilir giriş deneyimi.</h1>
              <p className="mt-5 max-w-xl text-base leading-8 text-white/72">
                Yayınlar, konferanslar, etkinlikler, duyurular ve kişisel araştırma kütüphanen tek bir ekranda seni bekliyor.
              </p>
            </div>

            <div className="grid gap-4">
              {[
                'Canlı akademik arama',
                'Konferans ve son tarih takibi',
                'Kaydet, geri dön, karşılaştır',
              ].map((item) => (
                <div key={item} className="rounded-[26px] border border-white/10 bg-white/6 p-5 backdrop-blur-md">
                  <p className="text-sm font-semibold">{item}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="flex items-center justify-center p-8">
          <div className="w-full max-w-md">
            <div className="mb-8 text-center lg:hidden">
              <h1 className="font-heading text-4xl text-[var(--text-strong)]">LearnExp</h1>
              <p className="mt-2 text-sm text-[var(--text-muted)]">Akıllı Akademik Keşif</p>
            </div>

            <div className="rounded-[30px] border border-[var(--line-soft)] bg-[var(--surface)] p-8 shadow-[var(--shadow-lg)]">
              <div className="mb-8 text-center">
                <p className="eyebrow mb-2">Giriş yap</p>
                <h2 className="font-heading text-4xl text-[var(--text-strong)]">Tekrar hoş geldin</h2>
                <p className="mt-2 text-sm text-[var(--text-muted)]">Araştırma alanına erişmek için hesabına giriş yap.</p>
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

                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <label htmlFor="password" className="block text-sm font-semibold text-[var(--text-strong)]">Şifre</label>
                    <Link to="/forgot-password" className="text-sm font-semibold text-[var(--brand)]">Şifremi unuttum</Link>
                  </div>
                  <div className="relative">
                    <input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                      className="w-full rounded-[18px] border border-[var(--line)] bg-[var(--surface-alt)] px-4 py-3 pr-14 text-sm text-[var(--text-primary)]"
                      placeholder="Şifrenizi girin"
                      required
                    />
                    <button type="button" onClick={() => setShowPassword((value) => !value)} className="absolute right-4 top-1/2 -translate-y-1/2 text-xs font-semibold text-[var(--text-muted)]">
                      {showPassword ? 'Gizle' : 'Göster'}
                    </button>
                  </div>
                </div>

                <label className="flex items-center gap-3 text-sm text-[var(--text-muted)]">
                  <input type="checkbox" checked={rememberMe} onChange={(event) => setRememberMe(event.target.checked)} />
                  Beni hatırla
                </label>

                <button type="submit" disabled={isLoading} className="btn-primary w-full justify-center disabled:cursor-not-allowed disabled:opacity-60">
                  {isLoading ? 'Giriş yapılıyor...' : 'Giriş yap'}
                </button>
              </form>

              <p className="mt-8 text-center text-sm text-[var(--text-muted)]">
                Hesabın yok mu?{' '}
                <Link to="/register" className="font-semibold text-[var(--brand)]">
                  Kayıt ol
                </Link>
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Login;
