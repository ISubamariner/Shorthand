export interface Symbol {
  id: number;
  letter: string;
  name: string;
  reference_image_url: string;
  symbol_type: "letter" | "grouping";
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
  points: number;
  created_at: string;
}

export interface Progress {
  symbol_letter: string;
  total: number;
  correct: number;
  accuracy: number;
}

export interface ProgressResponse {
  symbols: Progress[];
  current_streak: number;
  best_streak: number;
  total_score: number;
}

export interface LeaderboardEntry {
  rank: number;
  display_name: string;
  total_score: number;
  best_streak: number;
  is_current_user: boolean;
}

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  is_staff: boolean;
}

export interface WordTopic {
  id: string;
  name: string;
  slug: string;
}

export interface TeelineComponent {
  letter: string;
  blend_with: string | null;
  is_doubled_for_r: boolean;
  position: number;
}

export interface Word {
  id: string;
  text: string;
  teeline_letters: string;
  teeline_skeleton: string;
  difficulty: "beginner" | "intermediate" | "advanced";
  topic: WordTopic;
  components: TeelineComponent[];
}

export interface WordListItem {
  id: string;
  text: string;
  teeline_letters: string;
  teeline_skeleton: string;
  difficulty: "beginner" | "intermediate" | "advanced";
  topic: WordTopic;
}

export interface WordSession {
  id: string;
  word: Word;
  status: "in_progress" | "completed" | "abandoned";
  letters_correct: number;
  letters_total: number;
  points_awarded: number;
  letter_results: Record<number, { attempt_id: string; is_correct: boolean }>;
}

export interface WordProgress {
  word_id: string;
  word_text: string;
  total_sessions: number;
  completed_sessions: number;
  perfect_sessions: number;
  accuracy: number;
}

export interface WordSuggestion {
  word_id: string;
  text: string;
  teeline_skeleton: string;
  difficulty: string;
  topic_name: string | null;
}
