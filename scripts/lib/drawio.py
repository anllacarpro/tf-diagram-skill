"""
lib/drawio.py — Multi-page draw.io XML generator from parsed Terraform data.
Company/enterprise style: swimlanes by tier, cloud zones, hover tooltips,
compliance badges, dependency arrows, Legend page.
"""
import html, re, xml.etree.ElementTree as ET
from collections import defaultdict

# ── Draw.io shape map (resource_type → shape style) ──────────────────────────

SHAPES = {
    # AWS Networking
    'aws_vpc':                          ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.vpc',                       '#8C4FFF','#6B3BBF','VPC'),
    'aws_subnet':                       ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.subnet',                    '#8C4FFF','#6B3BBF','Subnet'),
    'aws_internet_gateway':             ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.internet_gateway',          '#8C4FFF','#6B3BBF','IGW'),
    'aws_nat_gateway':                  ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.nat_gateway',               '#8C4FFF','#6B3BBF','NAT GW'),
    'aws_eip':                          ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.elastic_ip_address',        '#8C4FFF','#6B3BBF','EIP'),
    'aws_route_table':                  ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.route_table',               '#8C4FFF','#6B3BBF','RT'),
    'aws_lb':                           ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.application_load_balancer', '#8C4FFF','#6B3BBF','ALB'),
    'aws_alb':                          ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.application_load_balancer', '#8C4FFF','#6B3BBF','ALB'),
    'aws_lb_target_group':              ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.application_load_balancer', '#8C4FFF','#6B3BBF','TG'),
    'aws_cloudfront_distribution':      ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.cloudfront',                '#8C4FFF','#6B3BBF','CloudFront'),
    'aws_route53_zone':                 ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.route_53',                  '#8C4FFF','#6B3BBF','Route 53'),
    'aws_vpn_gateway':                  ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.vpn_gateway',               '#8C4FFF','#6B3BBF','VPN GW'),
    'aws_transit_gateway':              ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.transit_gateway',           '#8C4FFF','#6B3BBF','TGW'),
    # AWS Compute
    'aws_instance':                     ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2',                       '#CC2264','#A01B4E','EC2'),
    'aws_autoscaling_group':            ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.auto_scaling',              '#CC2264','#A01B4E','ASG'),
    'aws_eks_cluster':                  ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.eks',                       '#CC2264','#A01B4E','EKS'),
    'aws_eks_node_group':               ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.eks',                       '#CC2264','#A01B4E','Node Group'),
    'aws_ecs_cluster':                  ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ecs',                       '#CC2264','#A01B4E','ECS'),
    'aws_ecs_service':                  ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ecs',                       '#CC2264','#A01B4E','ECS Svc'),
    'aws_lambda_function':              ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.lambda',                    '#CC2264','#A01B4E','Lambda'),
    'aws_api_gateway_rest_api':         ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.api_gateway',               '#CC2264','#A01B4E','API GW'),
    'aws_apigatewayv2_api':             ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.api_gateway',               '#CC2264','#A01B4E','API GW v2'),
    'aws_step_functions_state_machine': ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.step_functions',            '#CC2264','#A01B4E','Step Fn'),
    'aws_sagemaker_endpoint':           ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.sagemaker',                 '#CC2264','#A01B4E','SageMaker'),
    # AWS Data
    'aws_db_instance':                  ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.rds',                       '#3F48CC','#2E35A0','RDS'),
    'aws_rds_cluster':                  ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.aurora',                    '#3F48CC','#2E35A0','Aurora'),
    'aws_elasticache_replication_group':('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.elasticache',               '#3F48CC','#2E35A0','Redis'),
    'aws_dynamodb_table':               ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.dynamodb',                  '#3F48CC','#2E35A0','DynamoDB'),
    'aws_s3_bucket':                    ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.s3',                        '#3F48CC','#2E35A0','S3'),
    'aws_sqs_queue':                    ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.sqs',                       '#CC2264','#A01B4E','SQS'),
    'aws_sns_topic':                    ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.sns',                       '#CC2264','#A01B4E','SNS'),
    'aws_msk_cluster':                  ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.msk',                       '#CC2264','#A01B4E','MSK'),
    'aws_kinesis_stream':               ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.kinesis_data_streams',      '#CC2264','#A01B4E','Kinesis'),
    'aws_redshift_cluster':             ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.redshift',                  '#3F48CC','#2E35A0','Redshift'),
    'aws_glue_job':                     ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.glue',                      '#8C4FFF','#6B3BBF','Glue'),
    'aws_athena_workgroup':             ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.athena',                    '#8C4FFF','#6B3BBF','Athena'),
    'aws_efs_file_system':              ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.efs',                       '#3F48CC','#2E35A0','EFS'),
    # AWS Security
    'aws_security_group':               ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.security_group',            '#DD344C','#B02035','SG'),
    'aws_iam_role':                     ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.role',                      '#DD344C','#B02035','IAM Role'),
    'aws_iam_policy':                   ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.general',                   '#DD344C','#B02035','IAM Policy'),
    'aws_kms_key':                      ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.key_management_service',    '#DD344C','#B02035','KMS'),
    'aws_secretsmanager_secret':        ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.secrets_manager',           '#DD344C','#B02035','Secrets Mgr'),
    'aws_acm_certificate':              ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.certificate_manager',       '#DD344C','#B02035','ACM'),
    'aws_wafv2_web_acl':               ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.waf',                        '#DD344C','#B02035','WAF'),
    # AWS CI/CD
    'aws_ecr_repository':               ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ecr',                       '#CC2264','#A01B4E','ECR'),
    'aws_codepipeline':                 ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.codepipeline',              '#CC2264','#A01B4E','Pipeline'),
    'aws_cloudwatch_log_group':         ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.cloudwatch',                '#CC2264','#A01B4E','CloudWatch'),
    'aws_cloudwatch_metric_alarm':      ('mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.cloudwatch',                '#CC2264','#A01B4E','CW Alarm'),
    # GCP
    'google_compute_instance':          ('mxgraph.gcp2.compute_engine',              '#4285F4','#2B6CBF','GCE'),
    'google_compute_network':           ('mxgraph.gcp2.virtual_private_cloud',       '#4285F4','#2B6CBF','VPC'),
    'google_compute_subnetwork':        ('mxgraph.gcp2.virtual_private_cloud',       '#4285F4','#2B6CBF','Subnet'),
    'google_compute_firewall':          ('mxgraph.gcp2.cloud_armor',                 '#EA4335','#B0261A','Firewall'),
    'google_container_cluster':         ('mxgraph.gcp2.google_kubernetes_engine',    '#4285F4','#2B6CBF','GKE'),
    'google_container_node_pool':       ('mxgraph.gcp2.google_kubernetes_engine',    '#4285F4','#2B6CBF','Node Pool'),
    'google_cloud_run_service':         ('mxgraph.gcp2.cloud_run',                   '#4285F4','#2B6CBF','Cloud Run'),
    'google_cloudfunctions_function':   ('mxgraph.gcp2.cloud_functions',             '#4285F4','#2B6CBF','Cloud Fn'),
    'google_sql_database_instance':     ('mxgraph.gcp2.cloud_sql',                   '#4285F4','#2B6CBF','Cloud SQL'),
    'google_spanner_instance':          ('mxgraph.gcp2.cloud_spanner',               '#4285F4','#2B6CBF','Spanner'),
    'google_storage_bucket':            ('mxgraph.gcp2.cloud_storage',               '#4285F4','#2B6CBF','GCS'),
    'google_bigquery_dataset':          ('mxgraph.gcp2.bigquery',                    '#4285F4','#2B6CBF','BigQuery'),
    'google_bigquery_table':            ('mxgraph.gcp2.bigquery',                    '#4285F4','#2B6CBF','BQ Table'),
    'google_pubsub_topic':              ('mxgraph.gcp2.cloud_pub_sub',               '#4285F4','#2B6CBF','Pub/Sub'),
    'google_pubsub_subscription':       ('mxgraph.gcp2.cloud_pub_sub',               '#4285F4','#2B6CBF','Sub'),
    'google_service_account':           ('mxgraph.gcp2.cloud_iam',                   '#EA4335','#B0261A','Svc Acct'),
    'google_kms_key_ring':              ('mxgraph.gcp2.cloud_key_management_service','#EA4335','#B0261A','KMS'),
    'google_secret_manager_secret':     ('mxgraph.gcp2.cloud_key_management_service','#EA4335','#B0261A','Secret Mgr'),
    'google_artifact_registry_repository':('mxgraph.gcp2.artifact_registry',        '#4285F4','#2B6CBF','Artifact Reg'),
    'google_cloudbuild_trigger':        ('mxgraph.gcp2.cloud_build',                 '#4285F4','#2B6CBF','Cloud Build'),
    'google_redis_instance':            ('mxgraph.gcp2.memorystore',                 '#4285F4','#2B6CBF','Memorystore'),
    # Databricks
    'databricks_cluster':               ('mxgraph.gcp2.bigquery','#FF6600','#CC4400','DB Cluster'),
    'databricks_job':                   ('mxgraph.gcp2.bigquery','#FF6600','#CC4400','DB Job'),
    'databricks_catalog':               ('mxgraph.gcp2.bigquery','#FF6600','#CC4400','UC Catalog'),
    'databricks_schema':                ('mxgraph.gcp2.bigquery','#FF6600','#CC4400','Schema'),
    'databricks_metastore':             ('mxgraph.gcp2.bigquery','#FF6600','#CC4400','Metastore'),
    'databricks_storage_credential':    ('mxgraph.gcp2.cloud_key_management_service','#FF6600','#CC4400','Cred'),
    # Azure
    'azurerm_virtual_network':          ('mxgraph.azure2.virtual_network',                  '#0078D4','#005A9E','VNet'),
    'azurerm_subnet':                   ('mxgraph.azure2.subnet',                           '#0078D4','#005A9E','Subnet'),
    'azurerm_network_security_group':   ('mxgraph.azure2.network_security_group',           '#E74C3C','#B03A2E','NSG'),
    'azurerm_public_ip':                ('mxgraph.azure2.public_ip_address',                '#0078D4','#005A9E','Public IP'),
    'azurerm_load_balancer':            ('mxgraph.azure2.load_balancer',                    '#0078D4','#005A9E','LB'),
    'azurerm_application_gateway':      ('mxgraph.azure2.application_gateway',              '#0078D4','#005A9E','App GW'),
    'azurerm_virtual_machine':          ('mxgraph.azure2.virtual_machine',                  '#0078D4','#005A9E','VM'),
    'azurerm_kubernetes_cluster':       ('mxgraph.azure2.kubernetes_services',              '#0078D4','#005A9E','AKS'),
    'azurerm_app_service':              ('mxgraph.azure2.app_service',                      '#0078D4','#005A9E','App Svc'),
    'azurerm_function_app':             ('mxgraph.azure2.function_apps',                    '#0078D4','#005A9E','Fn App'),
    'azurerm_sql_database':             ('mxgraph.azure2.sql_database',                     '#0078D4','#005A9E','SQL DB'),
    'azurerm_cosmosdb_account':         ('mxgraph.azure2.azure_cosmos_db',                  '#0078D4','#005A9E','CosmosDB'),
    'azurerm_storage_account':          ('mxgraph.azure2.storage_account',                  '#0078D4','#005A9E','Storage'),
    'azurerm_redis_cache':              ('mxgraph.azure2.cache_redis',                      '#0078D4','#005A9E','Redis'),
    'azurerm_servicebus_namespace':     ('mxgraph.azure2.service_bus',                      '#0078D4','#005A9E','Svc Bus'),
    'azurerm_eventhub_namespace':       ('mxgraph.azure2.event_hubs',                       '#0078D4','#005A9E','Event Hubs'),
    'azurerm_key_vault':                ('mxgraph.azure2.key_vault',                        '#E74C3C','#B03A2E','Key Vault'),
    'azurerm_user_assigned_identity':   ('mxgraph.azure2.managed_identity',                 '#E74C3C','#B03A2E','Managed ID'),
    'azurerm_databricks_workspace':     ('mxgraph.azure2.azure_databricks',                 '#FF6600','#CC4400','Databricks'),
    'azurerm_data_factory':             ('mxgraph.azure2.data_factory',                     '#0078D4','#005A9E','ADF'),
    'azurerm_synapse_workspace':        ('mxgraph.azure2.azure_synapse_analytics',          '#0078D4','#005A9E','Synapse'),
    'azurerm_log_analytics_workspace':  ('mxgraph.azure2.log_analytics_workspace',          '#0078D4','#005A9E','Log Analytics'),
    'azurerm_container_registry':       ('mxgraph.azure2.container_registry',               '#0078D4','#005A9E','ACR'),
    # Kubernetes
    'kubernetes_namespace':             ('mxgraph.kubernetes.ns',       '#326CE5','#1A4DB5','Namespace'),
    'kubernetes_deployment':            ('mxgraph.kubernetes.deploy',   '#326CE5','#1A4DB5','Deployment'),
    'kubernetes_stateful_set':          ('mxgraph.kubernetes.sts',      '#326CE5','#1A4DB5','StatefulSet'),
    'kubernetes_daemon_set':            ('mxgraph.kubernetes.ds',       '#326CE5','#1A4DB5','DaemonSet'),
    'kubernetes_service':               ('mxgraph.kubernetes.svc',      '#326CE5','#1A4DB5','Service'),
    'kubernetes_ingress':               ('mxgraph.kubernetes.ing',      '#326CE5','#1A4DB5','Ingress'),
    'kubernetes_config_map':            ('mxgraph.kubernetes.cm',       '#326CE5','#1A4DB5','ConfigMap'),
    'kubernetes_secret':                ('mxgraph.kubernetes.secret',   '#326CE5','#1A4DB5','Secret'),
    'kubernetes_persistent_volume_claim':('mxgraph.kubernetes.pvc',    '#326CE5','#1A4DB5','PVC'),
    'kubernetes_horizontal_pod_autoscaler':('mxgraph.kubernetes.hpa',  '#326CE5','#1A4DB5','HPA'),
    'kubernetes_role':                  ('mxgraph.kubernetes.role',     '#326CE5','#1A4DB5','Role'),
    'helm_release':                     ('mxgraph.kubernetes.pod',      '#0F1689','#0A1060','Helm'),
}

