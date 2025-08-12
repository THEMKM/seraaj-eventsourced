/**
 * Client factory for @seraaj/sdk-bff
 */

import { Configuration } from './runtime';
import { DefaultApi, AuthenticationApi, SystemApi, VolunteerApi } from './apis';

export interface BffClientConfig {
  basePath?: string;
  accessToken?: string;
  headers?: Record<string, string>;
}

export function makeBffConfig(config: BffClientConfig = {}): Configuration {
  return {
    basePath: config.basePath || process.env.NEXT_PUBLIC_BFF_URL || 'http://localhost:8000/api',
    accessToken: config.accessToken,
    headers: config.headers,
  };
}

export function createBffClient(config?: BffClientConfig): DefaultApi {
  const configuration = makeBffConfig(config);
  return new DefaultApi(configuration);
}

// Individual API clients for more granular usage
export function createAuthApi(config?: BffClientConfig): AuthenticationApi {
  const configuration = makeBffConfig(config);
  return new AuthenticationApi(configuration);
}

export function createSystemApi(config?: BffClientConfig): SystemApi {
  const configuration = makeBffConfig(config);
  return new SystemApi(configuration);
}

export function createVolunteerApi(config?: BffClientConfig): VolunteerApi {
  const configuration = makeBffConfig(config);
  return new VolunteerApi(configuration);
}