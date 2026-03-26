# 🔗 Frontend-Backend API Integration

## ✅ Tamamlanan Özellikler

### 1. Backend API Endpoints

#### Articles API
- **GET `/api/articles/`** - Makale listesi (pagination, filtering, search)
  - Query params:
    - `search` - Başlık, özet, yazar, keyword'lerde arama
    - `categories` - Kategori filtresi (virgülle ayrılmış)
    - `source` - Kaynak filtresi (ID veya isim)
    - `date_from` - Başlangıç tarihi (YYYY-MM-DD)
    - `date_to` - Bitiş tarihi (YYYY-MM-DD)
    - `date_range` - Hızlı tarih filtresi (last_30_days, last_3_months, last_year)
    - `page` - Sayfa numarası
    - `page_size` - Sayfa başına sonuç sayısı

- **GET `/api/articles/{id}/`** - Tek makale detayı

- **GET `/api/articles/categories/`** - Tüm kategorileri listele

- **GET `/api/sources/list/`** - API kaynaklarını listele

#### Response Format
```json
{
  "count": 150,
  "next": "?page=2",
  "previous": null,
  "total_pages": 8,
  "current_page": 1,
  "page_size": 20,
  "results": [
    {
      "id": 1,
      "external_id": "arxiv:2401.12345",
      "title": "Article Title",
      "abstract": "Abstract text...",
      "authors": [
        {"name": "John Doe", "orcid": "0000-0001-2345-6789"}
      ],
      "published_date": "2024-01-15",
      "journal": "Nature",
      "url": "https://...",
      "pdf_url": "https://...",
      "doi": "10.1234/example",
      "categories": ["Machine Learning", "AI"],
      "keywords": ["neural networks", "deep learning"],
      "citation_count": 42,
      "api_source": {
        "id": 1,
        "name": "arXiv"
      },
      "fetched_at": "2024-02-12T10:30:00Z"
    }
  ]
}
```

---

### 2. Frontend Services

#### `services/api.ts`

**New Interfaces:**
```typescript
interface Article {
  id: number;
  external_id: string;
  title: string;
  abstract: string;
  authors: Array<{ name: string; orcid?: string }>;
  published_date: string | null;
  journal: string;
  url: string;
  pdf_url: string;
  doi: string | null;
  categories: string[];
  keywords: string[];
  citation_count: number;
  api_source: { id: number; name: string } | null;
  fetched_at: string;
}

interface SearchParams {
  search?: string;
  categories?: string;
  source?: string;
  date_from?: string;
  date_to?: string;
  date_range?: string;
  page?: number;
  page_size?: number;
}
```

**New API Methods:**
```typescript
articlesApi.search(params: SearchParams): Promise<ArticlesResponse>
articlesApi.getById(id: number): Promise<Article>
articlesApi.getSources(): Promise<APISource[]>
articlesApi.getCategories(): Promise<string[]>
```

---

### 3. Dashboard Integration

**Features:**
- ✅ Gerçek API'den makale çekme
- ✅ Arama fonksiyonu (search bar)
- ✅ Loading state
- ✅ Empty state
- ✅ Toplam makale sayısı gösterimi
- ✅ Article card'ları dinamik render

**Usage:**
```typescript
const [articles, setArticles] = useState<Article[]>([]);
const [searchQuery, setSearchQuery] = useState('');

const fetchArticles = async (search: string = '') => {
  const response = await articlesApi.search({ search, page_size: 10 });
  setArticles(response.results);
};

// Search on submit
const handleSearch = (e: React.FormEvent) => {
  e.preventDefault();
  fetchArticles(searchQuery);
};
```

---

### 4. Search Dashboard Integration

**Features:**
- ✅ Gelişmiş arama
- ✅ Kategori filtreleme (checkbox)
- ✅ Kaynak filtreleme (checkbox)
- ✅ Tarih aralığı filtreleme (dropdown)
- ✅ Pagination (Previous/Next)
- ✅ Dinamik kategori ve kaynak listesi
- ✅ Gerçek zamanlı filtreleme
- ✅ Sonuç sayısı gösterimi
- ✅ "Live Data" badge

**State Management:**
```typescript
const [articles, setArticles] = useState<Article[]>([]);
const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
const [selectedSources, setSelectedSources] = useState<string[]>([]);
const [dateRange, setDateRange] = useState('');
const [currentPage, setCurrentPage] = useState(1);
```

**Auto-fetch on filter change:**
```typescript
useEffect(() => {
  fetchArticles();
}, [selectedCategories, selectedSources, dateRange, currentPage]);
```

---

## 🚀 Kullanım Örnekleri

### 1. Basit Arama
```typescript
// Dashboard'da arama
const response = await articlesApi.search({
  search: 'machine learning',
  page_size: 10
});
```

