import { Configuration } from "./runtime";

export const makeBffConfig = (opts: { baseURL?: string; token?: string }) =>
  new Configuration({
    basePath: opts.baseURL ?? (typeof globalThis !== "undefined" && (globalThis as any).process?.env?.NEXT_PUBLIC_BFF_URL),
    headers: opts.token ? { Authorization: `Bearer ${opts.token}` } : {}
  });