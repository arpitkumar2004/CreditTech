"""Loan officer decisioning module (Phase 4).

Human-in-the-loop review + capture of approve/reject/more-info decisions on
scored loan applications, plus the append-only audit trail. The RE handoff
consumes decisions from this module — CreditTech does not auto-decide.
"""
