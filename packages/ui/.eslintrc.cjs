module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint'],
  extends: [
    'eslint:recommended',
    '@typescript-eslint/recommended'
  ],
  env: {
    browser: true,
    es2022: true
  },
  ignorePatterns: ['dist/', 'node_modules/']
};