### 2. Kategori Filtresi
```typescript
const response = await articlesApi.search({
  categories: 'Artificial Intelligence,Machine Learning',
  page_size: 20
});
```

### 3. Kaynak Filtresi
```typescript
const response = await articlesApi.search({
  source: 'arXiv',
  page_size: 15
});
```

### 4. Tarih Aralığı
```typescript
const response = await articlesApi.search({
  date_range: 'last_30_days',
  page_size: 20
});
```

### 5. Kombine Filtreler
```typescript
const response = await articlesApi.search({
  search: 'quantum computing',
  categories: 'Physics,Computer Science',
  source: 'arXiv',
  date_range: 'last_3_months',
  page: 1,
  page_size: 12
});
```

---

## 📊 UI Components

### Article Card Mapping
```typescript
// API article'ı ContentCard'a dönüştürme
<ContentCard 
  content={{
    id: article.id.toString(),
    type: 'article',
    title: article.title,
    description: article.abstract,
    authors: article.authors.map(a => a.name).join(', '),
    date: article.published_date || article.fetched_at,
    journal: article.journal,
    citations: article.citation_count,
    tags: article.categories.slice(0, 3),
    url: article.url,
    pdfUrl: article.pdf_url,
  }} 
  isSaved={savedIds.has(article.id.toString())} 
  onToggleSave={() => toggleSave(article.id.toString())} 
/>
```

### Loading State
```typescript
{loading ? (
  <div className="text-center py-12">
    <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
    <p className="mt-4 text-gray-600">Loading articles...</p>
  </div>
) : (
  // Articles list
)}
```

### Empty State
```typescript
{articles.length === 0 && (
  <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
    <svg className="w-16 h-16 mx-auto text-gray-400 mb-4">...</svg>
    <h3 className="text-xl font-semibold text-gray-800 mb-2">No articles found</h3>
    <p className="text-gray-600">Try adjusting your search query</p>
  </div>
)}
```

### Pagination
```typescript
<div className="mt-8 flex justify-center gap-2">
  <button
    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
    disabled={currentPage === 1}
    className="px-4 py-2 border rounded-lg disabled:opacity-50"
  >
    Previous
  </button>
  <span className="px-4 py-2">Page {currentPage} of {totalPages}</span>
  <button
    onClick={() => setCurrentPage(p => p + 1)}
    disabled={currentPage >= totalPages}
    className="px-4 py-2 border rounded-lg disabled:opacity-50"
  >
    Next
  </button>
</div>
```

---

## 🧪 Test Etme

### 1. Backend Test
```bash
# Django server çalıştır
cd backend
.\venv\Scripts\python.exe manage.py runserver

# Test endpoints
curl http://localhost:8000/api/articles/
curl http://localhost:8000/api/articles/?search=machine+learning
curl http://localhost:8000/api/articles/categories/
curl http://localhost:8000/api/sources/list/
```

### 2. Frontend Test
```bash
# Frontend server çalıştır
cd frontend
npm run dev

# Test pages
http://localhost:5173/          # Dashboard (search bar çalışıyor)
http://localhost:5173/search    # Search page (filters çalışıyor)
```

---

## 🎯 Özellikler

### Dashboard
- ✅ Search bar çalışıyor
- ✅ Gerçek API verisi gösteriliyor
- ✅ Loading state
- ✅ Empty state
- ✅ Toplam makale sayısı

### Search Page
- ✅ Gelişmiş arama
- ✅ Kategori filtreleri (dinamik)
- ✅ Kaynak filtreleri (dinamik)
- ✅ Tarih aralığı filtresi
- ✅ Pagination
- ✅ Sonuç sayısı
- ✅ "Live Data" badge
- ✅ Clear filters butonu

---

## 🔧 Yapılandırma

### CORS (Backend)
```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",
]
```

### API Base URL (Frontend)
```typescript
// services/api.ts
const API_BASE_URL = 'http://127.0.0.1:8000/api';
```

---

## 📝 Notlar

1. **Veri Yoksa**: Admin panelinden API source ekleyip fetch yapın
   ```bash
   python manage.py fetch_articles --all
   ```

2. **CORS Hatası**: Backend CORS ayarlarını kontrol edin

3. **404 Hatası**: URL'lerin doğru olduğundan emin olun

4. **Empty Results**: Veritabanında veri olduğundan emin olun

---

## 🎉 Sonuç

✅ **Frontend tamamen API'ye bağlandı**  
✅ **Arama çalışıyor**  
✅ **Filtreler çalışıyor**  
✅ **Pagination çalışıyor**  
✅ **Gerçek veri gösteriliyor**  

**Artık sistem production-ready! 🚀**
