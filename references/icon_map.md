# Icon & Provider Reference

## Provider prefix → cloud mapping

| Prefix       | Cloud       | Zone color |
|-------------|-------------|-----------|
| `aws_`      | AWS         | Orange #FF9900 |
| `google_`   | GCP         | Blue #4285F4 |
| `azurerm_`  | Azure       | Teal #0078D4 |
| `azuread_`  | Azure       | Teal #0078D4 |
| `kubernetes_`| Kubernetes | Indigo #326CE5 |
| `helm_`     | Kubernetes  | Dark #0F1689 |
| `databricks_`| Databricks | Orange #FF6600 |

## Tier classification

| Tier | Resources (sample) |
|------|-------------------|
| Networking | vpc, subnet, igw, nat, lb, alb, cloudfront, route53, vpn, transit_gateway |
| Compute | ec2, eks, ecs, lambda, api_gateway, step_functions, k8s_deployment |
| Data | rds, aurora, elasticache, dynamodb, s3, sqs, sns, kinesis, bigquery, pubsub |
| Security | security_group, iam_role, kms, secretsmanager, acm, waf, guardduty |
| CI/CD | ecr, codepipeline, cloudwatch, artifact_registry, cloudbuild |
| Other | Everything else |

## draw.io shape libraries required
Enable in draw.io: View → Shapes → check these:
- AWS4 (for AWS icons)
- GCP2 (for GCP icons)
- Azure2 (for Azure icons)
- Kubernetes (for K8s icons)

## PNG icon paths (after download_icons.py)
Icons stored at: `scripts/icons/{aws,gcp,azure,k8s}/...`

Source: diagrams Python package (mingrammer/diagrams on PyPI)
~1,500 official PNG icons, 48x48px average

## Arrow color coding (PNG renderer)

| Color | Type |
|-------|------|
| #E65100 (orange) | Traffic / routing |
| #1565C0 (blue) | Resource dependency |
| #283593 (indigo) | Kubernetes internal |
| #00695C (teal) | Data pipeline |
| #6A1B9A (purple) | Async / events |
| #455A64 (grey) | Cross-cloud |
| #B71C1C (red dashed) | Security / IAM |
