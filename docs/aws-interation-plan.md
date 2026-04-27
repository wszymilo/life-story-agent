# AWS Integration Plan: Life Story Preservation Agent

## Objective

Transition the Life Story Preservation Agent from its current PaaS stack (Vercel/Railway/Supabase) to a self-managed Terraform-controlled AWS environment in `eu-west-1`. Minimize monthly fixed costs while maintaining voice-first interaction patterns required for the elderly target demographic.

**Start from scratch** - no data migration from Supabase needed.

---

## Architecture Overview

| Layer | Component | Status | Notes |
|-------|-----------|--------|-------|
| Backend | AWS ECS Express Mode | ✅ Complete | FastAPI container on Fargate |
| Frontend | S3 + CloudFront | ✅ Complete | CDN with OAC |
| Database | Aurora Serverless v2 | ✅ Complete | PostgreSQL 16.4, Auto-Pause enabled |
| Auth | Amazon Cognito | ✅ Complete | Password auth (magic link deferred) |
| Storage | S3 | ✅ Complete | Audio + frontend buckets |
| IaC | Terraform (S3/DynamoDB backend) | ✅ Complete | All resources provisioned |

---

## Key Technical Decisions

1. **Region**: `eu-west-1` (Ireland)
2. **Magic Link Auth**: Deferred - Cognito password auth only
3. **Database**: Aurora Serverless v2 with PostgreSQL 16.4, min 0 ACU, Auto-Pause enabled
4. **Networking**: VPC with 2 public subnets (ALB) + 2 private subnets (RDS/ECS)
5. **Terraform State**: S3 bucket + DynamoDB table (`life-story-terraform-lock`)
6. **Backend Container**: Docker image pushed to ECR, deployed via ECS Express Mode
7. **Frontend CI/CD**: GitHub Action to build and upload to S3 + CloudFront invalidation

---

## Infrastructure Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS Region: eu-west-1                     │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                      VPC (10.0.0.0/16)                   │    │
│  │                                                           │    │
│  │  ┌─────────────────────┐    ┌─────────────────────────┐   │    │
│  │  │  Public Subnet A    │    │   Private Subnet A      │   │    │
│  │  │  (10.0.1.0/24)      │    │   (10.0.11.0/24)        │   │    │
│  │  │                      │    │                         │   │    │
│  │  │  • ALB              │    │   • ECS Tasks (Fargate)  │   │    │
│  │  │  • Internet Gateway │    │   • Aurora Cluster       │   │    │
│  │  └─────────────────────┘    └─────────────────────────┘   │    │
│  │                                                           │    │
│  │  ┌─────────────────────┐    ┌─────────────────────────┐   │    │
│  │  │  Public Subnet B    │    │   Private Subnet B       │   │    │
│  │  │  (10.0.2.0/24)      │    │   (10.0.12.0/24)        │   │    │
│  │  └─────────────────────┘    └─────────────────────────┘   │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────────────┐   │
│  │  CloudFront  │  │     S3        │  │      Cognito         │   │
│  │  (CDN)       │  │  • audio-     │  │  • User Pool         │   │
│  │              │  │    recordings │  │  • App Client        │   │
│  │              │  │  • terraform │  │                      │   │
│  │              │  │    state     │  │                      │   │
│  │              │  │  • frontend  │  │                      │   │
│  └───────────────┘  └───────────────┘  └─────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    ECS Express Mode                     │    │
│  │  • FastAPI Container (Fargate)                           │    │
│  │  • ALB Target Group                                     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Aurora Serverless v2 (PostgreSQL 16.4)      │    │
│  │  • Auto-Pause enabled (5-15s wake-up)                     │    │
│  │  • Min capacity: 0 ACU                                   │    │
│  │  • Max capacity: 4 ACU                                  │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Terraform Structure

```
terraform/
├── main.tf              # All AWS resources
├── variables.tf        # Input variables (configurable)
├── providers.tf        # Provider configuration
├── versions.tf        # Version constraints
└── backend.tf         # S3/DynamoDB state backend
```

### Resources Provisioned

| Resource | Status |
|----------|--------|
| `aws_vpc` | ✅ |
| `aws_subnet` (x4) | ✅ |
| `aws_internet_gateway` | ✅ |
| `aws_nat_gateway` (x2) | ✅ |
| `aws_route_table` (x4) | ✅ |
| `aws_db_subnet_group` | ✅ |
| `aws_rds_cluster` | ✅ |
| `aws_rds_cluster_instance` | ✅ |
| `aws_cognito_user_pool` | ✅ |
| `aws_cognito_user_pool_client` | ✅ |
| `aws_cognito_identity_pool` | ✅ |
| `aws_ecr_repository` | ✅ |
| `aws_ecs_cluster` | ✅ |
| `aws_ecs_task_definition` | ✅ |
| `aws_ecs_service` | ✅ |
| `aws_lb` | ✅ |
| `aws_lb_target_group` | ✅ |
| `aws_lb_listener` | ✅ |
| `aws_security_group` (x3) | ✅ |
| `aws_s3_bucket` (x2) | ✅ |
| `aws_cloudfront_distribution` | ✅ |
| `aws_cloudfront_origin_access_control` | ✅ |
| `aws_iam_role` (x2) | ✅ |
| `aws_iam_policy` | ✅ |
| `aws_secretsmanager_secret` | ✅ |
| `aws_ssm_parameter` (x2) | ✅ |
| `aws_cloudwatch_log_group` | ✅ |

