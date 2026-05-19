"""
lib/renderer.py — Company-style PNG architecture diagram renderer.
White zones, thin borders, official icons without wrappers,
horizontal layout, orthogonal arrows, color-coded by connection type.
"""
import os, re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import FancyBboxPatch, Rectangle
import matplotlib.image as mpimg

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.normpath(os.path.join(SKILL_DIR, '..', 'icons'))

# ── Icon path map ─────────────────────────────────────────────────────────────
def _a(p): return os.path.join(ICONS_DIR,'aws',p)
def _g(p): return os.path.join(ICONS_DIR,'gcp',p)
def _k(p): return os.path.join(ICONS_DIR,'k8s',p)
def _z(p): return os.path.join(ICONS_DIR,'azure',p)

ICON_PATHS = {
    'aws_route53_zone':                  _a('network/route-53.png'),
    'aws_acm_certificate':               _a('security/certificate-manager.png'),
    'aws_wafv2_web_acl':                 _a('security/waf.png'),
    'aws_lb':                            _a('network/elastic-load-balancing.png'),
    'aws_alb':                           _a('network/elastic-load-balancing.png'),
    'aws_lb_target_group':               _a('network/elastic-load-balancing.png'),
    'aws_internet_gateway':              _a('network/internet-gateway.png'),
    'aws_eip':                           _a('compute/ec2-elastic-ip-address.png'),
    'aws_nat_gateway':                   _a('network/nat-gateway.png'),
    'aws_eks_cluster':                   _a('compute/elastic-kubernetes-service.png'),
    'aws_eks_node_group':                _a('compute/elastic-kubernetes-service.png'),
    'aws_ecs_cluster':                   _a('compute/elastic-container-service.png'),
    'aws_lambda_function':               _a('compute/lambda.png'),
    'aws_db_instance':                   _a('database/rds.png'),
    'aws_rds_cluster':                   _a('database/aurora.png'),
    'aws_elasticache_cluster':           _a('database/elasticache.png'),
    'aws_elasticache_replication_group': _a('database/elasticache.png'),
    'aws_dynamodb_table':                _a('database/dynamodb.png'),
    'aws_s3_bucket':                     _a('storage/simple-storage-service-s3.png'),
    'aws_efs_file_system':               _a('storage/elastic-file-system.png'),
    'aws_sqs_queue':                     _a('app-integration/simple-queue-service-sqs.png'),
    'aws_sns_topic':                     _a('app-integration/simple-notification-service-sns.png'),
    'aws_msk_cluster':                   _a('app-integration/managed-streaming-for-kafka.png'),
    'aws_kinesis_stream':                _a('analytics/kinesis-data-streams.png'),
    'aws_redshift_cluster':              _a('database/redshift.png'),
    'aws_glue_job':                      _a('analytics/glue.png'),
    'aws_athena_workgroup':              _a('analytics/athena.png'),
    'aws_security_group':                _a('security/identity-and-access-management-iam-permissions.png'),
    'aws_iam_role':                      _a('security/identity-and-access-management-iam-role.png'),
    'aws_kms_key':                       _a('security/key-management-service.png'),
    'aws_secretsmanager_secret':         _a('security/secrets-manager.png'),
    'aws_ecr_repository':                _a('compute/ec2-container-registry-image.png'),
    'aws_cloudwatch_log_group':          _a('management-governance/cloudwatch.png'),
    'aws_cloudwatch_metric_alarm':       _a('management-governance/cloudwatch.png'),
    'aws_codepipeline':                  _a('developer-tools/codepipeline.png'),
    'aws_api_gateway_rest_api':          _a('network/api-gateway.png'),
    'aws_apigatewayv2_api':              _a('network/api-gateway.png'),
    'aws_step_functions_state_machine':  _a('app-integration/step-functions.png'),
    'aws_transit_gateway':               _a('network/transit-gateway.png'),
    'aws_vpn_gateway':                   _a('network/vpn-gateway.png'),
    'aws_cloudfront_distribution':       _a('network/cloudfront.png'),
    'aws_route53_record':                _a('network/route-53-hosted-zone.png'),
    'google_compute_instance':           _g('compute/compute-engine.png'),
    'google_compute_network':            _g('network/virtual-private-cloud.png'),
    'google_compute_subnetwork':         _g('network/virtual-private-cloud.png'),
    'google_compute_firewall':           _g('security/security-command-center.png'),
    'google_container_cluster':          _g('compute/kubernetes-engine.png'),
    'google_container_node_pool':        _g('compute/kubernetes-engine.png'),
    'google_cloud_run_service':          _g('compute/run.png'),
    'google_cloudfunctions_function':    _g('compute/functions.png'),
    'google_sql_database_instance':      _g('database/cloud-sql.png'),
    'google_spanner_instance':           _g('database/spanner.png'),
    'google_storage_bucket':             _g('storage/storage.png'),
    'google_bigquery_dataset':           _g('analytics/bigquery.png'),
    'google_bigquery_table':             _g('analytics/bigquery.png'),
    'google_pubsub_topic':               _g('analytics/pubsub.png'),
    'google_pubsub_subscription':        _g('analytics/pubsub.png'),
    'google_dataflow_job':               _g('analytics/dataflow.png'),
    'google_dataproc_cluster':           _g('analytics/dataproc.png'),
    'google_redis_instance':             _g('database/memorystore.png'),
    'google_service_account':            _g('security/iam.png'),
    'google_kms_key_ring':               _g('security/key-management-service.png'),
    'google_secret_manager_secret':      _g('security/secret-manager.png'),
    'google_artifact_registry_repository':_g('developer-tools/artifact-registry.png'),
    'google_cloudbuild_trigger':         _g('developer-tools/cloud-build.png'),
    'databricks_cluster':                _g('analytics/dataflow.png'),
    'databricks_job':                    _g('analytics/bigquery.png'),
    'databricks_catalog':                _g('analytics/bigquery.png'),
    'databricks_schema':                 _g('database/cloud-sql.png'),
    'databricks_metastore':              _g('database/spanner.png'),
    'databricks_storage_credential':     _g('security/key-management-service.png'),
    'azurerm_virtual_network':           _z('network/virtual-networks.png'),
    'azurerm_subnet':                    _z('network/virtual-networks.png'),
    'azurerm_network_security_group':    _z('security/key-vaults.png'),
    'azurerm_public_ip':                 _z('network/public-ip-addresses.png'),
    'azurerm_load_balancer':             _z('network/load-balancers.png'),
    'azurerm_virtual_machine':           _z('compute/virtual-machine.png'),
    'azurerm_kubernetes_cluster':        _z('compute/kubernetes-services.png'),
    'azurerm_app_service':               _z('compute/app-services.png'),
    'azurerm_function_app':              _z('compute/function-apps.png'),
    'azurerm_sql_database':              _z('database/sql-database.png'),
    'azurerm_cosmosdb_account':          _z('database/azure-cosmos-db.png'),
    'azurerm_storage_account':           _z('storage/storage-accounts.png'),
    'azurerm_redis_cache':               _z('database/cache-redis.png'),
    'azurerm_servicebus_namespace':      _z('integration/service-bus.png'),
    'azurerm_eventhub_namespace':        _z('analytics/event-hubs.png'),
    'azurerm_key_vault':                 _z('security/key-vaults.png'),
    'azurerm_user_assigned_identity':    _z('identity/managed-identities.png'),
    'azurerm_log_analytics_workspace':   _z('monitor/log-analytics-workspaces.png'),
    'azurerm_databricks_workspace':      _z('analytics/azure-databricks.png'),
    'azurerm_data_factory':              _z('analytics/data-factories.png'),
    'azurerm_synapse_workspace':         _z('analytics/azure-synapse-analytics.png'),
    'azurerm_container_registry':        _z('compute/container-registries.png'),
    'kubernetes_namespace':              _k('group/ns.png'),
    'kubernetes_deployment':             _k('compute/deploy.png'),
    'kubernetes_stateful_set':           _k('compute/sts.png'),
    'kubernetes_daemon_set':             _k('compute/ds.png'),
    'kubernetes_service':                _k('network/svc.png'),
    'kubernetes_ingress':                _k('network/ing.png'),
    'kubernetes_config_map':             _k('podconfig/cm.png'),
    'kubernetes_secret':                 _k('podconfig/secret.png'),
    'kubernetes_persistent_volume_claim':_k('storage/pvc.png'),
    'kubernetes_horizontal_pod_autoscaler':_k('clusterconfig/hpa.png'),
    'kubernetes_role':                   _k('rbac/role.png'),
    'kubernetes_cluster_role':           _k('rbac/c-role.png'),
    'helm_release':                      _k('ecosystem/helm.png'),
}

