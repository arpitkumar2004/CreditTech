import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { CheckCircle2, AlertTriangle, WifiOff, RotateCcw, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ingestApi, type SakhiEntryPayload } from "@/lib/api";

const schema = z.object({
  borrower_id: z.string().uuid("Must be a valid UUID"),
  shg_name: z.string().min(2),
  nabard_grade: z.enum(["A", "B", "C", "D"]),
  membership_years: z.coerce.number().min(0).max(50),
  monthly_savings: z.coerce.number().min(0),
  total_savings: z.coerce.number().min(0),
  loans_taken: z.coerce.number().min(0),
  loans_repaid: z.coerce.number().min(0),
  meeting_attendance_pct: z.coerce.number().min(0).max(100),
  land_holding_acres: z.coerce.number().min(0),
  land_ownership: z.enum(["OWN", "LEASE", "SHARE_CROP"]),
  irrigation_access: z.enum(["yes", "no"]),
  crop_type_primary: z.string().min(2),
  estimated_monthly_income: z.coerce.number().min(0),
  created_by: z.string().min(2),
});
type FormValues = z.infer<typeof schema>;

const QUEUE_KEY = "credittech.sakhi.queue.v1";
function queueOffline(payload: SakhiEntryPayload) {
  const raw = localStorage.getItem(QUEUE_KEY);
  const queue: SakhiEntryPayload[] = raw ? JSON.parse(raw) : [];
  queue.push(payload);
  localStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
}

const selectCls =
  "flex h-11 w-full rounded-xl border border-white/70 bg-white/70 backdrop-blur px-3 py-2 text-sm shadow-[inset_0_1px_0_rgba(255,255,255,0.9)] focus:outline-none focus:ring-2 focus:ring-ring/40";

