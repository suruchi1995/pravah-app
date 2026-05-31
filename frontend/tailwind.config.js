export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#1a2332', slate2: '#475569', mist: '#f5f7fa',
        brand: '#2E5C8A', branddk: '#1F3A5F',
        sage: '#5b8a72', amber2: '#c98a3c', rust: '#b5544a',
      },
      fontFamily: {
        display: ['"Fraunces"', 'Georgia', 'serif'],
        sans: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
