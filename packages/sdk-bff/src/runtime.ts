/**
 * Runtime utilities for @seraaj/sdk-bff
 */

export interface Configuration {
  basePath?: string;
  accessToken?: string;
  headers?: Record<string, string>;
}

export class BaseAPI {
  public configuration: Configuration;

  constructor(configuration?: Configuration) {
    this.configuration = {
      basePath: 'http://localhost:8000/api',
      ...configuration,
    };
  }

  protected async request<T>(
    path: string,
    init?: RequestInit
  ): Promise<T> {
    const url = `${this.configuration.basePath}${path}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...this.configuration.headers,
    };

    if (this.configuration.accessToken) {
      headers.Authorization = `Bearer ${this.configuration.accessToken}`;
    }

    const response = await fetch(url, {
      ...init,
      headers: {
        ...headers,
        ...init?.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        `HTTP ${response.status}: ${errorData.message || response.statusText}`
      );
    }

    return response.json();
  }
}