TIER_ORDER  = ['Networking','Compute','Data','Security','CI/CD','Other']
TIER_COLORS = {
    'Networking': ('#dae8fc','#6c8ebf'),
    'Compute':    ('#d5e8d4','#82b366'),
    'Data':       ('#fff2cc','#d6b656'),
    'Security':   ('#f8cecc','#b85450'),
    'CI/CD':      ('#e1d5e7','#9673a6'),
    'Other':      ('#f5f5f5','#666666'),
}
CLOUD_ZONE_STYLE = {
    'aws':         ('fillColor=#FFF3E0;strokeColor=#FF9900;','fillColor=#FFF3E0;strokeColor=#FF9900;opacity=20;'),
    'gcp':         ('fillColor=#E8F0FE;strokeColor=#4285F4;','fillColor=#E8F0FE;strokeColor=#4285F4;opacity=20;'),
    'azure':       ('fillColor=#E3F2FD;strokeColor=#0078D4;','fillColor=#E3F2FD;strokeColor=#0078D4;opacity=20;'),
    'k8s':         ('fillColor=#E8EAF6;strokeColor=#326CE5;','fillColor=#E8EAF6;strokeColor=#326CE5;opacity=20;'),
    'databricks':  ('fillColor=#FFF0E8;strokeColor=#FF6600;','fillColor=#FFF0E8;strokeColor=#FF6600;opacity=20;'),
    'generic':     ('fillColor=#f5f5f5;strokeColor=#666;','fillColor=#f5f5f5;strokeColor=#666;opacity=20;'),
}

