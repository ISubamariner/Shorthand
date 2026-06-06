import type {
  Attempt, LeaderboardEntry, ProgressResponse, Symbol, TokenPair, User,
  Word, WordListItem, WordProgress, WordSession, WordTopic,
} from "../types";

const BASE_URL = import.meta.env.VITE_API_URL || "/api";

let accessToken: string | null = localStorage.getItem("shorthand_access_token");
let refreshToken: string | null = localStorage.getItem("shorthand_refresh_token");

function setTokens(access: string | null, refresh?: string | null) {
  accessToken = access;
  if (access) {
    localStorage.setItem("shorthand_access_token", access);
  } else {
    localStorage.removeItem("shorthand_access_token");
  }
  if (refresh !== undefined) {
    refreshToken = refresh;
    if (refresh) {
      localStorage.setItem("shorthand_refresh_token", refresh);
    } else {
      localStorage.removeItem("shorthand_refresh_token");
    }
  }
}

export function getAccessToken(): string | null {
  return accessToken;
}

function getSessionToken(): string {
  let token = localStorage.getItem("shorthand_session_token");
  if (!token) {
    token = crypto.randomUUID();
    localStorage.setItem("shorthand_session_token", token);
  }
  return token;
}

let refreshPromise: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  if (!refreshToken) return false;
  if (refreshPromise) return refreshPromise;
  refreshPromise = (async () => {
    try {
      const res = await fetch(`${BASE_URL}/auth/refresh/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh: refreshToken }),
      });
      if (!res.ok) return false;
      const data = await res.json();
      setTokens(data.access);
      return true;
    } catch {
      return false;
    } finally {
      refreshPromise = null;
    }
  })();
  return refreshPromise;
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Session-Token": getSessionToken(),
    ...(options.headers as Record<string, string>),
  };

  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401 && accessToken && refreshToken) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      headers["Authorization"] = `Bearer ${accessToken}`;
      const retry = await fetch(`${BASE_URL}${path}`, { ...options, headers });
      if (retry.ok) {
        if (retry.status === 204) return undefined as T;
        return retry.json();
      }
      if (retry.status === 401) {
        setTokens(null, null);
      }
      const retryBody = await retry.json().catch(() => ({}));
      throw new ApiError(retry.status, retryBody);
    }
    setTokens(null, null);
  } else if (response.status === 401 && accessToken) {
    setTokens(null, null);
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

export function adminRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  return request(`/admin${path}`, options);
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
    async login(data: { username: string; password: string }): Promise<TokenPair> {
      const tokens = await request<TokenPair>("/auth/login/", { method: "POST", body: JSON.stringify(data) });
      setTokens(tokens.access, tokens.refresh);
      await request("/auth/claim-session/", { method: "POST" }).catch(() => {});
      localStorage.removeItem("shorthand_session_token");
      return tokens;
    },
    me(): Promise<User> {
      return request("/auth/me/");
    },
    updateMe(data: { email?: string; current_password?: string; new_password?: string }): Promise<User> {
      return request("/auth/me/", { method: "PATCH", body: JSON.stringify(data) });
    },
    async logout() {
      await request("/auth/logout/", { method: "POST" }).catch(() => {});
      setTokens(null, null);
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
    create(data: {
      symbol_letter: string;
      image_data: string;
      word_session?: string;
      word_position?: number;
    }): Promise<Attempt> {
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
    get(): Promise<ProgressResponse> {
      return request("/progress/");
    },
  },
  leaderboard: {
    get(): Promise<LeaderboardEntry[]> {
      return request("/leaderboard/");
    },
  },
  words: {
    list(params?: { difficulty?: string; topic?: string }): Promise<{ results: WordListItem[]; count: number }> {
      const search = new URLSearchParams();
      if (params?.difficulty) search.set("difficulty", params.difficulty);
      if (params?.topic) search.set("topic", params.topic);
      const qs = search.toString();
      return request(`/words/${qs ? `?${qs}` : ""}`);
    },
    get(id: string): Promise<Word> {
      return request(`/words/${id}/`);
    },
    topics(): Promise<WordTopic[]> {
      return request("/word-topics/");
    },
  },
  wordSessions: {
    create(wordId: string): Promise<WordSession> {
      return request("/word-sessions/", {
        method: "POST",
        body: JSON.stringify({ word_id: wordId }),
      });
    },
    get(id: string): Promise<WordSession> {
      return request(`/word-sessions/${id}/`);
    },
    complete(id: string): Promise<WordSession> {
      return request(`/word-sessions/${id}/complete/`, { method: "POST" });
    },
  },
  wordProgress: {
    get(params?: { difficulty?: string; topic?: string }): Promise<WordProgress[]> {
      const search = new URLSearchParams();
      if (params?.difficulty) search.set("difficulty", params.difficulty);
      if (params?.topic) search.set("topic", params.topic);
      const qs = search.toString();
      return request(`/word-progress/${qs ? `?${qs}` : ""}`);
    },
  },
};