FALLBACK_ICONS = {
    'aws': _a('aws.png'), 'gcp': _g('gcp.png'),
    'azure': _z('azure.png'), 'k8s': _k('k8s.png'),
    'helm': _k('ecosystem/helm.png'), 'databricks': _g('analytics/bigquery.png'),
}

_img_cache = {}
def load_icon(rtype):
    if rtype not in _img_cache:
        p = ICON_PATHS.get(rtype)
        if p and os.path.exists(p):
            _img_cache[rtype] = mpimg.imread(p)
        else:
            prov = rtype.split('_')[0]
            fb = FALLBACK_ICONS.get(prov)
            _img_cache[rtype] = mpimg.imread(fb) if fb and os.path.exists(fb) else None
    return _img_cache[rtype]

PROV_COLOR = {
    'aws':'#FF9900','gcp':'#4285F4','azure':'#0078D4',
    'kubernetes':'#326CE5','helm':'#326CE5','databricks':'#FF6600',
}

CONN_COLOR = {
    'traffic':'#E65100','dep':'#1565C0','k8s':'#283593',
    'async':'#6A1B9A','data':'#00695C','security':'#B71C1C','cross':'#455A64',
}

TIER_ZONE_COLORS = {
    'Networking': ('#EBF5FF','#1976D2','#0D47A1'),
    'Compute':    ('#E8F5E9','#388E3C','#1B5E20'),
    'Data':       ('#FFFDE7','#F9A825','#E65100'),
    'Security':   ('#FFF8E1','#EF6C00','#BF360C'),
    'CI/CD':      ('#F3E5F5','#7B1FA2','#4A148C'),
    'Other':      ('#FAFAFA','#757575','#424242'),
}

