# Feature: Migration to AWS Infrastructure (2026)
## Objective

Transition the Life Story Preservation Agent from its current PaaS stack (Vercel/Railway/Supabase) to a self-managed |  Terraform-controlled AWS environment. The goal is to minimize monthly fixed costs while maintaining the "Magic Link" authentication and voice-first interaction patterns required for the elderly target demographic.

## Proposed Architecture & Reasoning


| Layer    | Component            | Reasoning & Assumptions                                                                                                                                                      |
| -------- | -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backend  | AWS ECS Express Mode | App Runner is decommissioned as of April 30, 2026. Express Mode offers the simplest deployment path for FastAPI containers while running on standard Fargate infrastructure. |
| Frontend | S3 + CloudFront      | Provides a professional CDN with a 1TB free tier. It is significantly more cost-effective than managed hosting services for static React PWAs.                               |
| Database | Aurora Serverless v2 | We assume a "scale-to-zero" configuration is acceptable. This incurs a 5–15 second "cold start" delay but reduces idle compute costs to $0.                                  |
| Auth     | Amazon Cognito       | Maintains a free tier for up to 50,000 monthly active users. It is the most cost-efficient way to handle identity within the AWS ecosystem.                                  |

## Key Technical Assumptions

- Cost Sensitivity: The architecture prioritizes "Scale to Zero" and Free Tiers. The primary fixed cost will be the Application Load Balancer (ALB) required by ECS, estimated at ~$16/mo.
- Auth UX Parity: We assume the 80-year-old user base must keep "Magic Link" access. Since Cognito doesn't support this natively, we will implement a Custom Auth Flow using Lambda and Amazon SES.
- Infrastructure as Code: All resources must be provisioned via Terraform to ensure reproducibility and long-term maintainability.

## Implementation Constraints

- Database Versioning: To support the "Auto-Pause" feature, the Aurora cluster must use PostgreSQL 13.16+, 14.13+, 15.8+, or 16.4+.
- Networking: A standard VPC with public and private subnets is required to host the RDS instance securely while allowing the ECS tasks to communicate with OpenAI APIs.
- IMPORTANT: **Whenever possible keep existing implementation intact**.
- Always use up to date documentation and APIs - today is Apr 26, 2026.



## Tasks - keep this as a guidance not a hard requirement
### Phase 1: Infrastructure Provisioning (Terraform)

[ ] VPC Setup: Create a VPC with 2 public subnets (for ALB) and 2 private subnets (for RDS/ECS).
[ ] Database: Provision an Amazon Aurora Serverless v2 cluster.
    Task: Set min_capacity to 0 ACU and enable Auto-Pause to allow scaling to 0.
[ ] Identity: Create a Cognito User Pool with a Custom Auth Challenge.
    Task: Provision a Lambda function to handle the "Magic Link" logic via Amazon SES.

### Phase 2: Containerization & Backend Deployment

[ ] Registry: Create an Amazon ECR repository and push the FastAPI image.
[ ] Compute: Deploy the container using ECS Express Mode.
    Task: Configure the Application Load Balancer (ALB) and target groups for the FastAPI service.
[ ] Environment: Map existing Supabase environment variables to AWS equivalents (e.g., DATABASE_URL pointing to the Aurora endpoint).

### Phase 3: Frontend & CDN

[ ] Storage: Create a private S3 bucket for the React build files.
[ ] Distribution: Set up a CloudFront distribution pointing to the S3 bucket.
    Task: Configure "Origin Access Control" (OAC) so the bucket is not publicly accessible except via CloudFront.
    Note: Ensure the CloudFront Free Tier is utilized for the 1TB data transfer allowance.

### Phase 4: Data & Application Logic Migration

[ ] Storage Migration: Move .webm files from Supabase Storage to a new S3 bucket. Update the Python backend to use boto3 instead of the Supabase SDK.
[ ] RLS Logic: Since we are moving away from Supabase RLS, ensure the FastAPI backend explicitly filters all queries by user_id extracted from the Cognito JWT.
[ ] Final Polish: Update the PWA manifest and service workers to point to the new CloudFront URL.

### Troubleshooting & 2026 Context

- App Runner: Do not attempt to use App Runner; it is no longer available for new projects. Use AWS ECS Express Mode
- Aurora Cold Starts: If the UI hangs, ensure the frontend handles a 15-second timeout gracefully during the database "wake-up" period.
