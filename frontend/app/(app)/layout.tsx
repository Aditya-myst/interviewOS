import AppShell from "@/components/shell/AppShell";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppShell targetRole="Senior SWE">{children}</AppShell>;
}
