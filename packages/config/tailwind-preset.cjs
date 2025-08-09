module.exports = {
  content: [],
  theme: {
    extend: {
      colors: {
        sunBurst: 'var(--sun-burst)',
        ink: 'var(--ink)',
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
      keyframes: {
        'px-glow': {
          '0%, 100%': { boxShadow: '0 0 5px var(--sun-burst)' },
          '50%': { boxShadow: '0 0 20px var(--sun-burst), 0 0 30px var(--sun-burst)' }
        },
        'px-fade-in': {
          from: { opacity: '0', transform: 'translateY(10px)' },
          to: { opacity: '1', transform: 'translateY(0)' }
        }
      },
      animation: {
        pxGlow: 'px-glow 2s ease-in-out infinite',
        pxFadeIn: 'px-fade-in .3s ease both'
      }
    }
  },
  plugins: []
};