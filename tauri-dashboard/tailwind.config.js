/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        primary: '#00d4aa',
        secondary: '#6b7280',
      }
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('daisyui')
  ],
  daisyui: {
    themes: [
      {
        dark: {
          ...require('daisyui/src/theming/themes')['dark'],
          primary: '#00d4aa',
          'primary-focus': '#00b894',
          'primary-content': '#ffffff',
        }
      },
      'light'
    ],
    darkTheme: 'dark'
  }
}