CLOUD_NAME = {
    'aws':'☁ AWS','gcp':'☁ Google Cloud','azure':'☁ Azure',
    'k8s':'⚙ Kubernetes','databricks':'🔷 Databricks','generic':'⚙ Other',
}


def build_drawio(tf_data: dict, project_name: str) -> str:
    """Build a multi-page draw.io XML from parsed Terraform data."""
    resources = tf_data['resources']
    data_src   = tf_data['data']
    variables  = tf_data['variables']
    outputs    = tf_data['outputs']
    deps       = tf_data['dependencies']

    # Group resources by (account, region)
    by_scope = defaultdict(list)
    for key, rd in resources.items():
        scope = (rd.get('account','default'), rd.get('region','unknown-region'))
        by_scope[scope].append((key, rd))

    root_el = ET.Element('mxfile', {'host': 'app.diagrams.net', 'version': '21.0.0'})

    # One diagram page per scope
    for scope_idx, ((acc, reg), res_list) in enumerate(sorted(by_scope.items())):
        page_name = f'{acc} / {reg}' if acc != 'default' else (reg if reg != 'unknown-region' else project_name)
        diag = ET.SubElement(root_el, 'diagram', {'name': page_name, 'id': f'page-{scope_idx}'})
        _build_scope_page(diag, res_list, data_src, deps, variables, outputs, project_name, scope_idx)

    # Legend page
    legend_diag = ET.SubElement(root_el, 'diagram', {'name': '🗺 Legend', 'id': 'page-legend'})
    _build_legend_page(legend_diag, tf_data)

    ET.indent(root_el, space='  ')
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root_el, encoding='unicode')


