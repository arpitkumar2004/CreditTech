import { Link } from "react-router-dom";
import { Home, Search } from "lucide-react";

/**
 * 404 Not Found page — shown when no route matches the current URL.
 */
export default function NotFound() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center p-6">
      <div className="glass rounded-3xl p-10 max-w-lg text-center space-y-5">
        <div className="mx-auto w-20 h-20 rounded-full bg-violet-500/10 flex items-center justify-center">
          <Search className="h-10 w-10 text-violet-400" />
        </div>
        <h1 className="text-5xl font-bold text-violet-400">404</h1>
        <h2 className="text-xl font-semibold">Page not found</h2>
        <p className="text-sm text-muted-foreground max-w-xs mx-auto">
          The page you&apos;re looking for doesn&apos;t exist or has been moved. Check the URL or
          head back to the dashboard.
        </p>
        <Link to="/" className="pill inline-flex items-center gap-2">
          <Home className="h-4 w-4" /> Back to Dashboard
        </Link>
      </div>
    </div>
  );
}
