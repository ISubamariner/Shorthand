import type {
  Attempt, LeaderboardEntry, ProgressResponse, Symbol, TokenPair, User,
  Word, WordListItem, WordProgress, WordSession, WordTopic,
} from "../types";

const BASE_URL = import.meta.env.VITE_API_URL || "/api";

let accessToken: string | null = null;

function setAccessToken(token: string | null) {
  accessToken = token;
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

  if (response.status === 401 && accessToken) {
    setAccessToken(null);
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
    async login(data: { username: string; password: string }): Promise<TokenPair> {
      const tokens = await request<TokenPair>("/auth/login/", { method: "POST", body: JSON.stringify(data) });
      setAccessToken(tokens.access);
      await request("/auth/claim-session/", { method: "POST" }).catch(() => {});
      localStorage.removeItem("shorthand_session_token");
      return tokens;
    },
    me(): Promise<User> {
      return request("/auth/me/");
    },
    async logout() {
      await request("/auth/logout/", { method: "POST" }).catch(() => {});
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
