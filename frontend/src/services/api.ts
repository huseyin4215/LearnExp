const API_BASE_URL = 'http://127.0.0.1:8000/api';

export interface ApiResponse<T = unknown> {
  success: boolean;
  message: string;
  user?: T;
}

export interface User {
  id: number;
  email: string;
  fullName: string;
  isStaff?: boolean;
  isProfileComplete?: boolean;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface RegisterData {
  fullName: string;
  email: string;
  password: string;
}

// Article interfaces
export interface Article {
  id: number;
  external_id: string;
  title: string;
  abstract: string;
  authors: Array<{ name: string; orcid?: string; institution?: string }>;
  published_date: string | null;
  journal: string;
  url: string;
  pdf_url: string;
  image_url?: string;
  doi: string | null;
  categories: string[];
  keywords: string[];
  citation_count: number;
  api_source: {
    id: number;
    name: string;
  } | null;
  fetched_at: string;
}

export interface ArticlesResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Article[];
}

export interface SearchParams {
  search?: string;
  categories?: string;
  source?: string;
  date_from?: string;
  date_to?: string;
  date_range?: string;
  page?: number;
  page_size?: number;
}

// Scraped Content interfaces
export interface ScrapedContentItem {
  id: number;
  title: string;
  abstract: string;
  content_type: string;
  authors: Array<{ name: string }> | string[];
  published_date: string | null;
  source_url: string;
  keywords: string[];
  scraper_name?: string;
  image_url?: string;
}

export interface ScrapedContentResponse {
  success: boolean;
  total: number;
  page: number;
  per_page: number;
  contents: ScrapedContentItem[];
}

export interface APISource {
  id: number;
  name: string;
  description: string;
  response_format: string;
  is_active: boolean;
  total_articles_fetched: number;
}

export interface LiveSearchResponse {
  success: boolean;
  query: string;
  total_found: number;
  sources_searched: number;
  articles: Array<{
    title: string;
    abstract: string;
    authors: Array<{ name: string }>;
    published_date: string;
    journal: string;
    url: string;
    pdf_url: string;
    image_url: string;
    doi: string;
    categories: string[];
    keywords: string[];
    citation_count: number;
    source: string;
    external_id: string;
  }>;
  errors?: Array<{ source: string; error: string }>;
  timed_out_sources?: string[];
  partial_results?: boolean;
}

export const authApi = {
  async login(data: LoginData): Promise<ApiResponse<User>> {
    const response = await fetch(`${API_BASE_URL}/auth/login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    return response.json();
  },

  async register(data: RegisterData): Promise<ApiResponse<User>> {
    const response = await fetch(`${API_BASE_URL}/auth/register/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    return response.json();
  },

  async getUser(userId: number): Promise<ApiResponse<User>> {
    const response = await fetch(`${API_BASE_URL}/user/${userId}/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return response.json();
  },
};

// Articles API
export const articlesApi = {
  async search(params: SearchParams = {}): Promise<ArticlesResponse> {
    const queryParams = new URLSearchParams();

    if (params.search) queryParams.append('search', params.search);
    if (params.categories) queryParams.append('categories', params.categories);
    if (params.source) queryParams.append('source', params.source);
    if (params.date_from) queryParams.append('date_from', params.date_from);
    if (params.date_to) queryParams.append('date_to', params.date_to);
    if (params.date_range) queryParams.append('date_range', params.date_range);
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.page_size) queryParams.append('page_size', params.page_size.toString());

    const response = await fetch(`${API_BASE_URL}/articles/?${queryParams.toString()}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch articles');
    }

    return response.json();
  },

  async getById(id: number): Promise<Article> {
    const response = await fetch(`${API_BASE_URL}/articles/${id}/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch article');
    }

    return response.json();
  },

  async getSources(): Promise<APISource[]> {
    const response = await fetch(`${API_BASE_URL}/sources/list/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch sources');
    }

    const data = await response.json();
    return data.results || data;
  },

  async getCategories(): Promise<string[]> {
    const response = await fetch(`${API_BASE_URL}/articles/categories/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      // Return default categories if endpoint doesn't exist
      return [
        'Artificial Intelligence',
        'Machine Learning',
        'Computer Vision',
        'Natural Language Processing',
        'Robotics',
        'Data Science',
        'Quantum Computing',
        'Blockchain',
        'Cybersecurity',
        'Bioinformatics'
      ];
    }

    const data = await response.json();
    return data.categories || data;
  },

  async searchLive(query: string, maxResults: number = 20, sourceIds: number[] = [], scraperIds: number[] = [], userId?: number): Promise<LiveSearchResponse> {
    const response = await fetch(`${API_BASE_URL}/search/live/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        max_results: maxResults,
        source_ids: sourceIds,
        scraper_ids: scraperIds,
        user_id: userId
      }),
    });

    if (!response.ok) {
      throw new Error('Live search failed');
    }

    return response.json();
  },
};