def hx(h, d=(0.5,0.5,0.5)):
    h = h.lstrip('#')
    if len(h)==3: h=''.join(c*2 for c in h)
    try: return tuple(int(h[i:i+2],16)/255 for i in (0,2,4))
    except: return d

ISZ = 42   # icon size (data units)


def _place_icon(ax, rtype, cx, cy, sz, label, sublabel='', tagged=True, zo=10):
    img = load_icon(rtype)
    s = sz/2
    if img is not None:
        ext = [cx-s, cx+s, cy+s, cy-s]
        ax.imshow(img, extent=ext, zorder=zo, aspect='auto', interpolation='lanczos')
    ax.text(cx, cy+s+5, label, fontsize=8, color='#1a1a2e', va='top', ha='center',
        zorder=zo+1, path_effects=[pe.withStroke(linewidth=2, foreground='white')])
    if sublabel:
        ax.text(cx, cy+s+18, sublabel, fontsize=6, color='#607080', style='italic',
            va='top', ha='center', zorder=zo+1,
            path_effects=[pe.withStroke(linewidth=1.5, foreground='white')])
    if not tagged:
        ax.add_patch(plt.Circle((cx+s-4, cy-s+4), 8,
            facecolor='#CC0000', edgecolor='white', linewidth=1.5, zorder=zo+2))
        ax.text(cx+s-4, cy-s+4, '!', fontsize=6, fontweight='bold', color='white',
            va='center', ha='center', zorder=zo+3)
    return (cx, cy)


