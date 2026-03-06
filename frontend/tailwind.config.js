module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        fmc: {
          'bg':           '#0f0418',
          'surface':      '#1a0828',
          'panel':        '#4C1D3D',
          'card':         '#2d1040',
          'border':       '#DC586D',
          'border-glow':  '#FB9590',
          'accent':       '#DC586D',
          'accent-dark':  '#A33757',
          'accent-deep':  '#852E4E',
          'glow':         '#FB9590',
          'text':         '#FFBB94',
          'text-muted':   '#FB9590',
          'text-dim':     '#A33757',
          'text-bright':  '#FFBB94',
          'success':      '#4ade80',
          'warning':      '#fbbf24',
          'danger':       '#f87171',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Cascadia Code', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'glow-pulse':    'glow-pulse 2s ease-in-out infinite',
        'border-flow':   'border-flow 3s linear infinite',
        'shimmer':       'shimmer 1.5s infinite',
        'slide-in':      'slide-in 0.3s ease-out',
        'fade-in':       'fade-in 0.2s ease-out',
        'spin-slow':     'spin 3s linear infinite',
      },
      keyframes: {
        'glow-pulse': {
          '0%, 100%': { boxShadow: '0 0 8px #DC586D, 0 0 16px #DC586D40' },
          '50%':      { boxShadow: '0 0 16px #FB9590, 0 0 32px #FB959060' },
        },
        'border-flow': {
          '0%':   { borderColor: '#DC586D' },
          '50%':  { borderColor: '#FB9590' },
          '100%': { borderColor: '#DC586D' },
        },
        'shimmer': {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'slide-in': {
          from: { transform: 'translateX(-10px)', opacity: '0' },
          to:   { transform: 'translateX(0)',     opacity: '1' },
        },
        'fade-in': {
          from: { opacity: '0', transform: 'translateY(4px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
      },
      boxShadow: {
        'neon':       '0 0 8px #DC586D, 0 0 20px #DC586D40',
        'neon-hover': '0 0 12px #FB9590, 0 0 30px #FB959050',
        'neon-soft':  '0 0 4px #DC586D60',
        'card':       '0 4px 24px rgba(15, 4, 24, 0.8)',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
  safelist: [
    { pattern: /text-fmc-/ },
    { pattern: /bg-fmc-/ },
    { pattern: /border-fmc-/ },
    { pattern: /shadow-neon/ },
  ],
};
