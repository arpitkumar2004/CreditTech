import React, { useState } from "react";
import {
  CheckCircle2,
  Clock,
  ArrowRight,
  Languages,
  Sparkles,
} from "lucide-react";

interface RecourseStep {
  step: number;
  title_en: string;
  title_hi: string;
  points: number;
  status: "COMPLETED" | "IN_PROGRESS" | "NEXT";
  estimated_days: number;
  action_desc: string;
}

interface RecourseLadderProps {
  data?: {
    current_score?: number;
    current_band?: string;
    confidence_range?: number[];
    target_score?: number;
    target_band?: string;
    points_needed?: number;
  };
  steps?: RecourseStep[];
  className?: string;
}

export const RecourseLadderPlot: React.FC<RecourseLadderProps> = ({
  data,
  steps,
  className = "",
}) => {
  const [lang, setLang] = useState<"en" | "hi">("en");

  const currentScore = data?.current_score ?? 582;
  const targetScore = data?.target_score ?? 650;
  const pointsNeeded = Math.max(0, targetScore - currentScore);

  const defaultSteps: RecourseStep[] = [
    {
      step: 1,
      title_en: "3 Consecutive On-Time SHG Meetings",
      title_hi: "लगातार 3 स्वयं सहायता समूह बैठकों में समय पर उपस्थिति",
      points: 25,
      status: "COMPLETED",
      estimated_days: 30,
      action_desc: "Attend weekly SHG meetings and make timely peer-group savings deposits.",
    },
    {
      step: 2,
      title_en: "Pay Electricity Utility Bill Within 7 Days",
      title_hi: "बिजली बिल जारी होने के 7 दिनों के भीतर भुगतान करें",
      points: 35,
      status: "IN_PROGRESS",
      estimated_days: 45,
      action_desc: "Demonstrates consistent household utility discipline without overdue notices.",
    },
    {
      step: 3,
      title_en: "Log 2 Crop Harvest Sales Digitally via e-NAM / Sakhi",
      title_hi: "ई-नाम या बैंक सखी के माध्यम से 2 फसल बिक्री डिजिटल दर्ज करें",
      points: 40,
      status: "NEXT",
      estimated_days: 90,
      action_desc: "Builds verified agri-cashflow history replacing informal paper receipts.",
    },
  ];

  const activeSteps = steps && steps.length > 0 ? steps : defaultSteps;

  const progressPct = Math.min(100, Math.round(((currentScore - 300) / (targetScore - 300)) * 100));

  return (
    <div className={`rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm hover:shadow-md transition-shadow ${className}`}>
      {/* Header */}
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-slate-900">
              {lang === "en" ? "Actionable Score Recourse Ladder" : "सुधार एवं स्कोर प्रगति सीढ़ी"}
            </h3>
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-200">
              <Sparkles className="h-3.5 w-3.5 text-emerald-600" />
              {lang === "en" ? "Clear Path to 650+" : "650+ स्कोर का आसान मार्ग"}
            </span>
          </div>
          <p className="mt-0.5 text-xs text-slate-500">
            {lang === "en"
              ? "Every credit decision is backed by transparent, achievable milestones to unlock straight-through lending."
              : "हर ऋण निर्णय पारदर्शी कदमों से समर्थित है ताकि आप सीधे स्वचालित ऋण स्वीकृति प्राप्त कर सकें।"}
          </p>
        </div>

        {/* Language switch */}
        <button
          onClick={() => setLang(lang === "en" ? "hi" : "en")}
          className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:bg-slate-100 hover:border-slate-300"
        >
          <Languages className="h-3.5 w-3.5 text-blue-600" />
          <span>{lang === "en" ? "हिंदी में देखें" : "View in English"}</span>
        </button>
      </div>

      {/* Score Progress Bar */}
      <div className="mb-6 rounded-xl border border-slate-200/80 bg-slate-50/80 p-4">
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
          <div>
            <span className="text-slate-500">{lang === "en" ? "Current Score: " : "वर्तमान स्कोर: "}</span>
            <span className="font-mono text-lg font-bold text-amber-600">{currentScore}</span>
            <span className="ml-1 text-slate-400">/ 900</span>
          </div>
          <div>
            <span className="text-slate-500">{lang === "en" ? "Target Pre-Approved: " : "लक्ष्य (स्वीकृत): "}</span>
            <span className="font-mono text-lg font-bold text-emerald-700">{targetScore}</span>
            <span className="ml-2 rounded bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-800">
              {lang === "en" ? `+${pointsNeeded} pts needed` : `+${pointsNeeded} अंक शेष`}
            </span>
          </div>
        </div>

        {/* Meter bar */}
        <div className="mt-3 relative h-3 w-full overflow-hidden rounded-full bg-slate-200">
          <div
            className="h-full bg-gradient-to-r from-amber-500 to-emerald-600 transition-all duration-500"
            style={{ width: `${progressPct}%` }}
          />
        </div>
        <div className="mt-1.5 flex justify-between text-[11px] text-slate-500">
          <span>300 (Base)</span>
          <span className="text-amber-700 font-medium">550 (Review Band)</span>
          <span className="text-emerald-700 font-semibold">650 (STP Pass)</span>
          <span>900 (Max)</span>
        </div>
      </div>

      {/* Stepper Cards */}
      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        {activeSteps.map((step) => {
          const isCompleted = step.status === "COMPLETED";
          const isInProgress = step.status === "IN_PROGRESS";

          return (
            <div
              key={step.step}
              className={`relative flex flex-col justify-between rounded-xl border p-4 transition ${
                isCompleted
                  ? "border-emerald-200 bg-emerald-50/50 hover:bg-emerald-50/80"
                  : isInProgress
                  ? "border-amber-200 bg-amber-50/50 shadow-sm ring-1 ring-amber-200 hover:bg-amber-50/80"
                  : "border-slate-200 bg-slate-50/40 hover:bg-slate-50/70"
              }`}
            >
              <div>
                <div className="flex items-center justify-between">
                  <span
                    className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                      isCompleted
                        ? "bg-emerald-100 text-emerald-800"
                        : isInProgress
                        ? "bg-amber-100 text-amber-800"
                        : "bg-slate-200 text-slate-700"
                    }`}
                  >
                    {isCompleted && <CheckCircle2 className="h-3 w-3 text-emerald-600" />}
                    {isInProgress && <Clock className="h-3 w-3 text-amber-600" />}
                    {isCompleted
                      ? lang === "en" ? "Completed" : "पूर्ण"
                      : isInProgress
                      ? lang === "en" ? "In Progress" : "प्रगति पर"
                      : lang === "en" ? "Next Step" : "अगला कदम"}
                  </span>
                  <span className="font-mono text-sm font-bold text-emerald-700">
                    +{step.points} {lang === "en" ? "pts" : "अंक"}
                  </span>
                </div>

                <h4 className="mt-2.5 text-sm font-semibold text-slate-900">
                  {lang === "en" ? step.title_en : step.title_hi}
                </h4>
                <p className="mt-1 text-xs text-slate-600 leading-relaxed">
                  {step.action_desc}
                </p>
              </div>

              <div className="mt-4 flex items-center justify-between border-t border-slate-200/60 pt-2.5 text-[11px] text-slate-500">
                <span>{lang === "en" ? `Est. ${step.estimated_days} days` : `अनुमानित ${step.estimated_days} दिन`}</span>
                <span className="flex items-center gap-1 text-blue-700 font-semibold">
                  {lang === "en" ? "Step " : "चरण "} {step.step} <ArrowRight className="h-3 w-3" />
                </span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 rounded-xl bg-slate-50 p-3.5 text-xs text-slate-700 border border-slate-200/80">
        <span className="font-semibold text-emerald-800">
          {lang === "en" ? "Dignity & Agency Guarantee: " : "सम्मान एवं अधिकार की गारंटी: "}
        </span>
        {lang === "en"
          ? "Unlike opaque black-box credit algorithms, CreditTech guarantees that completing these three steps mathematically qualifies the borrower for automated pre-approval."
          : "पारंपरिक जटिल ऋण प्रणालियों के विपरीत, क्रेडिट-टेक यह सुनिश्चित करता है कि इन तीन कदमों को पूरा करने पर आपका ऋण बिना किसी बाधा के स्वतः स्वीकृत हो जाएगा।"}
      </div>
    </div>
  );
};
