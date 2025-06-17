import boto3
import os
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

# 2. Políticas para los grupos

policy_dir = 'config/policies'

policy_map = {
    'SecurityViewers': 'SecurityViewers.json',
    'DevOps': 'DevOps.json',
    'Compliance': 'Compliance.json',
    'AdminCloud': 'AdminCloud.json'
}

for group, policy_file in policy_map.items():
    try:
        with open(os.path.join(policy_dir, policy_file)) as f:
            policy_doc = json.load(f)

        iam.put_group_policy(
            GroupName=group,
            PolicyName=os.path.splitext(policy_file)[0],
            PolicyDocument=json.dumps(policy_doc)
        )
        print(f"📎 Política aplicada al grupo {group} desde {policy_file}")
    except Exception as e:
        print(f"⚠️  Error aplicando política a {group}: {e}")

# 3. Crear usuarios y asignar a grupo
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
with open('config/standards/securityhub_standards.yaml') as f:
    standards_yaml = yaml.safe_load(f)

standards_to_enable = [
    {"StandardsArn": arn} for arn in standards_yaml.get("Standards", [])
]
enabled = shub.get_enabled_standards()['StandardsSubscriptions']
enabled_arns = [s['StandardsArn'] for s in enabled]
pending = [s for s in standards_to_enable if s["StandardsArn"] not in enabled_arns]

if pending:
    shub.batch_enable_standards(StandardsSubscriptionRequests=pending)
    print("✅ Estándares nuevos habilitados.")
else:
    print("ℹ️ Todos los estándares ya estaban habilitados.")
