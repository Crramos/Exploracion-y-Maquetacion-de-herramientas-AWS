 # Exploración y Maquetación de herramientas AWS

Se procederá aborda la implementación de una arquitectura de seguridad en AWS completamente automatizada mediante el uso de Infrastructure as Code (IaC) con AWS CloudFormation y la automatización de despliegues con GitHub Actions. El objetivo principal es facilitar la activación centralizada de servicios de seguridad clave así como la gestión de usuarios y permisos de forma reproducible y escalable.

A través de scripts y plantillas se configura el entorno para cumplir con buenas prácticas de seguridad en la nube: se habilita y personaliza AWS Security Hub con los principales estándares de cumplimiento, se definen roles IAM adaptados a diferentes perfiles organizativos, y se integran servicios como AWS Config, CloudTrail, GuardDuty y KMS para asegurar la trazabilidad, auditoría y protección de los recursos. Todo ello está diseñado para ser ejecutado automáticamente al realizar cambios en el repositorio, fomentando un enfoque DevSecOps y minimizando errores manuales en entornos productivos.

## Requisitos previos

- Cuenta de AWS
- Conexión a internet
- Cuenta en GitHub 

## Instalación

### Paso 0 

Primero, clona este repositorio en tu máquina local. 

```
git clone https://github.com/Crramos/Exploracion-y-Maquetacion-de-herramientas-AWS

```

Una vez clonado súbalo a su cuenta:

```
cd Exploracion-y-Maquetacion-de-herramientas-AWS
git remote remove origin
git remote add origin https://github.com/tu-usuario/tu-repo-personal.git
git push -u origin main
```

### Paso 1

Ir al login de AWS y completar con los credenciales necesarios:

```
https://eu-west-1.signin.aws.amazon.com/oauth?response_type=code&backwards_compatible=false&iam_user=true&redirect_uri=https%3A%2F%2Fconsole.aws.amazon.com%2Fconsole%2Fhome&code_challenge_method=SHA-256&code_challenge=_vRe2FceF_TwGy4PPN96qJZSjYZ-Z05mFmjtmUwGkOw&client_id=arn%3Aaws%3Asignin%3A%3A%3Aconsole%2Fsignin-create-session&scope=openid
```

Donde se seleccionará el User type Root user y se completará con el email adecuado a la cuenta y su contraseña. En el caso de ser un profesor y no poseer una cuenta personal en AWS se podrán revisar las modificaciones mediante la cuenta facilitada en la memoria, llendo a este enlace:

```
https://eu-west-1.signin.aws.amazon.com/oauth?response_type=code&backwards_compatible=false&iam_user=true&redirect_uri=https%3A%2F%2Fconsole.aws.amazon.com%2Fconsole%2Fhome&code_challenge_method=SHA-256&code_challenge=_vRe2FceF_TwGy4PPN96qJZSjYZ-Z05mFmjtmUwGkOw&client_id=arn%3Aaws%3Asignin%3A%3A%3Aconsole%2Fsignin-create-session&scope=openid
```
y completando con los credenciales correspondientes e indicados en el apartado 4.6.


### Paso 2

Ir a cloudShell, sirviendo la imagen como uno de los métodos:

![Imagen CloudShell](/imagenes/cloudShell.png)

Luego se ejecutará el siguiente comando:

```
 aws organizations enable-aws-service-access \  
    --service-principal access-analyzer.amazonaws.com
```

Luego se irá a cloudFormation, sirviendo la imagen como referencia de una de las maneras:

![Imagen para ir a CloudFormation](/imagenes/cloudFormation.png)

Una vez allí se pulsará sobre "Crear pila". Luego se selecciona "Cree a partir de Infrastructure Composer" y se pulsa sobre "Cree en InfrastructureComposer":

![Imagen inicio pila](/imagenes/primero.png)

Luego se pulsa sobre Plantilla:

![Imagen plantilla](/imagenes/plantilla.png)

Y se copia y se pega el documento de "prerequisitos.yaml". Después se pulsa validar para ver que no haya habido problemas al momento de pegar el código y después se pulsa "Crear Plantilla":

![texto cualquiera por si no carga la imagen](url completa de la imagen)

Saltara un aviso como se muestra en pantalla y se pulsará "Confirmar y continuar con CloudFormation":

![Imagen Confirmar y Continuar](/imagenes/confirmarYContinuarCloudFormation.png)

Se pulsa "Siguiente":

![Imagen de siguiente](/imagenes/primera_parte_siguiente.png)

Y se completa los campos que salen. En nombre de pila y en AuditBucketName se escoge el más conveniente sabiendo que no pueden ser nombres ya existentes. Para el campo OrgId habrá que ir a AWS Organizations y copiar el Id de la organizacion.

 
![Imagen ID de la organizacion](/imagenes/Id_Organizacion.png)
![Imagen validacion Yamal](/imagenes/yamalAValidar.png)

Por último se hace click en el checbox y se pulsa siguiente:

![Imagen Checkbox](/imagenes/penultima_parte_checbox.png)

Y ya se envián los cambios:

![Imagen ulyima](/imagenes/ultima_parte_enviar.png)

Para comprobar que no hubo ningún problema se puede observar el CREATE_COMPLETE, así como todas las tareas realizadas:

![Imagen todo bien](/imagenes/todo_bien.png)

### Paso 3

Luego se va a la casilla de salidas para obtener GitHubDeployAccessKeyId y GitHubDeploySecretAccessKey:

![Imagen de los outputs](/imagenes/outputs.png)

Con eso se irá a la cuenta de GitHub donde esté el proyecto y se irá a Settings -> Secrets and variables -> Actions. Se pulsará sobre "New repository secret" y se añadirá como nombre AWS_ACCESS_KEY_ID y se pondrá la obtenida en la salida anterior como GitHubDeployAccessKeyId. Se repetirá lo mismo para AWS_SECRET_ACCESS_KEY y su salida en GitHubDeploySecretAccessKey. 

![Imagen github](/imagenes/github.png)

Luego solo quedará realizar un commit y un push para que se ejecute el archivo y se desplieguen el resto de recursos.


## Consideraciones adicionales

- Es necesario conocer la región donde se desea despleguer todo esto. Por defecto se está desplegando en eu-west-1. Si se desea cambiar la región a otra se puede realizar cambiando la línea 7 del documento enable_securityhub.py y la línea 25 del documento .github/workflows/enable-securityhub.yml  

- Si se desea añadir más standards al SecurityHub será necesario realizar primero el comando: aws securityhub describe-standards --region eu-west-1  en la CloudShell para poder saber los arn de los mismos. Cuidado con la región en el comando anterior, tiene que coincidir. Una vez se tenga solo hay que copiar el nombre y añadirlo al fichero /config/standards/securityhub_standards.yaml