def _cell_id(page_idx, n):
    return f'p{page_idx}_{n}'


def _build_scope_page(diag_el, res_list, data_src, deps, variables, outputs, project_name, idx):
    mg = ET.SubElement(diag_el, 'mxGraphModel', {
        'dx':'1422','dy':'762','grid':'1','gridSize':'10','guides':'1',
        'tooltips':'1','connect':'1','arrows':'1','fold':'1','page':'1',
        'pageScale':'1','pageWidth':'1654','pageHeight':'1169','math':'0','shadow':'0',
    })
    ro = ET.SubElement(mg, 'root')
    ET.SubElement(ro, 'mxCell', {'id':'0'})
    ET.SubElement(ro, 'mxCell', {'id':'1','parent':'0'})

    cells = []
    id_map = {}   # resource_key → cell_id
    n = [10]

    def nid():
        cid = f'p{idx}_{n[0]}'; n[0]+=1; return cid

    def add_cell(attrs, geo=None):
        c = ET.SubElement(ro, 'mxCell', attrs)
        if geo: ET.SubElement(c, 'mxGeometry', {k:str(v) for k,v in geo.items()}|{'as':'geometry'})
        return attrs['id']

    # Group by tier then cloud
    by_tier = defaultdict(lambda: defaultdict(list))
    for key, rd in res_list:
        by_tier[rd.get('tier','Other')][rd.get('provider','generic')].append((key,rd))
    # Data sources
    if data_src:
        for key, dd in data_src.items():
            by_tier['Data Sources']['generic'].append((key,dd))

    PAD=20; ICON=60; XGAP=130; YGAP=110; SH=30; COLS=6
    cy = PAD

    for tier in TIER_ORDER + ['Data Sources']:
        if tier not in by_tier: continue
        clouds = by_tier[tier]
        total = sum(len(v) for v in clouds.values())
        if total == 0: continue
        fill,stroke = TIER_COLORS.get(tier,('#f5f5f5','#666'))
        max_rows = max((len(v)+COLS-1)//COLS for v in clouds.values())
        swim_h = SH+PAD+max_rows*YGAP+PAD*2

        # Swimlane container
        swim_id = nid()
        add_cell({'id':swim_id,'value':tier,'parent':'1','vertex':'1',
                  'style':f'swimlane;startSize={SH};fillColor={fill};strokeColor={stroke};fontStyle=1;fontSize=10;'},
                 {'x':PAD,'y':cy,'width':1600,'height':swim_h})

        cx2 = PAD
        for cloud, cloud_res in sorted(clouds.items()):
            if not cloud_res: continue
            hdr,bg = CLOUD_ZONE_STYLE.get(cloud, CLOUD_ZONE_STYLE['generic'])
            cname = CLOUD_NAME.get(cloud, cloud)
            cc = min(COLS, len(cloud_res))
            cr = (len(cloud_res)+cc-1)//cc
            cw = cc*XGAP+PAD*2; ch = cr*YGAP+38+PAD

            add_cell({'id':nid(),'value':cname,'parent':'1','vertex':'1',
                      'style':f'rounded=1;whiteSpace=wrap;html=1;verticalAlign=top;spacingTop=4;'
                              f'{bg}{hdr}opacity=15;fontSize=10;fontStyle=1;'},
                     {'x':cx2,'y':cy+SH+PAD,'width':cw,'height':ch})

            for i,(key,rd) in enumerate(cloud_res):
                col = i%cc; row = i//cc
                rx = cx2+PAD+col*XGAP; ry = cy+SH+PAD+38+row*YGAP
                rtype = rd.get('type','unknown')
                rname = rd.get('name',key.split('.')[-1])
                info  = SHAPES.get(rtype)
                prefix = info[3] if info else rtype.split('_')[-1].title()
                short = rname[:16]+'…' if len(rname)>16 else rname
                lbl = f'{prefix}\n{short}'
                net_lines = rd.get('net_info',[])
                if net_lines: lbl += '\n' + '\n'.join(net_lines[:3])

                bad = not rd.get('has_tags', True)
                tooltip = f'{rtype}.{rname}\nFile: {rd.get("file","")}'

                if info:
                    shape, fill2, stroke2, _ = info
                    style = (f'shape={shape};fillColor={fill2};strokeColor={stroke2};'
                             f'fontColor=#fff;fontStyle=1;fontSize=8;'
                             f'labelPosition=bottom;verticalLabelPosition=bottom;'
                             f'align=center;verticalAlign=top;')
                    if bad: style += 'strokeWidth=3;strokeColor=#FF0000;'
                    w,h = 60,60
                else:
                    style = ('rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;'
                             'strokeColor=#666;fontSize=8;')
                    if bad: style += 'strokeWidth=3;strokeColor=#FF0000;'
                    w,h = 90,40

                if tier == 'Data Sources':
                    applied_style = style.replace('strokeColor=#FF0000', '').replace('strokeWidth=3;', '')
                    applied_style += 'dashed=1;dashPattern=6 3;opacity=60;'
                else:
                    applied_style = style

                cid = nid()
                add_cell({'id': cid, 'value': lbl, 'tooltip': tooltip,
                          'parent': '1', 'vertex': '1', 'style': applied_style},
                         {'x': rx, 'y': ry, 'width': w, 'height': h})
                id_map[key] = cid

            cx2 += cw+PAD
        cy += swim_h+PAD

    # Variables
    if variables:
        vy = cy+PAD
        add_cell({'id':nid(),'value':'📋 Terraform Variables',
                  'parent':'1','vertex':'1',
                  'style':'swimlane;startSize=24;fillColor=#fff8e1;strokeColor=#f9a825;fontStyle=1;fontSize=9;'},
                 {'x':PAD,'y':vy,'width':1600,'height':50+((len(variables)+9)//10)*42})
        for i,(vn,vc) in enumerate(sorted(variables.items())):
            col=i%10; row=i//10
            d = (vc.get('default') if isinstance(vc,dict) else None)
            ds = str(d)[:25] if d is not None else '(required)'
            add_cell({'id':nid(),'value':f'var: {vn}\n{ds}',
                      'parent':'1','vertex':'1',
                      'style':'shape=note;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=7;align=left;'},
                     {'x':PAD*2+col*140,'y':vy+28+row*42,'width':130,'height':36})
        cy = vy+50+((len(variables)+9)//10)*42+PAD

    # Outputs
    if outputs:
        oy = cy+PAD
        add_cell({'id':nid(),'value':'📤 Terraform Outputs',
                  'parent':'1','vertex':'1',
                  'style':'swimlane;startSize=24;fillColor=#e8f5e9;strokeColor=#4caf50;fontStyle=1;fontSize=9;'},
                 {'x':PAD,'y':oy,'width':1600,'height':65})
        for i,(on,oc) in enumerate(sorted(outputs.items())):
            val = oc.get('value','') if isinstance(oc,dict) else ''
            add_cell({'id':nid(),'value':f'OUTPUT\n{on}\n{str(val)[:40]}',
                      'parent':'1','vertex':'1',
                      'style':'shape=mxgraph.flowchart.terminate;fillColor=#d5e8d4;strokeColor=#82b366;fontStyle=1;fontSize=7;'},
                     {'x':PAD*2+i*125,'y':oy+10,'width':115,'height':44})

    # Dependency arrows
    seen_edges = set()
    for sk, tk, lbl in deps:
        si = id_map.get(sk); ti = id_map.get(tk)
        if si and ti and (si,ti) not in seen_edges:
            dashed = lbl == 'depends_on'
            edge_style = ('edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;fontSize=7;'
                         +('dashed=1;strokeColor=#b85450;' if dashed else ''))
            add_cell({'id':nid(),'value':'' if lbl=='ref' else lbl,
                      'parent':'1','edge':'1','source':si,'target':ti,
                      'style':edge_style},
                     {'relative':'1'})
            seen_edges.add((si,ti))


def _build_legend_page(diag_el, tf_data):
    mg = ET.SubElement(diag_el, 'mxGraphModel', {
        'dx':'1422','dy':'762','grid':'1','gridSize':'10',
        'pageWidth':'1654','pageHeight':'1169',
    })
    ro = ET.SubElement(mg, 'root')
    ET.SubElement(ro, 'mxCell', {'id':'0'})
    ET.SubElement(ro, 'mxCell', {'id':'1','parent':'0'})

    def add(attrs, geo):
        c = ET.SubElement(ro, 'mxCell', attrs)
        ET.SubElement(c, 'mxGeometry', {k:str(v) for k,v in geo.items()}|{'as':'geometry'})

    y = 20
    add({'id':'leg_title','value':'Architecture Legend',
         'parent':'1','vertex':'1',
         'style':'text;fontStyle=1;fontSize=14;'},
        {'x':20,'y':y,'width':400,'height':30})
    y += 44

    # Tier colors
    add({'id':'leg_t0','value':'TIER SWIMLANES','parent':'1','vertex':'1',
         'style':'text;fontStyle=1;fontSize=10;'},{'x':20,'y':y,'width':300,'height':24})
    y += 28
    for tier,(fill,stroke) in TIER_COLORS.items():
        add({'id':f'leg_{tier}','value':tier,'parent':'1','vertex':'1',
             'style':f'rounded=1;fillColor={fill};strokeColor={stroke};fontStyle=1;fontSize=9;'},
            {'x':20,'y':y,'width':200,'height':24})
        y += 28
    y += 10

    # Cloud colors
    add({'id':'leg_c0','value':'CLOUD PROVIDER ZONES','parent':'1','vertex':'1',
         'style':'text;fontStyle=1;fontSize=10;'},{'x':20,'y':y,'width':300,'height':24})
    y += 28
    for cloud,(hdr,bg) in CLOUD_ZONE_STYLE.items():
        add({'id':f'leg_cloud_{cloud}','value':CLOUD_NAME.get(cloud,cloud),
             'parent':'1','vertex':'1',
             'style':f'rounded=1;{bg}fontStyle=1;fontSize=9;opacity=80;'},
            {'x':20,'y':y,'width':200,'height':24})
        y += 28
    y += 10

    # Compliance
    add({'id':'leg_comp','value':'⚠️  Red border (3px) = resource missing tags — compliance issue',
         'parent':'1','vertex':'1',
         'style':'rounded=1;strokeColor=#FF0000;strokeWidth=3;fontSize=9;'},
        {'x':20,'y':y,'width':500,'height':28})
    y += 38
    add({'id':'leg_ds','value':'🔗 Dashed border = Terraform data source (read-only)',
         'parent':'1','vertex':'1',
         'style':'rounded=1;dashed=1;dashPattern=6 3;fontSize=9;'},
        {'x':20,'y':y,'width':500,'height':28})
    y += 38
    add({'id':'leg_dep','value':'→ Solid arrow = resource ref  |  Red dashed = depends_on',
         'parent':'1','vertex':'1','style':'text;fontSize=9;'},
        {'x':20,'y':y,'width':500,'height':28})
    y += 48

    # Stats
    r = len(tf_data['resources']); ds = len(tf_data['data'])
    m = len(tf_data['modules']); dep = len(tf_data['dependencies'])
    miss = sum(1 for x in tf_data['resources'].values() if not x.get('has_tags'))
    provs = ', '.join(sorted(tf_data['providers'])) or 'n/a'
    regs  = ', '.join(sorted(tf_data['regions']))   or 'n/a'
    accs  = ', '.join(sorted(tf_data['accounts']))  or 'n/a'
    stats = (f'📊 Project Summary\n\n'
             f'Resources: {r}   Data sources: {ds}   Modules: {m}\n'
             f'Dependencies: {dep}   Providers: {provs}\n'
             f'Regions: {regs}\nAccounts/Envs: {accs}\n'
             f'{"⚠️  Resources missing tags: "+str(miss) if miss else "✅ All resources tagged"}')
    add({'id':'leg_stats','value':stats,'parent':'1','vertex':'1',
         'style':'rounded=1;whiteSpace=wrap;fillColor=#f5f5f5;strokeColor=#666;'
                 'fontSize=9;align=left;verticalAlign=top;spacingLeft=8;spacingTop=8;'},
        {'x':20,'y':y,'width':600,'height':140})
