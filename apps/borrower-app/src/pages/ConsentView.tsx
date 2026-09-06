import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { ShieldCheck, ShieldX, Loader2, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { consentApi, type ConsentSummary } from "@/lib/api";
import { useToast } from "@/components/ui/toast";

export default function ConsentView() {
  const { toast } = useToast();
  const [consentId, setConsentId] = useState("");
  const [detail, setDetail] = useState<ConsentSummary | null>(null);

  const load = useMutation({
    mutationFn: (id: string) => consentApi.get(id),
    onSuccess: (d) => {
      setDetail(d);
      toast({ variant: "success", title: "Consent record loaded", description: `Purpose: ${d.purpose}` });
    },
    onError: (err: any) => {
      setDetail(null);
      toast({ variant: "error", title: "Record not found", description: err?.message || "Invalid or missing consent ID." });
    },
  });
  const verify = useMutation({
    mutationFn: (id: string) => consentApi.verify(id),
    onSuccess: (d) => {
      toast({
        variant: d.valid ? "success" : "error",
        title: d.valid ? "Integrity verified" : "Integrity check failed",
        description: d.valid ? "SHA-256 hash chain is intact." : (d.reason ?? "Chain mismatch detected."),
      });
    },
    onError: (err: any) => {
      toast({ variant: "error", title: "Verification failed", description: err?.message || "Could not verify chain." });
    },
  });

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl sm:text-3xl font-semibold display">Consent</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Look up a hash-chained consent record and verify its integrity end-to-end (ADR-6).
        </p>
      </header>
      <Card>
      <CardHeader>
        <CardTitle>Lookup</CardTitle>
        <CardDescription>
          Provide the consent UUID to fetch the record and validate its chain.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid grid-cols-1 sm:grid-cols-[1fr,auto,auto] gap-2 items-end">
          <div className="space-y-1.5">
            <Label htmlFor="cid">Consent ID</Label>
            <Input id="cid" value={consentId} onChange={(e) => setConsentId(e.target.value)} placeholder="UUID" />
          </div>
          <Button size="lg" onClick={() => load.mutate(consentId)} disabled={!consentId || load.isPending}>
            {load.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
            Load
          </Button>
          <Button size="lg" variant="outline" onClick={() => verify.mutate(consentId)} disabled={!consentId || verify.isPending}>
            {verify.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
            Verify chain
          </Button>
        </div>

        {verify.data && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className={
              "flex items-center gap-2 rounded-2xl border px-4 py-2.5 text-sm " +
              (verify.data.valid
                ? "border-emerald-200 bg-emerald-50/80 text-emerald-900"
                : "border-red-200 bg-red-50/80 text-red-900")
            }
          >
            {verify.data.valid ? <ShieldCheck className="h-4 w-4" /> : <ShieldX className="h-4 w-4" />}
            {verify.data.valid ? "Chain valid" : `Chain invalid — ${verify.data.reason ?? "unknown"}`}
          </motion.div>
        )}

        {detail && (
          <motion.dl
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 rounded-2xl border p-4 glass-soft text-sm"
          >
            <Field k="Purpose" v={detail.purpose} />
            <Field k="Status" v={detail.status} />
            <Field k="Data sources" v={detail.data_sources.join(", ")} />
            <Field k="Issued" v={new Date(detail.issued_at).toLocaleString()} />
            <Field k="Expires" v={new Date(detail.expires_at).toLocaleString()} />
            <Field k="Borrower" v={detail.borrower_id} mono />
          </motion.dl>
        )}
      </CardContent>
    </Card>
    </div>
  );
}

function Field({ k, v, mono }: { k: string; v: string; mono?: boolean }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wider text-muted-foreground">{k}</dt>
      <dd className={mono ? "font-mono text-xs break-all mt-0.5" : "mt-0.5"}>{v}</dd>
    </div>
  );
}
