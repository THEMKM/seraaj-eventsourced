const preset = require('../../packages/config/tailwind-preset.cjs');

module.exports = {
  presets: [preset],
  content: [
    'app/**/*.{ts,tsx}',
    'components/**/*.{ts,tsx}',
    '../../packages/ui/src/**/*.{ts,tsx,css}'
  ]
};