export default function SakhiEntry() {
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<FormValues>({
    defaultValues: { nabard_grade: "A", land_ownership: "OWN", irrigation_access: "yes" },
  });
  const [banner, setBanner] = useState<{ kind: "ok" | "err" | "queued"; text: string } | null>(null);

  const mutation = useMutation({
    mutationFn: (payload: SakhiEntryPayload) => ingestApi.submitSakhiEntry(payload),
    onSuccess: () => { setBanner({ kind: "ok", text: "Entry recorded successfully." }); reset(); },
    onError: (err: Error, payload) => {
      queueOffline(payload);
      setBanner({ kind: "queued", text: `Network unavailable — entry queued locally (${err.message}).` });
    },
  });

  const onSubmit = handleSubmit((raw) => {
    const parsed = schema.safeParse(raw);
    if (!parsed.success) {
      const first = parsed.error.errors[0];
      setBanner({ kind: "err", text: `${first.path.join(".")}: ${first.message}` });
      return;
    }
    const v = parsed.data;
    mutation.mutate({
      borrower_id: v.borrower_id,
      shg_data: {
        shg_name: v.shg_name, nabard_grade: v.nabard_grade,
        membership_years: v.membership_years, monthly_savings: v.monthly_savings,
        total_savings: v.total_savings, loans_taken: v.loans_taken,
        loans_repaid: v.loans_repaid, meeting_attendance_pct: v.meeting_attendance_pct,
      },
      farmer_data: {
        land_holding_acres: v.land_holding_acres, land_ownership: v.land_ownership,
        irrigation_access: v.irrigation_access === "yes",
        crop_type_primary: v.crop_type_primary,
        estimated_monthly_income: v.estimated_monthly_income,
      },
      created_by: v.created_by,
    });
  });

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl sm:text-3xl font-semibold display">New application</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Bank Sakhi · SHG / FPO entry · offline-capable capture with dual-entry reconciliation.
        </p>
      </header>
    <Card>
      <CardHeader className="pb-3">
        <CardTitle>Applicant details</CardTitle>
        <CardDescription>
          If the network is down when you submit, the entry is queued locally and re-uploaded on the next connection.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {banner && (
          <motion.div
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            role="status"
            className={
              "mb-5 rounded-2xl border px-4 py-2.5 text-sm flex items-center gap-2 " +
              (banner.kind === "ok"
                ? "border-emerald-200 bg-emerald-50/80 text-emerald-900"
                : banner.kind === "queued"
                ? "border-amber-200 bg-amber-50/80 text-amber-900"
                : "border-red-200 bg-red-50/80 text-red-900")
            }
          >
            {banner.kind === "ok"
              ? <CheckCircle2 className="h-4 w-4" />
              : banner.kind === "queued"
              ? <WifiOff className="h-4 w-4" />
              : <AlertTriangle className="h-4 w-4" />}
            {banner.text}
          </motion.div>
        )}
        <form onSubmit={onSubmit} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label="Borrower ID (UUID)" error={errors.borrower_id?.message}>
            <Input placeholder="e.g. 5f9e…" {...register("borrower_id", { required: true })} />
          </Field>
          <Field label="Recorded by (Sakhi username)" error={errors.created_by?.message}>
            <Input placeholder="sakhi_user" {...register("created_by", { required: true })} />
          </Field>

          <SectionTitle title="SHG profile" />
          <Field label="SHG name" error={errors.shg_name?.message}>
            <Input {...register("shg_name", { required: true })} />
          </Field>
          <Field label="NABARD grade">
            <select {...register("nabard_grade")} className={selectCls}>
              {["A", "B", "C", "D"].map((g) => <option key={g} value={g}>{g}</option>)}
            </select>
          </Field>
          <Field label="Membership years" error={errors.membership_years?.message}>
            <Input type="number" step="1" {...register("membership_years", { required: true })} />
          </Field>
          <Field label="Monthly savings (₹)" error={errors.monthly_savings?.message}>
            <Input type="number" step="1" {...register("monthly_savings", { required: true })} />
          </Field>
          <Field label="Total savings (₹)" error={errors.total_savings?.message}>
            <Input type="number" step="1" {...register("total_savings", { required: true })} />
          </Field>
          <Field label="Loans taken" error={errors.loans_taken?.message}>
            <Input type="number" step="1" {...register("loans_taken", { required: true })} />
          </Field>
          <Field label="Loans repaid" error={errors.loans_repaid?.message}>
            <Input type="number" step="1" {...register("loans_repaid", { required: true })} />
          </Field>
          <Field label="Meeting attendance %" error={errors.meeting_attendance_pct?.message}>
            <Input type="number" step="1" {...register("meeting_attendance_pct", { required: true })} />
          </Field>

          <SectionTitle title="Farmer profile" />
          <Field label="Land holding (acres)" error={errors.land_holding_acres?.message}>
            <Input type="number" step="0.1" {...register("land_holding_acres", { required: true })} />
          </Field>
          <Field label="Land ownership">
            <select {...register("land_ownership")} className={selectCls}>
              <option value="OWN">Own</option>
              <option value="LEASE">Lease</option>
              <option value="SHARE_CROP">Share-crop</option>
            </select>
          </Field>
          <Field label="Irrigation access">
            <select {...register("irrigation_access")} className={selectCls}>
              <option value="yes">Yes</option>
              <option value="no">No</option>
            </select>
          </Field>
          <Field label="Primary crop" error={errors.crop_type_primary?.message}>
            <Input placeholder="Cotton, Wheat, …" {...register("crop_type_primary", { required: true })} />
          </Field>
          <Field label="Estimated monthly income (₹)" error={errors.estimated_monthly_income?.message}>
            <Input type="number" step="1" {...register("estimated_monthly_income", { required: true })} />
          </Field>

          <div className="col-span-full flex flex-wrap gap-3 pt-4">
            <Button type="submit" size="lg" disabled={isSubmitting || mutation.isPending}>
              <Send className="h-4 w-4" />
              {mutation.isPending ? "Submitting…" : "Submit entry"}
            </Button>
            <Button type="button" size="lg" variant="outline" onClick={() => reset()}>
              <RotateCcw className="h-4 w-4" /> Reset
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
    </div>
  );
}

function Field({ label, children, error }: { label: string; children: React.ReactNode; error?: string }) {
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      {children}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
function SectionTitle({ title }: { title: string }) {
  return <h3 className="col-span-full mt-3 text-xs uppercase tracking-widest text-muted-foreground">{title}</h3>;
}
