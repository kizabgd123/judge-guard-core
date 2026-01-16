---
title: Agent Taming
objective: Implement advanced control and verification mechanisms for AI agents (Chain of Truth, Drift Score, Self-Healing).
status: ACTIVE
---

# 🎯 Agent Taming Skill

## Core Patterns

1. **Chain of Truth (CoT) Loop:** deterministic browser interaction.
2. **Semantic Drift Score:** measuring deviation from project essence.
3. **Self-Healing Loop:** Actor-Judge feedback cycle for autonomous correction.

## Verification

- Use `judge_guard.py` for all major actions.
- Minimum Drift Score threshold: < 0.4.
- Mandatory transition: Phase n -> Phase n+1 via JudgeGuard.
