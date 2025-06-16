import boto3

# Crear cliente de Security Hub
client = boto3.client('securityhub', region_name='us-west-1')

# Activar Security Hub (si no está activado)
try:
    client.enable_security_hub()
    print("✅ Security Hub habilitado.")
except client.exceptions.ResourceConflictException:
    print("ℹ️ Security Hub ya estaba habilitado.")

# Suscribir a los estándares recomendados
standards_to_enable = [
    {
        "StandardsArn": "arn:aws:securityhub:::standards/aws-foundational-security-best-practices/v/1.0.0"
    },
    {
        "StandardsArn": "arn:aws:securityhub:::standards/cis-aws-foundations-benchmark/v/1.2.0"
    },
    {
        "StandardsArn": "arn:aws:securityhub:::standards/pci-dss/v/3.2.1"
    }
]

try:
    response = client.batch_enable_standards(StandardsSubscriptionRequests=standards_to_enable)
    print("✅ Estándares suscritos correctamente.")
except client.exceptions.InvalidInputException as e:
    print("❌ Error en la entrada:", e)
except Exception as e:
    print("❌ Otro error:", e)

