"""
lib/parser.py — Terraform / Terragrunt project parser.
Extracts resources, modules, data sources, variables, outputs, providers.
Handles HCL2 with python-hcl2, falls back to regex for malformed files.
"""
import os, re, json, glob
from collections import defaultdict
from pathlib import Path

try:
    import hcl2
    HCL2_AVAILABLE = True
except ImportError:
    HCL2_AVAILABLE = False
    print("WARNING: python-hcl2 not installed. Run: pip install python-hcl2 --break-system-packages")

# ── Provider detection ────────────────────────────────────────────────────────

PROVIDER_MAP = {
    'aws': 'aws', 'google': 'gcp', 'azurerm': 'azure', 'azuread': 'azure',
    'kubernetes': 'k8s', 'helm': 'k8s', 'databricks': 'databricks',
    'random': 'generic', 'null': 'generic', 'local': 'generic',
    'tls': 'generic', 'time': 'generic', 'vault': 'generic',
    'datadog': 'generic', 'archive': 'generic',
}

def detect_provider(rtype: str) -> str:
    for prefix, cloud in PROVIDER_MAP.items():
        if rtype.startswith(prefix + '_') or rtype == prefix:
            return cloud
    return 'generic'

# ── Tier classification ───────────────────────────────────────────────────────

TIER_MAP = {
    # Networking
    'aws_vpc': 'Networking', 'aws_subnet': 'Networking',
    'aws_internet_gateway': 'Networking', 'aws_nat_gateway': 'Networking',
    'aws_route_table': 'Networking', 'aws_lb': 'Networking', 'aws_alb': 'Networking',
    'aws_lb_target_group': 'Networking', 'aws_cloudfront_distribution': 'Networking',
    'aws_route53_zone': 'Networking', 'aws_route53_record': 'Networking',
    'aws_vpn_gateway': 'Networking', 'aws_transit_gateway': 'Networking', 'aws_eip': 'Networking',
    'google_compute_network': 'Networking', 'google_compute_subnetwork': 'Networking',
    'google_compute_router': 'Networking', 'google_compute_forwarding_rule': 'Networking',
    'google_dns_managed_zone': 'Networking',
    'azurerm_virtual_network': 'Networking', 'azurerm_subnet': 'Networking',
    'azurerm_public_ip': 'Networking', 'azurerm_load_balancer': 'Networking',
    'azurerm_application_gateway': 'Networking',
    'kubernetes_service': 'Networking', 'kubernetes_ingress': 'Networking',
    # Compute
    'aws_instance': 'Compute', 'aws_autoscaling_group': 'Compute',
    'aws_eks_cluster': 'Compute', 'aws_eks_node_group': 'Compute',
    'aws_ecs_cluster': 'Compute', 'aws_ecs_service': 'Compute',
    'aws_lambda_function': 'Compute', 'aws_api_gateway_rest_api': 'Compute',
    'aws_apigatewayv2_api': 'Compute', 'aws_step_functions_state_machine': 'Compute',
    'google_compute_instance': 'Compute', 'google_container_cluster': 'Compute',
    'google_container_node_pool': 'Compute', 'google_cloud_run_service': 'Compute',
    'google_cloudfunctions_function': 'Compute',
    'azurerm_virtual_machine': 'Compute', 'azurerm_kubernetes_cluster': 'Compute',
    'azurerm_app_service': 'Compute', 'azurerm_function_app': 'Compute',
    'kubernetes_deployment': 'Compute', 'kubernetes_stateful_set': 'Compute',
    'kubernetes_namespace': 'Compute', 'kubernetes_horizontal_pod_autoscaler': 'Compute',
    'helm_release': 'Compute', 'databricks_cluster': 'Compute', 'databricks_job': 'Compute',
    # Data & Storage
    'aws_db_instance': 'Data', 'aws_rds_cluster': 'Data', 'aws_elasticache_cluster': 'Data',
    'aws_elasticache_replication_group': 'Data', 'aws_dynamodb_table': 'Data',
    'aws_s3_bucket': 'Data', 'aws_sqs_queue': 'Data', 'aws_sns_topic': 'Data',
    'aws_msk_cluster': 'Data', 'aws_kinesis_stream': 'Data', 'aws_redshift_cluster': 'Data',
    'aws_glue_job': 'Data', 'aws_athena_workgroup': 'Data', 'aws_efs_file_system': 'Data',
    'google_sql_database_instance': 'Data', 'google_spanner_instance': 'Data',
    'google_storage_bucket': 'Data', 'google_bigquery_dataset': 'Data',
    'google_bigquery_table': 'Data', 'google_pubsub_topic': 'Data',
    'google_pubsub_subscription': 'Data', 'google_redis_instance': 'Data',
    'azurerm_sql_database': 'Data', 'azurerm_cosmosdb_account': 'Data',
    'azurerm_storage_account': 'Data', 'azurerm_redis_cache': 'Data',
    'azurerm_servicebus_namespace': 'Data', 'azurerm_eventhub_namespace': 'Data',
    'databricks_catalog': 'Data', 'databricks_schema': 'Data',
    'databricks_metastore': 'Data', 'databricks_external_location': 'Data',
    'kubernetes_persistent_volume_claim': 'Data',
    # Security
    'aws_security_group': 'Security', 'aws_iam_role': 'Security',
    'aws_iam_policy': 'Security', 'aws_kms_key': 'Security',
    'aws_secretsmanager_secret': 'Security', 'aws_acm_certificate': 'Security',
    'aws_wafv2_web_acl': 'Security', 'aws_guardduty_detector': 'Security',
    'google_service_account': 'Security', 'google_kms_key_ring': 'Security',
    'google_secret_manager_secret': 'Security',
    'azurerm_key_vault': 'Security', 'azurerm_user_assigned_identity': 'Security',
    'azurerm_network_security_group': 'Security',
    'databricks_storage_credential': 'Security', 'databricks_permissions': 'Security',
    'kubernetes_secret': 'Security', 'kubernetes_role': 'Security',
    # CI/CD & Observability
    'aws_ecr_repository': 'CI/CD', 'aws_codepipeline': 'CI/CD',
    'aws_cloudwatch_log_group': 'CI/CD', 'aws_cloudwatch_metric_alarm': 'CI/CD',
    'google_artifact_registry_repository': 'CI/CD', 'google_cloudbuild_trigger': 'CI/CD',
    'azurerm_container_registry': 'CI/CD', 'azurerm_log_analytics_workspace': 'CI/CD',
}

