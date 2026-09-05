import { describe, expect, it } from "vitest";
import { isOverride, validateDecisionForm } from "@/lib/decisionLogic";

describe("isOverride", () => {
  it("APPROVE + APPROVED is not an override", () => {
    expect(isOverride("APPROVED", "APPROVE")).toBe(false);
  });
  it("APPROVE + REJECTED is an override", () => {
    expect(isOverride("REJECTED", "APPROVE")).toBe(true);
  });
  it("REJECT + APPROVED is an override", () => {
    expect(isOverride("APPROVED", "REJECT")).toBe(true);
  });
  it("REVIEW + any choice is not an override", () => {
    expect(isOverride("APPROVED", "REVIEW")).toBe(false);
    expect(isOverride("REJECTED", "REVIEW")).toBe(false);
    expect(isOverride("MORE_INFO_REQUIRED", "REVIEW")).toBe(false);
  });
});

describe("validateDecisionForm", () => {
  it("rejects missing decision", () => {
    expect(validateDecisionForm(null, "APPROVE", "")).toMatch(/Select a decision/);
  });
  it("requires override reason when overriding", () => {
    expect(validateDecisionForm("REJECTED", "APPROVE", "")).toMatch(/Override reason/);
  });
  it("rejects an override reason when not overriding", () => {
    expect(validateDecisionForm("APPROVED", "APPROVE", "not needed")).toMatch(/Remove/);
  });
  it("passes valid override", () => {
    expect(validateDecisionForm("REJECTED", "APPROVE", "credible reason")).toBeNull();
  });
  it("passes matching decision without reason", () => {
    expect(validateDecisionForm("APPROVED", "APPROVE", "")).toBeNull();
  });
});