def _zone(ax, x, y, w, h, label, zk, zo=2, dashed=False, inner=False):
    bg, bd, lc = TIER_ZONE_COLORS.get(zk, ('#fafafa','#aaa','#333'))
    fr, fg, fb = hx(bg); er, eg, eb = hx(bd); lr, lg, lb = hx(lc)
    a = 0.45 if inner else 0.25
    lw = 1.2 if inner else 1.8
    ls = '--' if dashed else '-'
    ax.add_patch(Rectangle((x+3,y+3), w, h, facecolor=(0,0,0,0.04), edgecolor='none', zorder=zo-1))
    ax.add_patch(Rectangle((x,y), w, h, facecolor=(fr,fg,fb,a),
                            edgecolor=(er,eg,eb,0.75), linewidth=lw, linestyle=ls, zorder=zo))
    ax.add_patch(Rectangle((x,y), w, 5, facecolor=(er,eg,eb,0.85), edgecolor='none', zorder=zo+1))
    if label:
        ax.text(x+12, y+13, label.upper(), fontsize=7.5, fontweight='bold',
            color=(lr,lg,lb), va='center', ha='left', zorder=zo+2,
            fontfamily='monospace',
            path_effects=[pe.withStroke(linewidth=2, foreground='white')])


def _ortho(ax, x0, y0, x1, y1, ck, lw=1.5, dashed=False, zo=6):
    c = hx(CONN_COLOR.get(ck, '#555'))
    ls = '--' if dashed else '-'
    mid = (x0+x1)/2
    xs=[x0,mid,mid,x1]; ys=[y0,y0,y1,y1]
    ax.plot(xs, ys, color=(*c,0.75), lw=lw, ls=ls, solid_capstyle='butt', zorder=zo)
    ex, ey = x1, y1
    ax.annotate('', xy=(ex,ey), xytext=(ex-10 if x1>x0 else ex+10, ey),
        arrowprops=dict(arrowstyle='->', color=(*c,0.85), lw=lw, mutation_scale=11), zorder=zo+1)


def _ortho_v(ax, x0, y0, x1, y1, ck, lw=1.3, dashed=False, zo=5):
    c = hx(CONN_COLOR.get(ck, '#555'))
    ls = '--' if dashed else '-'
    mid = (y0+y1)/2
    xs=[x0,x0,x1,x1]; ys=[y0,mid,mid,y1]
    ax.plot(xs, ys, color=(*c,0.70), lw=lw, ls=ls, solid_capstyle='butt', zorder=zo)
    ax.annotate('', xy=(x1,y1), xytext=(x1,y1-10 if y1>y0 else y1+10),
        arrowprops=dict(arrowstyle='->', color=(*c,0.85), lw=lw, mutation_scale=11), zorder=zo+1)


