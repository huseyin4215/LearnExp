// View Types - using string literals instead of enums for strict TS compatibility
export type ViewType = 'dashboard' | 'search' | 'library' | 'profile' | 'settings';

// Content Types - using string literals instead of enums
export type ContentType = 'article' | 'conference' | 'funding';

// Academic Content Interface
export interface AcademicContent {
    id: string;
    type: ContentType;
    title: string;
    description: string;
    source: string;
    date: string;
    tags: string[];
    keywords?: string[];
    deadline?: string;
    location?: string;
    amount?: string;
    url?: string;
    authors?: string;
    journal?: string;
    citations?: number;
    pdfUrl?: string;
    imageUrl?: string;
}

// User Interface
export interface User {
    name: string;
    role: string;
    institution: string;
    bio: string;
    interests: string[];
}

// News Item Interface
export interface NewsItem {
    id: string;
    title: string;
    description: string;
    source: string;
    date: string;
    tags: string[];
}

// Chat Message Interface
export interface ChatMessage {
    role: 'user' | 'model';
    text: string;
}
