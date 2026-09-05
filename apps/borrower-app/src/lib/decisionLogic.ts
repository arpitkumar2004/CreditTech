import type { ModelRecommendation, OfficerDecision } from "./types";

/** Mirrors services/core/decisioning/service.is_override — keep in sync. */
export function isOverride(
  decision: OfficerDecision,
  recommendation: ModelRecommendation,
): boolean {
  if (recommendation === "REVIEW") return false;
  if (recommendation === "APPROVE") return decision !== "APPROVED";
  return decision !== "REJECTED";
}

export function validateDecisionForm(
  decision: OfficerDecision | null,
  recommendation: ModelRecommendation,
  overrideReason: string | null,
): string | null {
  if (!decision) return "Select a decision";
  const override = isOverride(decision, recommendation);
  const reason = (overrideReason ?? "").trim();
  if (override && !reason) {
    return `Override reason required — your decision (${decision}) differs from model recommendation (${recommendation}).`;
  }
  if (!override && reason) {
    return "Remove the override reason — your decision matches the model recommendation.";
  }
  return null;
}
