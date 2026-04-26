/** @type {import('tailwindcss').Config} */
export default {
    darkMode: 'class',
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
                serif: ['Newsreader', 'Georgia', 'serif'],
            },
            colors: {
                navy: {
                    50: '#f0f4fa',
                    100: '#dce4f2',
                    200: '#b8c9e5',
                    300: '#8ba7d3',
                    400: '#5f82bd',
                    500: '#3d63a5',
                    600: '#2d4e89',
                    700: '#243f6e',
                    800: '#1c325a',
                    900: '#0f1d34',
                    950: '#080e1a',
                },
                accent: {
                    coral: '#E8634A',
                    teal: '#2BA5A0',
                    amber: '#F2A93B',
                    violet: '#7C5CFC',
                },
            },
            animation: {
                'fade-in': 'fadeIn 0.4s ease-out',
                'slide-up': 'slideUp 0.5s ease-out',
                'slide-in-right': 'slideInRight 0.3s ease-out',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideUp: {
                    '0%': { opacity: '0', transform: 'translateY(16px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                slideInRight: {
                    '0%': { opacity: '0', transform: 'translateX(16px)' },
                    '100%': { opacity: '1', transform: 'translateX(0)' },
                },
            },
        },
    },
    plugins: [],
}
