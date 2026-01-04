import { AppRouter } from "@/router";

export default function App() {
  return (
    <div className="h-screen bg-background text-foreground font-sans antialiased">
      <AppRouter />
    </div>
  );
}
