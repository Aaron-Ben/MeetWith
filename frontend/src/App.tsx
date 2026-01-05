import { AppRouter } from "@/router";
import { ThemeProvider } from "@/contexts/ThemeContext";

export default function App() {
  return (
    <ThemeProvider>
      <div className="h-screen bg-background text-foreground font-sans antialiased">
        <AppRouter />
      </div>
    </ThemeProvider>
  );
}