def get_tier(rtype: str) -> str:
    return TIER_MAP.get(rtype, 'Other')

# ── Network info extractor ────────────────────────────────────────────────────

NET_FIELDS = {
    'cidr_block': 'CIDR', 'cidr_blocks': 'CIDR', 'ipv4_cidr_block': 'CIDR',
    'address_space': 'CIDR', 'address_prefixes': 'CIDR',
    'availability_zone': 'AZ', 'availability_zones': 'AZs',
    'region': 'Region', 'location': 'Region',
    'from_port': 'Port', 'to_port': 'ToPort', 'protocol': 'Proto',
    'public_ip': 'Pub IP', 'ip_address': 'IP', 'allocation_id': 'EIP',
}

def extract_net_info(config: dict) -> list:
    lines = []
    if not isinstance(config, dict): return lines
    for field, label in NET_FIELDS.items():
        val = config.get(field)
        if val is None: continue
        if isinstance(val, list): val = ', '.join(str(v) for v in val[:2])
        elif isinstance(val, dict): continue
        val = str(val).strip().strip('"')
        if val and val not in ('null', 'None', '', '0'):
            lines.append(f'{label}: {val}')
    for rule in (config.get('ingress') or [])[:2]:
        if isinstance(rule, dict):
            fp = rule.get('from_port', ''); tp = rule.get('to_port', '')
            pr = rule.get('protocol', '')
            if fp: lines.append(f'→ {pr} {fp}-{tp}')
    return lines[:4]

def has_tags(config: dict) -> bool:
    if not isinstance(config, dict): return False
    t = config.get('tags') or config.get('labels')
    return bool(t) and isinstance(t, dict)

# ── Region/account detection ──────────────────────────────────────────────────

