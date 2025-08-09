export default [
  {
    files: ['app/**/*.{js,jsx,ts,tsx}', 'contexts/**/*.{js,jsx,ts,tsx}', 'lib/**/*.{js,jsx,ts,tsx}'],
    ignores: ['.next/**', 'node_modules/**'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module'
    },
    rules: {
      'no-restricted-imports': [2, {
        patterns: [
          '*axios*',
          '*node-fetch*',
          '*cross-fetch*',
          '*ky*',
          '*superagent*'
        ]
      }],
      'no-restricted-globals': [2, 'fetch']
    }
  }
];