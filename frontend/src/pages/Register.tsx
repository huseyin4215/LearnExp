import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authApi, userStorage } from '../services/api';

const Register: React.FC = () => {
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [agreeTerms, setAgreeTerms] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [event.target.name]: event.target.value });
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError('');
    setSuccess('');

    if (formData.password !== formData.confirmPassword) {
      setError('Şifreler eşleşmiyor.');
      return;
    }

    if (formData.password.length < 6) {
      setError('Şifre en az 6 karakter olmalı.');
      return;
    }

    setIsLoading(true);
    try {
      const response = await authApi.register({
        fullName: formData.fullName,
        email: formData.email,
        password: formData.password,
      });

      if (response.success && response.user) {
        userStorage.setUser(response.user);
        setSuccess('Hesap oluşturuldu. Profil adımına yönlendiriliyorsunuz.');
        setTimeout(() => navigate('/complete-profile'), 1200);
      } else {
        setError(response.message || 'Kayıt oluşturulamadı.');
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
        <section className="flex items-center justify-center p-8">
          <div className="w-full max-w-md">
            <div className="mb-8 text-center lg:hidden">
              <h1 className="font-heading text-4xl text-[var(--text-strong)]">LearnExp</h1>
              <p className="mt-2 text-sm text-[var(--text-muted)]">Akıllı Akademik Keşif</p>
            </div>

            <div className="rounded-[30px] border border-[var(--line-soft)] bg-[var(--surface)] p-8 shadow-[var(--shadow-lg)]">
              <div className="mb-8 text-center">
                <p className="eyebrow mb-2">Kayıt ol</p>
                <h1 className="font-heading text-4xl text-[var(--text-strong)]">Yeni bir hesap oluştur</h1>
                <p className="mt-2 text-sm text-[var(--text-muted)]">Yayınları, konferansları ve kişisel keşif alanını birlikte kur.</p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-5">
                {error && <div className="rounded-[18px] border border-[rgba(198,69,69,0.2)] bg-[rgba(198,69,69,0.08)] px-4 py-3 text-sm text-[var(--danger)]">{error}</div>}
                {success && <div className="rounded-[18px] border border-[rgba(31,143,88,0.2)] bg-[rgba(31,143,88,0.08)] px-4 py-3 text-sm text-[var(--success)]">{success}</div>}

                <div>
                  <label htmlFor="fullName" className="mb-2 block text-sm font-semibold text-[var(--text-strong)]">Ad soyad</label>
                  <input id="fullName" name="fullName" type="text" value={formData.fullName} onChange={handleChange} className="w-full rounded-[18px] border border-[var(--line)] bg-[var(--surface-alt)] px-4 py-3 text-sm text-[var(--text-primary)]" placeholder="Adınız Soyadınız" required />
                </div>

                <div>
                  <label htmlFor="email" className="mb-2 block text-sm font-semibold text-[var(--text-strong)]">E-posta adresi</label>
                  <input id="email" name="email" type="email" value={formData.email} onChange={handleChange} className="w-full rounded-[18px] border border-[var(--line)] bg-[var(--surface-alt)] px-4 py-3 text-sm text-[var(--text-primary)]" placeholder="ornek@universite.edu.tr" required />
                </div>

                <div className="grid gap-5 md:grid-cols-2">
                  <div>
                    <label htmlFor="password" className="mb-2 block text-sm font-semibold text-[var(--text-strong)]">Şifre</label>
                    <input id="password" name="password" type="password" value={formData.password} onChange={handleChange} className="w-full rounded-[18px] border border-[var(--line)] bg-[var(--surface-alt)] px-4 py-3 text-sm text-[var(--text-primary)]" placeholder="Şifre oluştur" required />
                  </div>
                  <div>
                    <label htmlFor="confirmPassword" className="mb-2 block text-sm font-semibold text-[var(--text-strong)]">Şifre tekrar</label>
                    <input id="confirmPassword" name="confirmPassword" type="password" value={formData.confirmPassword} onChange={handleChange} className="w-full rounded-[18px] border border-[var(--line)] bg-[var(--surface-alt)] px-4 py-3 text-sm text-[var(--text-primary)]" placeholder="Tekrar yaz" required />
                  </div>
                </div>

                <label className="flex items-start gap-3 rounded-[18px] border border-[var(--line-soft)] bg-[var(--surface-alt)] px-4 py-3 text-sm text-[var(--text-muted)]">
                  <input type="checkbox" checked={agreeTerms} onChange={(event) => setAgreeTerms(event.target.checked)} className="mt-1" required />
                  <span>LearnExp kullanım koşulları ve gizlilik ilkelerini kabul ediyorum.</span>
                </label>

                <button type="submit" disabled={isLoading || !agreeTerms} className="btn-primary w-full justify-center disabled:cursor-not-allowed disabled:opacity-60">
                  {isLoading ? 'Hesap oluşturuluyor...' : 'Kayıt ol'}
                </button>
              </form>

              <p className="mt-8 text-center text-sm text-[var(--text-muted)]">
                Zaten hesabın var mı?{' '}
                <Link to="/login" className="font-semibold text-[var(--brand)]">
                  Giriş yap
                </Link>
              </p>
            </div>
          </div>
        </section>

        <section className="relative hidden overflow-hidden lg:flex">
          <div className="absolute inset-0 bg-[linear-gradient(135deg,#091221,#10223a_55%,#183e6f)]" />
          <div className="absolute left-20 top-24 h-72 w-72 rounded-full bg-indigo-500/18 blur-3xl" />
          <div className="absolute bottom-16 right-16 h-80 w-80 rounded-full bg-sky-400/12 blur-3xl" />

          <div className="relative z-10 flex w-full flex-col justify-between p-12 text-white">
            <div>
              <p className="eyebrow text-white/70">Akademik başlangıç</p>
              <h2 className="mt-6 font-heading text-6xl leading-tight">Kendi araştırma alanını ilk günden kur.</h2>
              <p className="mt-5 max-w-xl text-base leading-8 text-white/72">
                LearnExp; yayın takibi, konferans izlemesi, konu bazlı keşif ve kişisel araştırma kütüphanesi için tasarlandı.
              </p>
            </div>

            <div className="grid gap-4">
              {[
                'Makale ve etkinlikleri kaydet',
                'Konuları ve son tarihleri izle',
                'Profil tabanlı önerilere hazırlan',
              ].map((item) => (
                <div key={item} className="rounded-[26px] border border-white/10 bg-white/6 p-5 backdrop-blur-md">
                  <p className="text-sm font-semibold">{item}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Register;
