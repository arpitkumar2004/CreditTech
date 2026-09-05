import { Outlet, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import TopNav from "./TopNav";

export default function Layout() {
  const location = useLocation();
  return (
    <div className="min-h-full flex flex-col">
      <TopNav />

      <main className="mx-auto max-w-7xl w-full px-6 lg:px-8 py-8 flex-1">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.22, ease: [0.4, 0, 0.2, 1] }}
          >
            <Outlet />
          </motion.div>
        </AnimatePresence>
      </main>

      <footer className="mx-auto max-w-7xl w-full px-6 lg:px-8 pb-6">
        <div className="glass-soft rounded-full px-4 py-2 text-xs text-muted-foreground flex justify-between">
          <span>CreditTech · rural credit scoring MVP</span>
          <span>DPDP · AA · offline-first</span>
        </div>
      </footer>
    </div>
  );
}
