import { lazy, Suspense } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import "./styles/tokens.css";
import "./styles/components.css";
import "./styles/layout.css";
import "./styles/admin.css";
import { Header } from "./components/Header";
import { LeaderboardPage } from "./pages/LeaderboardPage";
import { LoginPage } from "./pages/LoginPage";
import { PracticePage } from "./pages/PracticePage";
import { ProgressPage } from "./pages/ProgressPage";
import { SettingsPage as UserSettingsPage } from "./pages/SettingsPage";
import { WordPracticePage } from "./pages/WordPracticePage";
import { AdminRoute } from "./components/admin/AdminRoute";

const AdminLayout = lazy(() =>
  import("./pages/admin/AdminLayout").then((m) => ({ default: m.AdminLayout }))
);
const DashboardPage = lazy(() =>
  import("./pages/admin/DashboardPage").then((m) => ({ default: m.DashboardPage }))
);
const UsersPage = lazy(() =>
  import("./pages/admin/UsersPage").then((m) => ({ default: m.UsersPage }))
);
const UserDetailPage = lazy(() =>
  import("./pages/admin/UserDetailPage").then((m) => ({ default: m.UserDetailPage }))
);
const ContentPage = lazy(() =>
  import("./pages/admin/ContentPage").then((m) => ({ default: m.ContentPage }))
);
const AnalyticsPage = lazy(() =>
  import("./pages/admin/AnalyticsPage").then((m) => ({ default: m.AnalyticsPage }))
);
const JobsPage = lazy(() =>
  import("./pages/admin/JobsPage").then((m) => ({ default: m.JobsPage }))
);
const AuditLogPage = lazy(() =>
  import("./pages/admin/AuditLogPage").then((m) => ({ default: m.AuditLogPage }))
);
const SettingsPage = lazy(() =>
  import("./pages/admin/SettingsPage").then((m) => ({ default: m.SettingsPage }))
);

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/admin/*"
          element={
            <AdminRoute>
              <Suspense fallback={<div style={{ padding: 24 }}>Loading...</div>}>
                <Routes>
                  <Route element={<AdminLayout />}>
                    <Route index element={<DashboardPage />} />
                    <Route path="users" element={<UsersPage />} />
                    <Route path="users/:id" element={<UserDetailPage />} />
                    <Route path="content" element={<ContentPage />} />
                    <Route path="analytics" element={<AnalyticsPage />} />
                    <Route path="jobs" element={<JobsPage />} />
                    <Route path="audit-log" element={<AuditLogPage />} />
                    <Route path="settings" element={<SettingsPage />} />
                  </Route>
                </Routes>
              </Suspense>
            </AdminRoute>
          }
        />
        <Route
          path="*"
          element={
            <>
              <Header />
              <Routes>
                <Route path="/" element={<PracticePage />} />
                <Route path="/words" element={<WordPracticePage />} />
                <Route path="/progress" element={<ProgressPage />} />
                <Route path="/leaderboard" element={<LeaderboardPage />} />
                <Route path="/login" element={<LoginPage />} />
                <Route path="/settings" element={<UserSettingsPage />} />
              </Routes>
            </>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
