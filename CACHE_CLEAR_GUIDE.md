# 🔧 Tarayıcı Cache Temizleme - Kesin Çözüm

## Sorun
Tarayıcı eski `api.ts` dosyasını cache'lemiş. Export'lar düzeltildi ama tarayıcı eski versiyonu kullanıyor.

---

## ✅ Çözüm 1: Hard Refresh (En Hızlı)

1. Tarayıcıda `http://localhost:5173` sayfasındayken
2. **Ctrl + Shift + R** (Windows/Linux)
3. Veya **Ctrl + F5**
4. Veya **Shift + F5**

---

## ✅ Çözüm 2: DevTools ile Cache Temizleme

1. **F12** tuşuna basın (DevTools açılır)
2. **Network** sekmesine gidin
3. **Disable cache** kutucuğunu işaretleyin
4. Sayfayı yenileyin (**F5**)
5. Hata gittiyse **Disable cache** işaretini kaldırabilirsiniz

---

## ✅ Çözüm 3: Tarayıcı Cache'ini Tamamen Temizle

### Chrome/Edge:
1. **Ctrl + Shift + Delete**
2. **Time range**: "All time" seçin
3. **Cached images and files** işaretleyin
4. **Clear data** tıklayın
5. Tarayıcıyı kapatıp yeniden açın

### Firefox:
1. **Ctrl + Shift + Delete**
2. **Time range to clear**: "Everything" seçin
3. **Cache** işaretleyin
4. **Clear Now** tıklayın
5. Tarayıcıyı kapatıp yeniden açın

---

## ✅ Çözüm 4: Vite Cache Temizleme

Terminal'de:

```bash
cd frontend

# Vite cache'i temizle
rmdir /s /q .vite
rmdir /s /q node_modules\.vite

# Dev server'ı yeniden başlat
npm run dev
```

Sonra tarayıcıda **Ctrl + Shift + R**

---

## ✅ Çözüm 5: Tam Reset (Kesin Çözüm)

```bash
cd frontend

# Tüm cache'leri temizle
rmdir /s /q .vite
rmdir /s /q dist
rmdir /s /q node_modules

# Yeniden yükle
npm install

# Başlat
npm run dev
```

Sonra:
1. Tarayıcıyı **tamamen kapat**
2. Yeniden aç
3. `http://localhost:5173` git
4. **Ctrl + Shift + R**

---

## 🧪 Test

Console'da hata olmamalı. Şunu görmeli:

```
✅ No errors
✅ Dashboard yükleniyor
✅ Search bar çalışıyor
```

---

## 📝 Not

**En hızlı çözüm**: DevTools açık tutup **Disable cache** işaretli bırakın. Development sırasında cache sorunları yaşamazsınız.

---

## 🆘 Hâlâ Çalışmıyorsa

1. Farklı bir tarayıcı deneyin (Chrome → Firefox veya tersi)
2. Incognito/Private mode'da açın
3. Terminal'deki Vite output'unu kontrol edin (hata var mı?)