// Scrapers API (Web scraping kaynakları)
export interface ScraperSource {
  id: number;
  name: string;
  source_type: string;
  scraper_type: string;
  is_active: boolean;
  total_items_scraped: number;
}

export const scrapersApi = {
  async list(): Promise<ScraperSource[]> {
    const response = await fetch(`${API_BASE_URL}/scrapers/`);
    if (!response.ok) return [];
    const data = await response.json();
    return data.scrapers || [];
  },
  
  async run(id: number, query?: string): Promise<{success: boolean; message?: string}> {
    const response = await fetch(`${API_BASE_URL}/scrapers/${id}/run/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });
    if (!response.ok) throw new Error('Failed to run scraper');
    return response.json();
  },
};

// Scraped Content API (Haberler / İçerikler)
export const scrapedContentApi = {
  async fetchLatest(page: number = 1, perPage: number = 10, search: string = '', contentType: string = ''): Promise<ScrapedContentResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
    });
    if (search) params.append('search', search);
    if (contentType) params.append('content_type', contentType);

    const response = await fetch(`${API_BASE_URL}/contents/?${params.toString()}`);
    if (!response.ok) throw new Error('Failed to fetch scraped content');
    return response.json();
  },
};

// Library API (Kütüphane)
export interface LibraryItem {
  id: number;
  external_id: string;
  title: string;
  abstract: string;
  authors: Array<{ name: string }>;
  published_date: string;
  journal: string;
  url: string;
  pdf_url: string;
  doi: string;
  source: string;
  categories: string[];
  citation_count: number;
  saved_at: string;
}

export interface LibraryResponse {
  success: boolean;
  total: number;
  page: number;
  total_pages: number;
  items: LibraryItem[];
}

export const libraryApi = {
  async list(userId: number, page: number = 1, pageSize: number = 10, search: string = ''): Promise<LibraryResponse> {
    const params = new URLSearchParams({
      user_id: userId.toString(),
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (search) params.append('search', search);

    const response = await fetch(`${API_BASE_URL}/library/?${params.toString()}`);
    if (!response.ok) throw new Error('Failed to fetch library');
    return response.json();
  },

  async save(userId: number, article: {
    external_id: string;
    title: string;
    abstract: string;
    authors: Array<{ name: string }>;
    published_date: string;
    journal: string;
    url: string;
    pdf_url: string;
    doi: string;
    source: string;
    categories: string[];
    citation_count: number;
  }): Promise<{ success: boolean; message: string; saved_id?: number; already_saved?: boolean }> {
    const response = await fetch(`${API_BASE_URL}/library/save/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, ...article }),
    });
    if (!response.ok) throw new Error('Failed to save article');
    return response.json();
  },

  async remove(userId: number, externalId: string): Promise<{ success: boolean; message: string; removed: boolean }> {
    const response = await fetch(`${API_BASE_URL}/library/remove/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, external_id: externalId }),
    });
    if (!response.ok) throw new Error('Failed to remove article');
    return response.json();
  },

  async check(userId: number, externalIds: string[]): Promise<{ success: boolean; saved_ids: string[] }> {
    const response = await fetch(`${API_BASE_URL}/library/check/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, external_ids: externalIds }),
    });
    if (!response.ok) throw new Error('Failed to check library');
    return response.json();
  },
};

