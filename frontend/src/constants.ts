import type { User, AcademicContent, NewsItem } from './types';

// Mock User Data
export const MOCK_USER: User = {
    name: 'Ahmet Kaya',
    role: 'Researcher • Machine Learning Specialist',
    institution: 'Istanbul Technical University',
    bio: 'Passionate researcher focused on deep learning, computer vision, and natural language processing. Currently working on transformer-based models for Turkish language understanding.',
    interests: ['Machine Learning', 'Computer Vision', 'Natural Language Processing', 'Deep Learning'],
};

// Mock Academic Content
export const MOCK_CONTENT: AcademicContent[] = [
    {
        id: 'c1',
        type: 'article',
        title: 'Transformer-Based Models for Low-Resource Languages',
        description: 'This paper explores the application of transformer architectures to improve machine translation and text generation for languages with limited training data.',
        source: 'arXiv',
        date: 'Dec 15, 2024',
        tags: ['NLP', 'Transformers', 'Low-Resource'],
    },
    {
        id: 'c2',
        type: 'conference',
        title: 'International Conference on Machine Learning (ICML) 2024',
        description: 'Premier gathering of researchers in machine learning, featuring cutting-edge research in deep learning, reinforcement learning, and AI applications.',
        source: 'ICML Foundation',
        date: 'July 21-27, 2024',
        location: 'Vienna, Austria',
        deadline: 'Feb 01, 2024',
        tags: ['Machine Learning', 'Deep Learning', 'AI'],
    },
];

// News Items
export const NEWS_ITEMS: NewsItem[] = [
    {
        id: 'n1',
        title: 'OpenAI Releases GPT-5: Next Generation Language Model',
        description: 'Revolutionary breakthrough in natural language understanding with 10x improvement in reasoning capabilities.',
        source: 'OpenAI Blog',
        date: 'Dec 20, 2024',
        tags: ['AI', 'NLP', 'GPT'],
    },
    {
        id: 'n2',
        title: 'European Research Council Announces €2B Funding Initiative',
        description: 'New funding program targeting AI ethics, sustainability, and healthcare applications across EU member states.',
        source: 'ERC News',
        date: 'Dec 18, 2024',
        tags: ['Funding', 'Research', 'Europe'],
    },
    {
        id: 'n3',
        title: 'TÜBİTAK 1001 Program: 2025 Application Period Opens',
        description: 'Turkish scientific research support program now accepting applications for fundamental research projects.',
        source: 'TÜBİTAK',
        date: 'Dec 10, 2024',
        tags: ['Turkey', 'Funding', 'Research'],
    },
    {
        id: 'n4',
        title: 'NeurIPS 2024 Best Paper Award: Quantum Machine Learning',
        description: 'Groundbreaking work on quantum algorithms for machine learning wins prestigious award.',
        source: 'NeurIPS',
        date: 'Dec 12, 2024',
        tags: ['Quantum', 'ML', 'Awards'],
    },
];
