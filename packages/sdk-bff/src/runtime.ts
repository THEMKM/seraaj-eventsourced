/**
 * Runtime configuration for the Seraaj BFF SDK
 */

export interface RequestOptions {
  method: string;
  headers?: Record<string, string>;
  body?: string;
}

export class Configuration {
  constructor(private options: {
    basePath?: string;
    headers?: Record<string, string>;
  } = {}) {}

  get basePath(): string {
    return this.options.basePath || 'http://localhost:8000/api';
  }

  get headers(): Record<string, string> {
    return this.options.headers || {};
  }
}

export class BaseAPI {
  constructor(protected configuration: Configuration = new Configuration()) {}

  protected async request<T>(
    path: string, 
    requestOptions: RequestOptions
  ): Promise<T> {
    const url = `${this.configuration.basePath}${path}`;
    
    const response = await fetch(url, {
      method: requestOptions.method,
      headers: {
        'Content-Type': 'application/json',
        ...this.configuration.headers,
        ...requestOptions.headers,
      },
      body: requestOptions.body,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }
}