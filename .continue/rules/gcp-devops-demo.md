---
name: GCP DevOps Demo Rules
description: Reglas del proyecto gcp-devops-gitops-demo
alwaysApply: true
---
- Coste 0 EUR en GCP Always Free (Cloud Run, Artifact Registry, IAM y bucket GCS en US para tfstate). GKE Autopilot y VPC solo validación estática (terraform fmt y terraform validate), nunca apply en nube.
- Cero secretos, tokens ni .tfstate en Git. IAM mínimo privilegio y Docker no-root.
- Trabajar estrictamente tarjeta a tarjeta según docs/SPRINT_PLAN.md sin adelantarse.