---

## GitHub Actions Workflows

### 1. `terraform.yml` - Terraform Infrastructure CI/CD ✅

- **Trigger**: Manual only (`workflow_dispatch`)
- **Parameters**: `action` (plan/apply/destroy)
- **Features**:
  - Auto-sets GitHub Variables on apply (via GitHub API curl)
  - Auto-clears GitHub Variables on destroy
  - Auto-cleans Secrets Manager pending deletions on destroy
  - Terraform init → fmt → validate → plan/apply/destroy
- **Secrets Required**: `GH_PAT` (Classic PAT with repo scope)

### 2. `backend.yml` - Backend Deployment

- **Trigger**: Manual only (`workflow_dispatch`)
- **Features**:
  - Build Docker image from `aws/` directory
  - Push to ECR
  - Force new ECS deployment
  - Health check verification via ALB URL from GitHub variables
- **Variables Used**: `ECR_REPOSITORY_URL`, `ECS_CLUSTER_NAME`, `ECS_SERVICE_NAME`, `FRONTEND_API_URL`

### 3. `frontend.yml` - Frontend Build & Deploy

- **Trigger**: Manual only (`workflow_dispatch`)
- **Features**:
  - npm install + lint + typecheck + build
  - Upload to S3 frontend bucket
  - CloudFront invalidation
- **Variables Used**: `FRONTEND_BUCKET`, `CF_DISTRIBUTION_ID`

---

## Migration Phases

### Phase 1: Infrastructure Provisioning ✅

**Status:** COMPLETE

**Completed Tasks:**
- [x] Initialize Terraform with S3/DynamoDB backend
- [x] Create VPC with public/private subnets
- [x] Provision Aurora Serverless v2 cluster (PostgreSQL 16.4, min 0 ACU, Auto-Pause)
- [x] Create Cognito User Pool (password auth initially)
- [x] Configure ALB + ECS Express Mode for FastAPI
- [x] Create S3 buckets (audio, frontend, terraform state)
- [x] Set up CloudFront distribution with OAC for frontend bucket

**Output Values:** (available as GitHub Variables after terraform apply)
```
FRONTEND_API_URL     = http://[alb-dns-name].elb.amazonaws.com
CLOUDFRONT_URL       = https://[cloudfront-distribution].cloudfront.net
COGNITO_USER_POOL_ID = eu-west-1_[pool-id]
COGNITO_CLIENT_ID    = [client-id]
AURORA_ENDPOINT      = [cluster-endpoint].rds.amazonaws.com
AUDIO_BUCKET         = life-story-agent-audio
ECR_REPOSITORY_URL   = [account-id].dkr.ecr.eu-west-1.amazonaws.com/life-story-agent/fastapi
ECS_CLUSTER_NAME     = life-story-agent-cluster
ECS_SERVICE_NAME    = life-story-agent-fastapi-service
FRONTEND_BUCKET      = life-story-agent-frontend
CF_DISTRIBUTION_ID   = [cloudfront-id]
SSM_PARAMETER_PATH   = /life-story-agent
```

---

### Phase 2: Containerization & Backend Deployment

**Status:** ✅ COMPLETE

**Completed Tasks:**
- [x] Create `Dockerfile` for FastAPI application (CMD: `uv run uvicorn`)
- [x] Replace Supabase SDK → asyncpg (via db/query.py)
- [x] Replace Supabase storage → boto3 S3 (via services/storage.py)
- [x] Replace Supabase auth → Cognito JWT (via api/deps.py)
- [x] Update config.py with AWS environment variables
- [x] Add explicit user_id filtering in routes (no more Supabase RLS)
- [x] Push image to ECR (via backend.yml workflow)
- [x] Deploy container via ECS Express Mode
- [x] Verify: ALB health check returns `{"status":"ok"}`

**Note:** Auto-seed on startup NOT implemented - user creation handled in `api/deps.py` on first Cognito login

---

### Phase 3: Frontend & CDN

**Status:** NOT STARTED

**Note:** Frontend not yet deployed - waiting for backend verification complete

**Tasks:**
- [ ] Build: `npm run build`
- [ ] Upload to S3 frontend bucket
- [ ] Create CloudFront invalidation GitHub Action
- [ ] Update PWA manifest/service workers for new CloudFront URL