AWS_REGION_RE = re.compile(r'(us|eu|ap|sa|ca|me|af)-(east|west|north|south|central|northeast|southeast)-\d')
GCP_REGION_RE = re.compile(r'(us|europe|asia|northamerica|southamerica|australia)-\w+-\d')
AZ_REGION_RE  = re.compile(r'(eastus|westus|northeurope|westeurope|southeastasia|brazilsouth)\d?')
ENV_RE = re.compile(r'^(dev|staging|prod|production|sandbox|shared|mgmt|management)$', re.I)
ACCOUNT_RE = re.compile(r'^\d{12}$')

def infer_region_account(filepath: str, config: dict, tf_root: str) -> tuple:
    parts = Path(os.path.relpath(filepath, tf_root)).parts
    region = 'unknown-region'
    account = 'default'
    for part in parts:
        if AWS_REGION_RE.search(part) or GCP_REGION_RE.search(part) or AZ_REGION_RE.search(part):
            region = part
        if ACCOUNT_RE.match(part):
            account = part
        if ENV_RE.match(part):
            account = part
    if isinstance(config, dict):
        r = config.get('region', config.get('location', ''))
        if r and isinstance(r, str) and len(r) < 30:
            region = r.strip('"')
    return account, region

# ── HCL Parser ────────────────────────────────────────────────────────────────

REF_PAT = re.compile(
    r'\$\{(aws_\w+|google_\w+|azurerm_\w+|kubernetes_\w+|helm_\w+|databricks_\w+)\.(\w+)'
)
DEP_PAT = re.compile(
    r'(aws_\w+|google_\w+|azurerm_\w+|kubernetes_\w+|helm_\w+|databricks_\w+)\.(\w+)'
)


def parse_project(directory: str) -> dict:
    """Parse a Terraform project directory and return structured data."""
    result = {
        'resources': {}, 'modules': {}, 'providers': {},
        'data': {}, 'variables': {}, 'outputs': {}, 'locals': {},
        'dependencies': [], 'accounts': set(), 'regions': set(),
    }

    tf_root = os.path.abspath(directory)
    tf_files = (
        glob.glob(os.path.join(tf_root, '**/*.tf'), recursive=True) +
        glob.glob(os.path.join(tf_root, '**/*.hcl'), recursive=True)
    )
    tf_files = [
        f for f in tf_files
        if '.terraform' + os.sep not in f and '/.terraform/' not in f
    ]

    if not tf_files:
        print(f'  WARNING: No .tf/.hcl files found in {directory}')
        return result

    for filepath in sorted(tf_files):
        rel = os.path.relpath(filepath, tf_root)
        mp  = os.path.dirname(rel).replace(os.sep, '/') or 'root'
        try:
            content = open(filepath, 'r', encoding='utf-8', errors='replace').read()
            # Fix semicolons in single-line blocks (common in demo/test TF)
            content_fixed = re.sub(r'\{([^}]+)\}',
                                   lambda m: '{' + m.group(1).replace(';', '\n') + '}',
                                   content)
            parsed_ok = False
            if HCL2_AVAILABLE:
                try:
                    parsed = hcl2.loads(content_fixed)
                    _extract_hcl2(parsed, result, rel, mp, tf_root)
                    parsed_ok = True
                except Exception:
                    pass
            if not parsed_ok:
                _extract_regex(content, result, rel, mp, tf_root)
        except Exception as e:
            print(f'  WARNING: {rel}: {e}')

    _extract_dependencies(result)
    return result


