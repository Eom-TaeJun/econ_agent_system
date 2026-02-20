// tailwind.config.template.js
// Finance Harness / EIMAS Design System — Master Template
// 프로젝트별로 복사 후 PRIMARY / SECONDARY 값만 교체할 것.

/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: false, // 다크모드 비활성화 (명시적 요청 시에만 'class'로 변경)
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      // ─── 여기만 프로젝트별로 교체 ───────────────────────────
      colors: {
        primary: {
          DEFAULT: '#2563EB',
          50:  '#EFF6FF',
          100: '#DBEAFE',
          200: '#BFDBFE',
          300: '#93C5FD',
          400: '#60A5FA',
          500: '#2563EB',
          600: '#1D4ED8',
          700: '#1E40AF',
          800: '#1E3A8A',
          900: '#1E3050',
        },
        secondary: {
          DEFAULT: '#10B981',
          50:  '#ECFDF5',
          100: '#D1FAE5',
          200: '#A7F3D0',
          300: '#6EE7B7',
          400: '#34D399',
          500: '#10B981',
          600: '#059669',
          700: '#047857',
          800: '#065F46',
          900: '#064E3B',
        },
      },
      // ─── 아래는 모든 프로젝트 공통 (수정 금지) ────────────────
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        // 허용된 타이포 스케일 (이 외 크기 사용 금지)
        'xs':   ['12px', { lineHeight: '1.5' }],
        'sm':   ['14px', { lineHeight: '1.6' }],
        'base': ['16px', { lineHeight: '1.6' }],
        'xl':   ['20px', { lineHeight: '1.4' }],
        '3xl':  ['30px', { lineHeight: '1.2' }],
      },
      spacing: {
        // 4px 기반 8단계 스케일 (이 외 값 사용 금지)
        '1':  '4px',
        '2':  '8px',
        '4':  '16px',
        '6':  '24px',
        '8':  '32px',
        '12': '48px',
        '16': '64px',
        '24': '96px',
      },
      borderRadius: {
        'sm':  '6px',
        'md':  '8px',
        'lg':  '12px',
        'xl':  '16px',
        '2xl': '20px',
      },
      boxShadow: {
        'card': '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        'card-hover': '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
      },
      maxWidth: {
        'content': '1280px', // max-w-7xl
      },
    },
  },
  plugins: [
    require('tailwindcss-animate'), // shadcn/ui 필수
  ],
}
