import type { Attempt, Progress, Symbol, TokenPair, User } from "../types";

const BASE_URL = import.meta.env.VITE_API_URL || "/api";

let accessToken: string | null = null;
let isRedirectingTo401 = false;

function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401 && !isRedirectingTo401) {
    isRedirectingTo401 = true;
    setAccessToken(null);
    window.location.href = "/login";
    isRedirectingTo401 = false;
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(response.status, body);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: unknown
  ) {
    super(`API error ${status}`);
  }
}

export const api = {
  auth: {
    register(data: { username: string; email: string; password: string }): Promise<User> {
      return request("/auth/register/", { method: "POST", body: JSON.stringify(data) });
    },
    login(data: { username: string; password: string }): Promise<TokenPair> {
      return request<TokenPair>("/auth/login/", { method: "POST", body: JSON.stringify(data) }).then(
        (tokens) => {
          setAccessToken(tokens.access);
          return tokens;
        }
      );
    },
    me(): Promise<User> {
      return request("/auth/me/");
    },
    logout() {
      setAccessToken(null);
    },
  },
  symbols: {
    list(): Promise<Symbol[]> {
      return request("/symbols/");
    },
    get(letter: string): Promise<Symbol> {
      return request(`/symbols/${letter}/`);
    },
  },
  attempts: {
    create(data: { symbol_letter: string; image_data: string }): Promise<Attempt> {
      return request("/attempts/", { method: "POST", body: JSON.stringify(data) });
    },
    list(): Promise<{ results: Attempt[]; count: number }> {
      return request("/attempts/");
    },
    get(id: string): Promise<Attempt> {
      return request(`/attempts/${id}/`);
    },
  },
  progress: {
    get(): Promise<Progress[]> {
      return request("/progress/");
    },
  },
};