def _extract_hcl2(parsed, result, filepath, mp, tf_root):
    for bt, blocks in parsed.items():
        if not isinstance(blocks, list): continue
        for block in blocks:
            if not isinstance(block, dict): continue

            if bt == 'resource':
                for rtype, rnames in block.items():
                    if not isinstance(rnames, dict): continue
                    for rname, rconfig in rnames.items():
                        rtype = rtype.strip('"'); rname = rname.strip('"')
                        cfg = rconfig if isinstance(rconfig, dict) else {}
                        acc, reg = infer_region_account(filepath, cfg, tf_root)
                        result['accounts'].add(acc); result['regions'].add(reg)
                        key = f'{rtype}.{rname}'
                        result['resources'][key] = {
                            'type': rtype, 'name': rname, 'config': cfg,
                            'file': filepath, 'module_path': mp,
                            'provider': detect_provider(rtype),
                            'tier': get_tier(rtype),
                            'account': acc, 'region': reg,
                            'has_tags': has_tags(cfg),
                            'net_info': extract_net_info(cfg),
                        }
                        p = detect_provider(rtype)
                        if p not in ('generic',):
                            result['providers'][p] = result['providers'].get(p, {})

            elif bt == 'data':
                for dtype, dnames in block.items():
                    if not isinstance(dnames, dict): continue
                    for dname, dconfig in dnames.items():
                        dtype = dtype.strip('"'); dname = dname.strip('"')
                        cfg = dconfig if isinstance(dconfig, dict) else {}
                        key = f'data.{dtype}.{dname}'
                        result['data'][key] = {
                            'type': dtype, 'name': dname, 'config': cfg,
                            'file': filepath, 'module_path': mp,
                            'provider': detect_provider(dtype),
                        }

            elif bt == 'module':
                for mname, mc in block.items():
                    mname = mname.strip('"')
                    cfg = mc if isinstance(mc, dict) else {}
                    result['modules'][f'module.{mname}'] = {
                        'name': mname, 'source': cfg.get('source', 'unknown'),
                        'config': cfg, 'file': filepath, 'module_path': mp,
                    }

            elif bt == 'variable':
                for vname, vc in block.items():
                    result['variables'][vname.strip('"')] = vc if isinstance(vc, dict) else {}

            elif bt == 'output':
                for oname, oc in block.items():
                    result['outputs'][oname.strip('"')] = oc if isinstance(oc, dict) else {}

            elif bt == 'provider':
                for pname, pc in block.items():
                    p = detect_provider(pname.strip('"'))
                    cfg = pc if isinstance(pc, dict) else {}
                    result['providers'][p] = cfg
                    r = cfg.get('region', cfg.get('location', ''))
                    if r and isinstance(r, str):
                        result['regions'].add(r.strip('"'))


def _extract_regex(content, result, filepath, mp, tf_root):
    for m in re.finditer(r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{', content):
        rtype, rname = m.group(1), m.group(2)
        key = f'{rtype}.{rname}'
        if key not in result['resources']:
            acc, reg = infer_region_account(filepath, {}, tf_root)
            result['accounts'].add(acc); result['regions'].add(reg)
            result['resources'][key] = {
                'type': rtype, 'name': rname, 'config': {},
                'file': filepath, 'module_path': mp,
                'provider': detect_provider(rtype),
                'tier': get_tier(rtype),
                'account': acc, 'region': reg,
                'has_tags': False, 'net_info': [],
            }
    for m in re.finditer(r'data\s+"([^"]+)"\s+"([^"]+)"\s*\{', content):
        dtype, dname = m.group(1), m.group(2)
        key = f'data.{dtype}.{dname}'
        if key not in result['data']:
            result['data'][key] = {
                'type': dtype, 'name': dname, 'config': {},
                'file': filepath, 'module_path': mp,
                'provider': detect_provider(dtype),
            }
    for m in re.finditer(r'module\s+"([^"]+)"\s*\{', content):
        mname = m.group(1)
        key = f'module.{mname}'
        if key not in result['modules']:
            s = re.search(r'source\s*=\s*"([^"]+)"', content[m.start():m.start()+500])
            result['modules'][key] = {
                'name': mname, 'source': s.group(1) if s else 'unknown',
                'config': {}, 'file': filepath, 'module_path': mp,
            }


def _extract_dependencies(result):
    all_keys = set(result['resources']) | set(result['data'])
    seen = set()
    for src_key, sd in result['resources'].items():
        cfg_str = json.dumps(sd.get('config', {}))
        for rtype, rname in REF_PAT.findall(cfg_str):
            tgt = f'{rtype}.{rname}'
            if tgt in all_keys and tgt != src_key:
                e = (src_key, tgt, 'ref')
                if e[:2] not in seen:
                    result['dependencies'].append(e)
                    seen.add(e[:2])
        for dep in sd.get('config', {}).get('depends_on', []):
            m = DEP_PAT.search(str(dep))
            if m:
                tgt = f'{m.group(1)}.{m.group(2)}'
                if tgt in all_keys and (src_key, tgt) not in seen:
                    result['dependencies'].append((src_key, tgt, 'depends_on'))
                    seen.add((src_key, tgt))
