export interface Symbol {
  id: number;
  letter: string;
  name: string;
  reference_image_url: string;
}

export interface Attempt {
  id: string;
  symbol: number;
  symbol_letter: string;
  image_url: string;
  predicted_label: string | null;
  confidence: number | null;
  is_correct: boolean | null;
  status: "pending" | "processing" | "completed" | "failed";
  created_at: string;
}

export interface Progress {
  symbol_letter: string;
  total: number;
  correct: number;
  accuracy: number;
}

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
}
