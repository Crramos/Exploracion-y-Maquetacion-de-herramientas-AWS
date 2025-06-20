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
        user_exists = False

        # Intentar crear el usuario
        try:
            iam.create_user(UserName=user)
            print(f"✅ Usuario creado: {user}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                print(f"ℹ️ El usuario {user} ya existe.")
                user_exists = True
            else:
                raise

        # Intentar crear login profile (solo si el usuario fue recién creado o ya existe)
        try:
            iam.create_login_profile(
                UserName=user,
                Password=passwords[user],
                PasswordResetRequired=True
            )
            print(f"🔐 Login habilitado para: {user}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                print(f"ℹ️ Login profile ya existe para: {user}")
            elif e.response['Error']['Code'] == 'AccessDenied':
                print(f"❌ Permiso denegado para login de {user}")
            else:
                raise

        # Verificar y corregir grupos
        try:
            current_groups = iam.list_groups_for_user(UserName=user)['Groups']
            current_group_names = [g['GroupName'] for g in current_groups]

            if group in current_group_names:
                print(f"✅ {user} ya pertenece a su grupo correcto: {group}")
            else:
                # Eliminar de otros grupos
                for other_group in current_group_names:
                    iam.remove_user_from_group(GroupName=other_group, UserName=user)
                    print(f"⬅️ {user} eliminado de grupo incorrecto: {other_group}")

                # Añadir al grupo correcto
                iam.add_user_to_group(GroupName=group, UserName=user)
                print(f"➡️ {user} añadido al grupo correcto: {group}")
        except ClientError as e:
            print(f"⚠️ Error al gestionar grupos para {user}: {e}")

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
