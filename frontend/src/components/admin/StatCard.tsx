export function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="admin-stat-card">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
    </div>
  );
}
