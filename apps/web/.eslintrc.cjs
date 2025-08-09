module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  plugins: ['boundaries', '@typescript-eslint'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'next/core-web-vitals'
  ],
  settings: {
    'boundaries/elements': [
      { type: 'ui', pattern: '@seraaj/ui' },
      { type: 'sdk', pattern: '@seraaj/sdk-bff' }
    ]
  },
  rules: {
    'boundaries/element-types': [2, {
      default: 'disallow',
      rules: [{ from: ['apps'], allow: ['ui', 'sdk'] }]
    }],
    'no-restricted-imports': [2, {
      paths: [
        { name: 'axios', message: 'Use @seraaj/sdk-bff' },
        { name: 'node-fetch', message: 'Use @seraaj/sdk-bff' },
        { name: '@seraaj/sdk-bff', importNames: ['*'], message: 'Import via package root or ./client only' }
      ],
      patterns: ['**/fetch', '@seraaj/sdk-bff/src/**']
    }],
    'no-restricted-globals': [2, 'fetch']
  }
};