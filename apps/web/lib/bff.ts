'use client';

import { makeBffConfig } from '@seraaj/sdk-bff';

export const cfgFor = (token?: string) => makeBffConfig({ 
  baseURL: process.env.NEXT_PUBLIC_BFF_URL || 'http://localhost:8000/api', 
  token 
});