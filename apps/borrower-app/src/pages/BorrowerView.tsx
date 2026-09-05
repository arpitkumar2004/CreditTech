import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Loader2, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ingestApi } from "@/lib/api";

export default function BorrowerView() {
  const [borrowerId, setBorrowerId] = useState("");
  const trigger = useMutation({ mutationFn: (id: string) => ingestApi.triggerAggregation(id) });

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl sm:text-3xl font-semibold display">Borrower aggregation</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Run the four-rail ingestion (AA · Geospatial · Bureau · SHG / FPO) and inspect the resulting feature snapshot.
        </p>
      </header>
      <Card>
        <CardHeader>
          <CardTitle>Trigger aggregation</CardTitle>
          <CardDescription>
            Enter the borrower UUID to fetch the latest sources and materialise a feature snapshot.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-[1fr,auto] gap-3 items-end">
            <div className="space-y-1.5">
              <Label htmlFor="bid">Borrower ID</Label>
              <Input id="bid" value={borrowerId} onChange={(e) => setBorrowerId(e.target.value)} placeholder="UUID" />
            </div>
            <Button size="lg" onClick={() => trigger.mutate(borrowerId)} disabled={!borrowerId || trigger.isPending}>
              {trigger.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
              Aggregate
            </Button>
          </div>

          {trigger.isError && (
            <p className="text-sm text-destructive">{(trigger.error as Error).message}</p>
          )}

          {trigger.data && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-soft rounded-2xl p-4 space-y-3"
            >
              <div className="flex items-center gap-2 text-sm">
                <span className="text-muted-foreground">Overall status</span>
                <StatusPill status={trigger.data.overall_status} />
              </div>
              <p className="text-xs text-muted-foreground">
                snapshot_id: <code>{trigger.data.feature_snapshot_id ?? "—"}</code>
              </p>
              <pre className="text-xs bg-white/80 border rounded-xl p-3 overflow-x-auto">
                {JSON.stringify(trigger.data.sources, null, 2)}
              </pre>
            </motion.div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const map: Record<string, string> = {
    SUCCESS: "bg-emerald-100 text-emerald-900 border-emerald-300",
    PARTIAL: "bg-amber-100 text-amber-900 border-amber-300",
    FAILED: "bg-red-100 text-red-900 border-red-300",
  };
  return (
    <span className={"inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium " + (map[status] ?? "bg-secondary")}>
      {status}
    </span>
  );
}
