export interface AdminUser {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_staff: boolean;
  date_joined: string;
  last_login: string | null;
}

export interface DashboardStats {
  user_count: number;
  attempt_count: number;
  active_today: number;
  pending_jobs: number;
  failed_jobs: number;
}

export interface AdminSymbol {
  id: number;
  letter: string;
  name: string;
  reference_image_url: string;
  symbol_type: "letter" | "grouping";
}

export interface AdminWord {
  id: string;
  text: string;
  teeline_letters: string;
  difficulty: "beginner" | "intermediate" | "advanced";
  topic: string;
  topic_name: string;
  is_curated: boolean;
  created_at: string;
}

export interface AdminJob {
  id: string;
  type: string;
  status: "pending" | "running" | "completed" | "failed" | "dead";
  priority: number;
  attempts: number;
  max_attempts: number;
  error_log: string;
  scheduled_at: string;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminJobDetail extends AdminJob {
  user: number | null;
  correlation_key: string | null;
  payload: Record<string, unknown>;
  locked_at: string | null;
  locked_by: string | null;
}

export interface AuditLogEntry {
  id: string;
  actor: number | null;
  actor_username: string | null;
  action: string;
  target_type: string;
  target_id: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface SystemSetting {
  id: string;
  key: string;
  value: unknown;
  updated_at: string;
  updated_by: number | null;
}

export interface UsageStats {
  daily: Array<{ date: string; count: number }>;
  total: number;
}

export interface RetentionStats {
  total_users: number;
  active_users: number;
  retention_rate: number;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface MonitoringSnapshot {
  cpu_percent: number;
  memory_percent: number;
  memory_used_mb: number;
  memory_total_mb: number;
  disk_percent: number;
  disk_used_gb: number;
  disk_total_gb: number;
  process_uptime_seconds: number;
  db_size_mb: number;
  db_connections: number;
  table_stats: MonitoringTableStat[];
}

export interface MonitoringHistoryPoint {
  timestamp: string;
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
  db_size_mb: number;
  db_connections: number;
}

export interface MonitoringTableStat {
  name: string;
  row_count: number;
  size_mb: number;
}
