import boto3

# Crear cliente de Security Hub
client = boto3.client('securityhub', region_name='eu-west-1')

# Activar Security Hub (si no está activado)
try:
    client.enable_security_hub()
    print("✅ Security Hub habilitado.")
except client.exceptions.ResourceConflictException:
    print("ℹ️ Security Hub ya estaba habilitado.")
except Exception as e:
    print("❌ No se pudo habilitar Security Hub:", e)
    exit(1)

# Suscribir a los estándares recomendados
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

# Obtener los que ya están activos
enabled = client.get_enabled_standards()['StandardsSubscriptions']
already_enabled_arns = [s['StandardsArn'] for s in enabled]

# Filtrar solo los que faltan
pending = [
    s for s in standards_to_enable if s["StandardsArn"] not in already_enabled_arns
]

if pending:
    client.batch_enable_standards(StandardsSubscriptionRequests=pending)
    print("✅ Estándares nuevos habilitados.")
else:
    print("ℹ️ Todos los estándares ya estaban habilitados.")

