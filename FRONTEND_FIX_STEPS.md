# 🔧 Frontend Export Hatası - Çözüm Adımları

## Hata
```
Uncaught SyntaxError: The requested module '/src/services/api.ts' does not provide an export named 'Article'
```

## ✅ Çözüm Adımları

### 1. Tarayıcıyı Tamamen Kapat
- Tüm sekmeleri kapat
- Tarayıcıyı tamamen kapat (Ctrl+Shift+Q veya Alt+F4)

### 2. Vite Dev Server'ı Yeniden Başlat

```bash
# Terminal'de Ctrl+C ile mevcut server'ı durdur
# Sonra yeniden başlat:

cd frontend
npm run dev
```

### 3. Tarayıcıyı Aç ve Cache'i Temizle

- Tarayıcıyı aç
- `http://localhost:5173` adresine git
- **Ctrl+Shift+R** (Hard Reload) veya **Ctrl+F5** yap
- Veya: F12 (DevTools) → Network tab → "Disable cache" işaretle

### 4. Hâlâ Hata Varsa

```bash
# Frontend klasöründe:
cd frontend

# node_modules ve .vite cache'i temizle
rm -rf node_modules
rm -rf .vite
rm -rf dist

# Yeniden yükle
npm install

# Başlat
npm run dev
```

---

## 🔍 Yapılan Değişiklikler

`frontend/src/services/api.ts` dosyasında tüm interface'ler export edildi:

```typescript
export interface Article { ... }
export interface ArticlesResponse { ... }
export interface SearchParams { ... }
export interface APISource { ... }
export interface User { ... }
export interface ApiResponse { ... }
```

---

## ✅ Test

Tarayıcı console'unda hata olmamalı ve şunları görmeli:

- Dashboard sayfası yükleniyor
- Search bar çalışıyor
- Makaleler listeleniyor (veya "No articles found" mesajı)

---

## 🚀 Hızlı Çözüm (Tek Komut)

```bash
# Frontend klasöründe:
cd frontend
npm run dev
```

Sonra tarayıcıda **Ctrl+Shift+R** (Hard Reload)

---

## 📝 Not

Vite dev server TypeScript değişikliklerini otomatik algılar ama bazen cache sorunu yaşanabilir. Hard reload genellikle çözüm olur.
