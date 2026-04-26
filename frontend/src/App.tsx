import React from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import Navbar from './components/Navbar';
import ChatOverlay from './components/ChatOverlay';
import Footer from './components/Footer';
import ProtectedRoute from './components/ProtectedRoute';
import Dashboard from './views/Dashboard';
import SearchDashboard from './views/SearchDashboard';
import MyLibrary from './views/MyLibrary';
import Profile from './views/Profile';
import Settings from './views/Settings';
import News from './views/News';
import Login from './pages/Login';
import Register from './pages/Register';
import CompleteProfile from './pages/CompleteProfile';
import ForgotPassword from './pages/ForgotPassword';
import InfoPage from './views/InfoPage';
import Recommendations from './views/Recommendations';
import { ThemeProvider } from './contexts/ThemeContext';
import { AuthProvider } from './contexts/AuthContext';
import { LanguageProvider } from './contexts/LanguageContext';

const App: React.FC = () => {
  const location = useLocation();
  const isAuthPage = ['/login', '/register', '/complete-profile', '/forgot-password'].includes(location.pathname);

  const privacyPage = (
    <InfoPage
      eyebrow={{ tr: 'Gizlilik', en: 'Privacy' }}
      title={{ tr: 'Veri kullanımı, güvenlik ve hesap gizliliği ilkeleri.', en: 'Data usage, security, and account privacy principles.' }}
      intro={{
        tr: 'LearnExp; hesap bilgileri, kaydedilen içerikler ve arama tercihleri gibi kullanıcı verilerini ürün deneyimini kişiselleştirmek için işler.',
        en: 'LearnExp processes account details, saved items, and search preferences to personalize the product experience.',
      }}
      sections={[
        {
          heading: { tr: 'Hangi verileri tutuyoruz?', en: 'What do we store?' },
          body: {
            tr: 'Hesap bilgileri, kayıtlı içerikler, temel profil tercihleri ve araştırma etkinlikleri ürün deneyimini iyileştirmek için saklanabilir.',
            en: 'Account details, saved content, core profile preferences, and research activity may be stored to improve the product experience.',
          },
        },
        {
          heading: { tr: 'Nasıl kullanıyoruz?', en: 'How do we use it?' },
          body: {
            tr: 'Bu veriler arama sonuçlarını iyileştirmek, öneri akışlarını kişiselleştirmek ve kütüphane deneyimini sürdürmek için kullanılır.',
            en: 'This data is used to improve search results, personalize recommendation feeds, and maintain the library experience.',
          },
        },
      ]}
    />
  );

  const helpPage = (
    <InfoPage
      eyebrow={{ tr: 'Yardım Merkezi', en: 'Help Center' }}
      title={{ tr: 'Arama, kütüphane, öneriler ve hesap ayarları için hızlı yardım.', en: 'Quick help for search, library, recommendations, and account settings.' }}
      intro={{
        tr: 'LearnExp içinde araştırma akışını yönetmek için arama, filtreler, kaydetme ve profil tercihleri bir arada çalışır.',
        en: 'Search, filters, saving, and profile preferences work together inside LearnExp to manage your research flow.',
      }}
      sections={[
        {
          heading: { tr: 'Arama ve filtreleme', en: 'Search and filtering' },
          body: {
            tr: 'Arama sayfasında kaynak seçimi yaptıktan sonra konu, kategori ve tarih aralıklarıyla sonuçları daraltabilirsin.',
            en: 'After selecting sources on the search page, you can narrow results with topics, categories, and date ranges.',
          },
        },
        {
          heading: { tr: 'Kaydetme ve öneriler', en: 'Saving and recommendations' },
          body: {
            tr: 'Kartlardaki yer imi ve beğeni aksiyonları zamanla sana daha alakalı öneriler oluşturulmasına yardımcı olur.',
            en: 'Bookmark and like actions on cards help build more relevant recommendations for you over time.',
          },
        },
      ]}
    />
  );

  const contactPage = (
    <InfoPage
      eyebrow={{ tr: 'İletişim', en: 'Contact' }}
      title={{ tr: 'Ürün geri bildirimi, ortaklık ve destek talepleri için iletişim.', en: 'Get in touch for product feedback, partnerships, and support.' }}
      intro={{
        tr: 'LearnExp ürün deneyimi, içerik kaynakları ve kurumsal kullanım senaryoları için bizimle bağlantı kurabilirsin.',
        en: 'You can reach out to us about the LearnExp product experience, content sources, and institutional use cases.',
      }}
      sections={[
        {
          heading: { tr: 'Genel iletişim', en: 'General contact' },
          body: {
            tr: 'Ürün geri bildirimi ve destek için support@learnexp.local adresi üzerinden ekibe ulaşılabilir.',
            en: 'For product feedback and support, the team can be reached at support@learnexp.local.',
          },
        },
        {
          heading: { tr: 'Kurum ve ortaklıklar', en: 'Institutions and partnerships' },
          body: {
            tr: 'Kurumsal entegrasyonlar ve içerik iş birlikleri için partnerships@learnexp.local üzerinden iletişime geçebilirsin.',
            en: 'For institutional integrations and content partnerships, contact partnerships@learnexp.local.',
          },
        },
      ]}
    />
  );

  const accessibilityPage = (
    <InfoPage
      eyebrow={{ tr: 'Erişilebilirlik', en: 'Accessibility' }}
      title={{ tr: 'Daha okunabilir, daha odaklı ve daha kapsayıcı araştırma deneyimi.', en: 'A more readable, focused, and inclusive research experience.' }}
      intro={{
        tr: 'LearnExp; kontrast, klavye erişimi, odak durumları ve azaltılmış hareket gibi erişilebilirlik ilkelerini gözeterek tasarlanır.',
        en: 'LearnExp is designed with accessibility principles such as contrast, keyboard access, focus states, and reduced motion in mind.',
      }}
      sections={[
        {
          heading: { tr: 'Arayüz ilkeleri', en: 'Interface principles' },
          body: {
            tr: 'Büyük başlık hiyerarşileri, net buton sınırları ve semantik yapı sayesinde kritik araştırma içerikleri daha rahat taranır.',
            en: 'Large heading hierarchies, clear button boundaries, and semantic structure make critical research content easier to scan.',
          },
        },
        {
          heading: { tr: 'Sürekli iyileştirme', en: 'Continuous improvement' },
          body: {
            tr: 'Yeni ekranlar ve bileşenler eklenirken kontrast, dokunma alanı ve odak görünürlüğü düzenli olarak gözden geçirilir.',
            en: 'As new screens and components are added, contrast, touch targets, and focus visibility are reviewed regularly.',
          },
        },
      ]}
    />
  );

  if (isAuthPage) {
    return (
      <AuthProvider>
        <LanguageProvider>
          <ThemeProvider>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/complete-profile" element={<CompleteProfile />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
            </Routes>
          </ThemeProvider>
        </LanguageProvider>
      </AuthProvider>
    );
  }

  return (
    <AuthProvider>
      <LanguageProvider>
        <ThemeProvider>
          <div className="min-h-screen flex flex-col bg-[var(--page-bg)] text-[var(--text-primary)] transition-colors">
            <Navbar />
            <main className="flex-1 w-full py-8">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/search" element={<ProtectedRoute><SearchDashboard /></ProtectedRoute>} />
                <Route path="/library" element={<ProtectedRoute><MyLibrary /></ProtectedRoute>} />
                <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
                <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
                <Route path="/recommendations" element={<ProtectedRoute><Recommendations /></ProtectedRoute>} />
                <Route path="/news" element={<News />} />
                <Route path="/privacy" element={privacyPage} />
                <Route path="/help" element={helpPage} />
                <Route path="/contact" element={contactPage} />
                <Route path="/accessibility" element={accessibilityPage} />
              </Routes>
            </main>
            <Footer />
            <ChatOverlay />
          </div>
        </ThemeProvider>
      </LanguageProvider>
    </AuthProvider>
  );
};

export default App;
