import type { User, AcademicContent } from './types';

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
        url: 'https://arxiv.org/abs/1706.03762',
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
