import boto3
import yaml
import json
from botocore.exceptions import ClientError

region = 'eu-west-1'
iam = boto3.client('iam')
shub = boto3.client('securityhub', region_name=region)

#  1. Crear grupos IAM
with open('config/groups.txt', 'r') as f:
    content = f.read()
    groups = content.split()  

for group in groups:
    try:
        iam.create_group(GroupName=group)
        print(f"✅ Grupo creado: {group}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print(f"ℹ️ El grupo {group} ya existe.")
        else:
            raise

# 2. Crear usuarios y asignar a grupo
with open('config/group_users.yaml', 'r') as f:
    group_users = yaml.safe_load(f)

with open('config/passwords.yaml', 'r') as f:
    passwords = yaml.safe_load(f)

for group, users in group_users.items():
    for user in users:
        try:
            iam.create_user(UserName=user)
            print(f"✅ Usuario creado: {user}")

            # Crear perfil de inicio de sesión (Login Profile)
            iam.create_login_profile(
                UserName=user,
                Password=passwords[user],
                PasswordResetRequired=True
            )
            print(f"🔐 Login habilitado para: {user}")

            iam.add_user_to_group(GroupName=group, UserName=user)
            print(f"{user} añadido a {group}")

        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                print(f"ℹ️ El usuario {user} ya existe.")
            elif e.response['Error']['Code'] == 'AccessDenied':
                print(f"❌ Permiso denegado al crear perfil de login para {user}.")
            else:
                raise

# 3. Políticas para los grupos
viewer_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "securityhub:GetFindings",
                "securityhub:DescribeStandards",
                "securityhub:GetInsightResults",
                "securityhub:DescribeHub",
                "securityhub:ListEnabledProductsForImport",
                "securityhub:ListFindingAggregators",
                "securityhub:GetAdhocInsightResults",
                "securityhub:ListMembers"
            ],
            "Resource": "*"
        }
    ]
}

admin_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "securityhub:*",
                "iam:*",
                "config:*",
                "cloudtrail:*",
                "guardduty:*",
                "kms:*",
                "organizations:*"
            ],
            "Resource": "*"
        }
    ]
}

for group in ['SecurityViewers', 'DevOps', 'Compliance']:
    try:
        iam.put_group_policy(
            GroupName=group,
            PolicyName='SecurityHubReadPolicy',
            PolicyDocument=json.dumps(viewer_policy)
        )
        print(f"📎 Política de lectura aplicada al grupo {group}")
    except Exception as e:
        print(f"⚠️  Error aplicando política a {group}: {e}")

try:
    iam.put_group_policy(
        GroupName='AdminCloud',
        PolicyName='SecurityHubFullAccess',
        PolicyDocument=json.dumps(admin_policy)
    )
    print(" Política de administración aplicada al grupo AdminCloud")
except Exception as e:
    print(f"  Error aplicando política a AdminCloud: {e}")

# 4. Activar Security Hub
try:
    shub.enable_security_hub()
    print("✅ Security Hub habilitado.")
except shub.exceptions.ResourceConflictException:
    print("ℹ️ Security Hub ya estaba habilitado.")
except Exception as e:
    print("❌ No se pudo habilitar Security Hub:", e)
    exit(1)

# 5. Suscribir a estándares
standards_to_enable = [
    {
        "StandardsArn": "arn:aws:securityhub:eu-west-1::standards/aws-foundational-security-best-practices/v/1.0.0"
    },
    {
        "StandardsArn": "arn:aws:securityhub:::ruleset/cis-aws-foundations-benchmark/v/1.2.0"
    },
    {
        "StandardsArn": "arn:aws:securityhub:eu-west-1::standards/pci-dss/v/3.2.1"
    }
]

enabled = shub.get_enabled_standards()['StandardsSubscriptions']
enabled_arns = [s['StandardsArn'] for s in enabled]
pending = [s for s in standards_to_enable if s["StandardsArn"] not in enabled_arns]

if pending:
    shub.batch_enable_standards(StandardsSubscriptionRequests=pending)
    print("✅ Estándares nuevos habilitados.")
else:
    print("ℹ️ Todos los estándares ya estaban habilitados.")
