
# CreditTech Infrastructure (IaC baseline)

Terraform baseline for the CreditTech pilot. Deliberately small — one managed
container service, one managed Postgres, one object-storage bucket, all in an
India region (ADR-5).

Layout:

```
infra/
  modules/
    network/         # VPC, subnets, security groups
    database/        # Managed Postgres (RDS/CloudSQL equivalent)
    container_app/   # Managed container runtime (ECS Fargate / Cloud Run)
    storage/         # Object storage bucket for artefacts + consent PDFs
  envs/
    staging/         # Staging environment composition
    production/      # Production environment composition
```

## Assumptions (see Credittechplanningcontext.md §5 ADR-5)

- Single managed public cloud, India region (`ap-south-1` shown as the example).
- Managed containers, **not Kubernetes**.
- Managed Postgres, single instance for the pilot (read replica added at ~10K
  borrowers per §7.2).
- State stored in a remote backend (S3 + DynamoDB lock, or GCS + IAM equivalent)
  — configure `backend.tf` per environment before first `terraform init`.

## Bootstrap

```bash
cd infra/envs/staging
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

Real cloud credentials are **not** committed. Provider auth uses environment
variables or the CI job's OIDC role. Do not run `terraform apply` from a
workstation without an explicit Phase-0 sign-off on the target account.

## Status

This is a **scaffold** — enough structure to satisfy the Phase 1 DoD
("cloud accounts + IaC baseline") and to give the CI pipeline something to
`terraform plan` against. Actual resource wiring is deferred to Phase 6/7
when production accounts and RE-agreed hosting are locked in.