// Kullanıcı bilgilerini localStorage'da sakla
export const userStorage = {
  setUser(user: User) {
    localStorage.setItem('user', JSON.stringify(user));
  },

  getUser(): User | null {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },

  removeUser() {
    localStorage.removeItem('user');
  },

  setToken(token: string) {
    localStorage.setItem('authToken', token);
  },

  getToken(): string | null {
    return localStorage.getItem('authToken');
  },

  removeToken() {
    localStorage.removeItem('authToken');
  },

  isLoggedIn(): boolean {
    return !!this.getUser();
  },
};

// Activity API (Kullanıcı Aktiviteleri)
export interface ActivityItem {
  id: number;
  type: 'search' | 'save' | 'remove_save' | 'view' | 'like' | 'remove_like' | 'profile_update';
  content_title: string;
  content_id: string;
  query: string;
  created_at: string;
}

export interface ActivityResponse {
  success: boolean;
  activities: ActivityItem[];
}

export const activityApi = {
  async record(userId: number, activity: {
    activity_type: 'search' | 'save' | 'remove_save' | 'view' | 'like' | 'remove_like' | 'profile_update';
    content_title?: string;
    content_id?: string;
    query?: string;
  }): Promise<{ success: boolean; message: string; activity_id?: number }> {
    const response = await fetch(`${API_BASE_URL}/activity/record/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, ...activity }),
    });
    if (!response.ok) throw new Error('Failed to record activity');
    return response.json();
  },

  async getRecent(userId: number, limit: number = 10): Promise<ActivityResponse> {
    const response = await fetch(`${API_BASE_URL}/activity/recent/?user_id=${userId}&limit=${limit}`);
    if (!response.ok) throw new Error('Failed to fetch activities');
    return response.json();
  },
};

// Recommendation API (Öneri Sistemi)
export interface RecommendationItem {
  external_id: string;
  title: string;
  abstract: string;
  authors: Array<{ name: string }>;
  published_date: string;
  url: string;
  pdf_url: string;
  image_url: string;
  doi: string;
  source: string;
  categories: string[];
  score: number;
}

export interface RecommendationResponse {
  success: boolean;
  recommendations: RecommendationItem[];
  count: number;
  message?: string;
}

export interface NLPStatusResponse {
  success: boolean;
  nlp_processed: number;
  total_content: number;
  unprocessed: number;
  coverage: number;
}

export const recommendationApi = {
  async getRecommendations(userId: number, limit: number = 20): Promise<RecommendationResponse> {
    const response = await fetch(`${API_BASE_URL}/recommendations/?user_id=${userId}&limit=${limit}`);
    if (!response.ok) throw new Error('Failed to fetch recommendations');
    return response.json();
  },

  async getSimilar(externalId: string, limit: number = 10): Promise<{ success: boolean; similar: RecommendationItem[]; count: number }> {
    const response = await fetch(`${API_BASE_URL}/recommendations/similar/?external_id=${encodeURIComponent(externalId)}&limit=${limit}`);
    if (!response.ok) throw new Error('Failed to fetch similar articles');
    return response.json();
  },

  async getNLPStatus(): Promise<NLPStatusResponse> {
    const response = await fetch(`${API_BASE_URL}/recommendations/nlp-status/`);
    if (!response.ok) throw new Error('Failed to fetch NLP status');
    return response.json();
  },

  async triggerProcessing(batchSize: number = 50): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE_URL}/recommendations/process/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ batch_size: batchSize }),
    });
    if (!response.ok) throw new Error('Failed to trigger NLP processing');
    return response.json();
  },
};