**Frontend .env changes needed:**
```
VITE_API_URL=https://[cloudfront-distribution].cloudfront.net
VITE_COGNITO_REGION=eu-west-1
VITE_COGNITO_USER_POOL_ID=[from terraform output]
VITE_COGNITO_CLIENT_ID=[from terraform output]
```

---

### Phase 4: Database Schema & Seed

**Status:** ✅ SCHEMA COMPLETE, AUTO-SEED NOT IMPLEMENTED

**Completed Tasks:**
- [x] Extract schema from Supabase migrations (`supabase/migrations/001_aurora_schema.sql`)
- [x] Add DB backup step to `terraform.yml` (runs before destroy)

**Design Decision:**
- Schema auto-seed on startup NOT implemented
- User creation handled in `api/deps.py` on first Cognito login (auto-insert to users table)
- Schema must exist in Aurora before first deployment (via direct DB connection or Terraform)

---

## IAM Permissions for aiengineer User

**Status:** Configured via inline policy (custom consolidated policy)

The aiengineer user has a consolidated custom policy with permissions for:
- EC2/VPC (networking)
- ECS/Ecr
- RDS/Aurora
- Cognito
- S3
- CloudFront
- DynamoDB
- IAM
- CloudWatch Logs
- Lambda
- SSM
- Application Autoscaling
- ELB

---

## Cost Estimate (Monthly)

| Service | Estimated Cost |
|---------|----------------|
| ALB | ~$16.00 |
| ECS Express Mode (Fargate) | ~$5-10 (light usage) |
| Aurora Serverless (scale-to-zero) | ~$0-5 (idle) |
| S3 (audio + frontend) | ~$1-5 |
| CloudFront | ~$0-5 (1TB free tier) |
| NAT Gateway | ~$0 |
| **Total** | **~$22-41/month** |

---

## Next Steps (Priority Order)

### 1. Deploy Frontend (Phase 3) 🔜 CURRENT
- Trigger `frontend.yml` workflow (GitHub → Actions → Deploy Frontend → Run workflow)
- Workflow builds with Cognito env vars from GitHub Variables
- Uploads to S3 and invalidates CloudFront

### 2. Verify End-to-End Flow
- Test user registration/login via Cognito
- Test audio recording upload to S3
- Test story generation with OpenAI

### 3. (Optional) Implement Auto-seed on Startup
- Currently user creation is handled in `api/deps.py` on first login
- If schema must exist before first deployment, implement auto-seed in `main.py`

---

## Troubleshooting Notes

- **App Runner**: Not applicable - using ECS Express Mode
- **Aurora Cold Starts**: Frontend must handle 5-15 second timeout during database "wake-up"
- **ECS Express Mode**: Task execution role has ECR pull permissions
- **CloudFront OAC**: Using Origin Access Control (OAC) for S3 bucket access
- **Dockerfile Location**: `aws/Dockerfile` (not root) to avoid Railway/Vercel detection
- **GitHub Variables**: Set automatically by terraform workflow, consumed by backend/frontend/migrate workflows
- **Secrets Manager Soft Delete**: Auto-cleaned on `terraform destroy` via cleanup step

---

## Implementation Checklist

### Phase 1: Infrastructure ✅
- [x] Set up Terraform S3/DynamoDB backend
- [x] Create VPC with subnets
- [x] Provision Aurora Serverless v2
- [x] Create Cognito User Pool
- [x] Configure ALB + ECS Express Mode
- [x] Create S3 buckets + CloudFront
- [x] Configure GitHub Variables for downstream workflows

### Phase 2: Backend ✅
- [x] Create Dockerfile in `aws/` directory (fixed CMD: `uv run uvicorn`)
- [x] Update code (asyncpg, boto3, Cognito auth) - all routes refactored
- [x] Push to ECR (via backend.yml workflow)
- [x] Deploy and verify (ECS task RUNNING, ALB health: `{"status":"ok"}`)

### Phase 3: Frontend ✅ CODE COMPLETE, DEPLOYMENT PENDING
- [x] Frontend refactored to use AWS Cognito (not Supabase)
- [x] Build passes (`npm run build`)
- [x] Tests pass (96 passed)
- [x] Typecheck passes
- [x] Lint passes (1 warning)
- [ ] Deploy via `frontend.yml` GitHub Action workflow
- [ ] Verify PWA works with new CloudFront URL

### Phase 4: Schema Migration ✅ (user creation in api/deps.py instead)
- [x] Extract schema from Supabase migrations
- [x] Add DB backup step to terraform.yml (pre-destroy)
- [x] Remove migrate.yml (not needed - GitHub Actions can't reach private Aurora)
- [x] User auto-creation on first login implemented in `api/deps.py`

---

*Document version: 1.5 | Last updated: 2026-04-27*
