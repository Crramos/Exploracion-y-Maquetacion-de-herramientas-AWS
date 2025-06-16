import boto3
import json
from botocore.exceptions import ClientError

region = 'eu-west-1'
iam = boto3.client('iam')
shub = boto3.client('securityhub', region_name=region)

#  1. Crear grupos IAM
groups = ['SecurityViewers', 'DevOps', 'Compliance', 'AdminCloud']
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
group_users = {
    'SecurityViewers': ['securityviewer-user1', 'securityviewer-user2'],
    'DevOps': ['devops-user1', 'devops-user2'],
    'Compliance': ['compliance-user1', 'compliance-user2'],
    'AdminCloud': ['admincloud-user1', 'admincloud-user2']
}

passwords = {
    'securityviewer-user1': 'ViewerUser123!',
    'securityviewer-user2': 'ViewerUser123!',
    'devops-user1': 'DevOpsUser123!',
    'devops-user2': 'DevOpsUser123!',
    'compliance-user1': 'ComplianceUser123!',
    'compliance-user2': 'ComplianceUser123!',
    'admincloud-user1': 'AdminUser123!',
    'admincloud-user2': 'AdminUser123!'
}

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

        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                print(f"ℹ️ El usuario {user} ya existe.")
            else:
                raise
        try:
            iam.add_user_to_group(GroupName=group, UserName=user)
            print(f"➡️  Usuario {user} añadido al grupo {group}")
        except ClientError as e:
            print(f"⚠️  No se pudo añadir {user} a {group}: {e}")

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
            ]
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