def render_diagram(tf_data: dict, project_name: str, output_path: str):
    """Render a company-style PNG from parsed Terraform data."""
    from collections import defaultdict

    icons_exist = os.path.exists(os.path.join(ICONS_DIR, '.downloaded'))
    if not icons_exist:
        print(f'  ⚠️  Icons not found. Run: python3 scripts/download_icons.py')
        print(f'      Rendering without icons (labels only)...')

    resources = tf_data['resources']
    data_src   = tf_data['data']
    variables  = tf_data['variables']
    outputs    = tf_data['outputs']
    deps       = tf_data['dependencies']

    # Group by tier then provider
    by_tier = defaultdict(lambda: defaultdict(list))
    for key, rd in resources.items():
        by_tier[rd.get('tier','Other')][rd.get('provider','generic')].append((key,rd))
    if data_src:
        for key, dd in data_src.items():
            by_tier['Data Sources']['generic'].append((key,dd))

    # Canvas sizing
    TIERS = [t for t in ['Networking','Compute','Data','Security','CI/CD','Other','Data Sources']
             if t in by_tier]
    max_icons_per_tier = max(
        (sum(len(v) for v in clouds.values()) for clouds in by_tier.values()),
        default=1
    )
    COLS = min(6, max_icons_per_tier)
    rows_total = sum(
        max((len(v)+COLS-1)//COLS for v in clouds.values())
        for clouds in by_tier.values()
    )

    W = max(2800, COLS * 140 + 400)
    H = max(900, rows_total * 120 + len(variables)*50 + 300)

    fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=150)
    ax.set_xlim(0,W); ax.set_ylim(H,0)
    ax.axis('off'); ax.set_aspect('equal')
    fig.patch.set_facecolor('#F1F3F4')

    # White card
    ax.add_patch(Rectangle((16,38), W-32, H-54,
        facecolor='white', edgecolor='#D0D4DA', linewidth=1.5, zorder=1))

    # Title bar
    ax.add_patch(Rectangle((16,38), W-32, 44, facecolor='#232F3E', edgecolor='none', zorder=2))
    ax.text(W/2, 60, f'PRODUCTION INFRASTRUCTURE — {project_name.upper()}',
        fontsize=13, fontweight='bold', va='center', ha='center',
        color='white', zorder=3, fontfamily='monospace')
    providers = sorted(tf_data['providers'].keys())
    ax.text(W-30, 60, '  ·  '.join(p.upper() for p in providers),
        fontsize=7, va='center', ha='right', color='#FF9900', zorder=3)

    # Divider
    ax.plot([W*0.62, W*0.62], [90, H-30], color='#DDE1E7', lw=1.2, ls='--', zorder=3)

    PAD = 30
    XGAP = 130
    YGAP = 110
    cy = 92
    id_map = {}

    for tier in TIERS:
        clouds = by_tier[tier]
        total = sum(len(v) for v in clouds.values())
        if total == 0: continue

        fill_h, bd_h, lc_h = TIER_ZONE_COLORS.get(tier, TIER_ZONE_COLORS['Other'])
        max_rows = max((len(v)+COLS-1)//COLS for v in clouds.values())
        tier_h = 38 + max_rows * YGAP + PAD * 2
        _zone(ax, PAD, cy, W*0.56, tier_h, tier, tier, zo=3)

        cx2 = PAD + 20
        for cloud, cloud_res in sorted(clouds.items()):
            if not cloud_res: continue
            cc = min(COLS, len(cloud_res))
            for i, (key, rd) in enumerate(cloud_res):
                col = i % cc; row = i // cc
                rx = cx2 + PAD + col * XGAP
                ry = cy + 46 + row * YGAP
                rtype = rd.get('type','unknown')
                rname = rd.get('name', key.split('.')[-1])
                short = rname[:16]+'…' if len(rname) > 16 else rname
                net = rd.get('net_info', [])
                sublabel = net[0] if net else ''
                tagged = rd.get('has_tags', True)
                c = _place_icon(ax, rtype, rx, ry, ISZ, short, sublabel, tagged, zo=12)
                id_map[key] = c
            cx2 += cc * XGAP + PAD * 2

        cy += tier_h + PAD // 2

    # Variables & Outputs strip
    if variables or outputs:
        vy = cy + PAD
        ax.add_patch(Rectangle((PAD, vy), W-PAD*2, 130,
            facecolor='#FAFAFA', edgecolor='#DDD', linewidth=1, zorder=3))
        ax.text(PAD+10, vy+14, 'VARIABLES', fontsize=7, fontweight='bold',
            color='#555', zorder=5, fontfamily='monospace')
        for i,(vn,vc) in enumerate(sorted(variables.items())[:8]):
            d = vc.get('default') if isinstance(vc,dict) else None
            ds = str(d)[:20] if d is not None else '(req)'
            bx = PAD+20+i*200; by2 = vy+28
            ax.add_patch(Rectangle((bx,by2), 185, 44,
                facecolor='#FFFDE7', edgecolor='#F9A825', lw=0.8, zorder=4))
            ax.text(bx+6, by2+14, vn, fontsize=7, fontweight='bold',
                color='#5D3A00', va='center', zorder=5, fontfamily='monospace')
            ax.text(bx+6, by2+30, f'= {ds}', fontsize=6.5, color='#777',
                va='center', zorder=5, style='italic')

        ax.text(PAD+10, vy+82, 'OUTPUTS', fontsize=7, fontweight='bold',
            color='#555', zorder=5, fontfamily='monospace')
        for i,(on,oc) in enumerate(sorted(outputs.items())[:6]):
            val = oc.get('value','') if isinstance(oc,dict) else ''
            bx = PAD+20+i*300; by2 = vy+96
            ax.add_patch(Rectangle((bx,by2), 285, 26,
                facecolor='#E8F5E9', edgecolor='#43A047', lw=0.8, zorder=4))
            ax.text(bx+6, by2+8, on, fontsize=6.5, fontweight='bold',
                color='#1B5E20', va='center', zorder=5, fontfamily='monospace')
            ax.text(bx+6, by2+20, str(val)[:40], fontsize=5.5, color='#777',
                va='center', zorder=5, style='italic')

    # Dependency arrows (simplified - between nodes that fit in canvas)
    seen = set()
    for sk, tk, lbl in deps:
        sc = id_map.get(sk); tc = id_map.get(tk)
        if sc and tc and (sc,tc) not in seen and sc != tc:
            dashed = lbl == 'depends_on'
            ck = 'dep' if lbl == 'ref' else 'security'
            _ortho(ax, sc[0]+ISZ//2, sc[1], tc[0]-ISZ//2, tc[1], ck, lw=1.2, dashed=dashed, zo=4)
            seen.add((sc,tc))

    # Legend
    LX = W*0.62; LY = 94
    ax.add_patch(Rectangle((LX,LY), 260, 190,
        facecolor='white', edgecolor='#DDE1E7', linewidth=1.2, zorder=20))
    ax.add_patch(Rectangle((LX,LY), 260, 30, facecolor='#232F3E', edgecolor='none', zorder=21))
    ax.text(LX+10, LY+15, 'LEGEND', fontsize=8, fontweight='bold',
        color='white', va='center', zorder=22, fontfamily='monospace')
    legend = [
        ('traffic','━━▶','Traffic / routing'),
        ('dep',    '━━▶','Resource dependency'),
        ('k8s',    '━━▶','Kubernetes internal'),
        ('data',   '━━▶','Data pipeline'),
        ('async',  '━━▶','Async / events'),
        ('cross',  '╌╌▶','Cross-cloud'),
        ('security','╌╌▶','Security / IAM'),
    ]
    for i,(ck,sym,lbl) in enumerate(legend):
        iy = LY+42+i*21
        c = hx(CONN_COLOR[ck])
        ax.text(LX+12, iy, sym, fontsize=8, color=c, va='center', zorder=22, fontfamily='monospace')
        ax.text(LX+55, iy, lbl, fontsize=7, color='#333', va='center', zorder=22)

    # Compliance badge legend
    ax.add_patch(plt.Circle((LX+22, LY+192), 8,
        facecolor='#CC0000', edgecolor='white', linewidth=1, zorder=22))
    ax.text(LX+22, LY+192, '!', fontsize=6, fontweight='bold', color='white',
        va='center', ha='center', zorder=23)
    ax.text(LX+38, LY+192, 'Missing tags (compliance)', fontsize=7, color='#CC0000',
        va='center', zorder=22)

    # Stats
    r = len(resources); ds2 = len(data_src)
    miss = sum(1 for x in resources.values() if not x.get('has_tags'))
    regs = ', '.join(sorted(tf_data['regions'])[:3])
    ax.text(LX, LY+226,
        f'{r} resources  ·  {ds2} data sources  ·  {miss} missing tags\nRegions: {regs}',
        fontsize=6.5, color='#607080', va='top', zorder=20)

    ax.text(W/2, H-6,
        'terraform-diagram skill  ·  open .drawio at app.diagrams.net',
        fontsize=5, color='#AAA', ha='center', va='bottom', zorder=20)

    plt.tight_layout(pad=0)
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
        facecolor='#F1F3F4', format='png')
    plt.close()
    print(f'  PNG: {output_path}  ({os.path.getsize(output_path)//1024} KB)')
