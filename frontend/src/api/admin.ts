import type {
  AdminUser,
  AdminJob,
  AdminJobDetail,
  AdminSymbol,
  AdminWord,
  AuditLogEntry,
  DashboardStats,
  PaginatedResponse,
  RetentionStats,
  SystemSetting,
  UsageStats,
  MonitoringSnapshot,
  MonitoringHistoryPoint,
  MonitoringTableStat,
} from "../types/admin";
import { adminRequest } from "./client";

export const adminApi = {
  dashboard: {
    stats(): Promise<DashboardStats> {
      return adminRequest("/dashboard/stats/");
    },
  },
  users: {
    list(params?: { search?: string; page?: number }): Promise<PaginatedResponse<AdminUser>> {
      const search = new URLSearchParams();
      if (params?.search) search.set("search", params.search);
      if (params?.page) search.set("page", String(params.page));
      const qs = search.toString();
      return adminRequest(`/users/${qs ? `?${qs}` : ""}`);
    },
    get(id: number): Promise<AdminUser> {
      return adminRequest(`/users/${id}/`);
    },
    update(id: number, data: Partial<Pick<AdminUser, "is_active" | "is_staff">>): Promise<AdminUser> {
      return adminRequest(`/users/${id}/`, { method: "PATCH", body: JSON.stringify(data) });
    },
  },
  content: {
    symbols: {
      list(): Promise<AdminSymbol[]> {
        return adminRequest("/content/symbols/");
      },
      create(data: { letter: string; name: string; reference_image_url?: string }): Promise<AdminSymbol> {
        return adminRequest("/content/symbols/", { method: "POST", body: JSON.stringify(data) });
      },
      update(id: number, data: Partial<AdminSymbol>): Promise<AdminSymbol> {
        return adminRequest(`/content/symbols/${id}/`, { method: "PATCH", body: JSON.stringify(data) });
      },
      delete(id: number): Promise<void> {
        return adminRequest(`/content/symbols/${id}/`, { method: "DELETE" });
      },
    },
    words: {
      list(): Promise<AdminWord[]> {
        return adminRequest("/content/words/");
      },
      create(data: Omit<AdminWord, "id" | "topic_name" | "created_at">): Promise<AdminWord> {
        return adminRequest("/content/words/", { method: "POST", body: JSON.stringify(data) });
      },
      update(id: string, data: Partial<AdminWord>): Promise<AdminWord> {
        return adminRequest(`/content/words/${id}/`, { method: "PATCH", body: JSON.stringify(data) });
      },
      delete(id: string): Promise<void> {
        return adminRequest(`/content/words/${id}/`, { method: "DELETE" });
      },
    },
  },
  analytics: {
    usage(days?: number): Promise<UsageStats> {
      const qs = days ? `?days=${days}` : "";
      return adminRequest(`/analytics/usage/${qs}`);
    },
    retention(days?: number): Promise<RetentionStats> {
      const qs = days ? `?days=${days}` : "";
      return adminRequest(`/analytics/retention/${qs}`);
    },
  },
  jobs: {
    list(params?: { status?: string; page?: number }): Promise<PaginatedResponse<AdminJob>> {
      const search = new URLSearchParams();
      if (params?.status) search.set("status", params.status);
      if (params?.page) search.set("page", String(params.page));
      const qs = search.toString();
      return adminRequest(`/jobs/${qs ? `?${qs}` : ""}`);
    },
    get(id: string): Promise<AdminJobDetail> {
      return adminRequest(`/jobs/${id}/`);
    },
    retry(id: string): Promise<AdminJob> {
      return adminRequest(`/jobs/${id}/retry/`, { method: "POST" });
    },
    cancel(id: string): Promise<AdminJob> {
      return adminRequest(`/jobs/${id}/cancel/`, { method: "POST" });
    },
  },
  auditLog: {
    list(params?: {
      action?: string;
      actor?: string;
      target_type?: string;
      page?: number;
    }): Promise<PaginatedResponse<AuditLogEntry>> {
      const search = new URLSearchParams();
      if (params?.action) search.set("action", params.action);
      if (params?.actor) search.set("actor", params.actor);
      if (params?.target_type) search.set("target_type", params.target_type);
      if (params?.page) search.set("page", String(params.page));
      const qs = search.toString();
      return adminRequest(`/audit-log/${qs ? `?${qs}` : ""}`);
    },
  },
  settings: {
    list(): Promise<SystemSetting[]> {
      return adminRequest("/settings/");
    },
    update(settings: Array<{ key: string; value: unknown }>): Promise<SystemSetting[]> {
      return adminRequest("/settings/", { method: "PATCH", body: JSON.stringify(settings) });
    },
  },
  monitoring: {
    current(): Promise<MonitoringSnapshot> {
      return adminRequest("/monitoring/current/");
    },
    history(range: "24h" | "7d" = "24h"): Promise<MonitoringHistoryPoint[]> {
      return adminRequest(`/monitoring/history/?range=${range}`);
    },
    tableStats(): Promise<MonitoringTableStat[]> {
      return adminRequest("/monitoring/table-stats/");
    },
  },
};
