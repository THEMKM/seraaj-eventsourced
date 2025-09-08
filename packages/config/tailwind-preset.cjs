module.exports = {
  content: [],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Updated 8-Bit Optimism palette matching reference
        primary: '#FFD749',
        sunBurst: 'var(--sun-burst)',
        ink: 'var(--ink)',
        'pixel-coral': '#FF6B94',
        'pixel-mint': '#00D9FF', 
        'pixel-lavender': '#9A48FF',
        'deep-indigo': '#1A1B5C',
        'electric-teal': '#00D4AA',
        'warm-sandstone': '#F5E6D3',
        'neon-cyan': '#00FFFF',
        'neon-pink': '#FF00FF',
        'neon-green': '#00FF00',
        'dark-bg': '#0D1117',
        'dark-surface': '#161B22',
        'dark-border': '#30363D',
        pixelCoral: 'var(--pixel-coral)',
        neonCyan: 'var(--neon-cyan)',
        electricTeal: 'var(--electric-teal)',
        deepIndigo: 'var(--deep-indigo)',
        pixelLavender: 'var(--pixel-lavender)',
        success: 'var(--success)',
        warning: 'var(--warning)',
        error: 'var(--error)',
        info: 'var(--info)'
      },
      fontFamily: {
        pixel: ['"Press Start 2P"', 'monospace'],
        body: ['Inter', 'sans-serif']
      },
      spacing: {
        'px': '8px',
        'px-2': '16px', 
        'px-3': '24px',
        'px-4': '32px'
      },
      keyframes: {
        'px-glow': {
          '0%, 100%': { boxShadow: '0 0 5px var(--sun-burst)' },
          '50%': { boxShadow: '0 0 20px var(--sun-burst), 0 0 30px var(--sun-burst)' }
        },
        'px-fade-in': {
          from: { opacity: '0', transform: 'translateY(10px)' },
          to: { opacity: '1', transform: 'translateY(0)' }
        },
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        },
        slideIn: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(0)' }
        },
        glow: {
          '0%': { boxShadow: '0 0 5px #FFD749, 0 0 10px #FFD749' },
          '100%': { boxShadow: '0 0 20px #FFD749, 0 0 30px #FFD749' }
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' }
        }
      },
      animation: {
        pxGlow: 'px-glow 2s ease-in-out infinite',
        pxFadeIn: 'px-fade-in .3s ease both',
        'px-bounce': 'bounce 1s infinite steps(8)',
        'px-pulse': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'px-spin': 'spin 1s steps(8) infinite',
        'px-slide-in': 'slideIn 0.3s ease-out',
        'px-shimmer': 'shimmer 2s linear infinite'
      }
    }
  },
  plugins: [
    function({ addUtilities }) {
      addUtilities({
        '.clip-px': {
          'clip-path': 'polygon(8px 0%, 100% 0%, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0% 100%, 0% 8px)'
        },
        '.shadow-px': {
          'box-shadow': '4px 4px 0px #101028'
        },
        '.shadow-px-glow': {
          'box-shadow': '4px 4px 0px #101028, 0 0 20px rgba(255, 215, 73, 0.5)'
        },
        '.shadow-px-dark': {
          'box-shadow': '4px 4px 0px #30363D'
        },
        '.border-px': {
          'border-width': '2px',
          'border-style': 'solid'
        },
        '.ripple': {
          'position': 'relative',
          'overflow': 'hidden',
          'transform': 'translate3d(0, 0, 0)'
        },
        '.shimmer': {
          'background': 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent)',
          'background-size': '200% 100%'
        },
        '.pixel-perfect': {
          'image-rendering': 'pixelated',
          'image-rendering': '-moz-crisp-edges',
          'image-rendering': 'crisp-edges'
        },
        // RTL utilities
        '.rtl': { direction: 'rtl' },
        '.ltr': { direction: 'ltr' },
        '.rtl .text-left': { 'text-align': 'right' },
        '.rtl .text-right': { 'text-align': 'left' },
        '.rtl .ml-auto': { 'margin-left': '0', 'margin-right': 'auto' },
        '.rtl .mr-auto': { 'margin-right': '0', 'margin-left': 'auto' }
      });
    }
  ]
};