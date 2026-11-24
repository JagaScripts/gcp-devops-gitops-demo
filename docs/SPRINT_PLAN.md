## Tarjeta 1: [3 SP] [Est: 0h 45m] Bootstrap de repositorio, GCP Always Free y Terraform modular
Checklist:
1. Crear estructura de directorios en Linux e inicializar repositorio Git y remoto en GitHub.
2. Configurar proyecto en Google Cloud con alerta de presupuesto de 1 EUR, APIs requeridas y bucket GCS en región US para tfstate.
3. Implementar módulo Terraform activo para Service Account (IAM mínimo privilegio), Artifact Registry y Cloud Run.
4. Implementar módulo Terraform de GKE Autopilot y VPC parametrizado sin aprovisionamiento en la nube.
5. Ejecutar terraform fmt, terraform validate y terraform plan desde terminal Linux.
Acceptance Criteria (AC):
- AC1: El repositorio existe en GitHub sin secretos ni archivos .tfstate versionados.
- AC2: terraform fmt -check -recursive y terraform validate retornan código de salida 0 en todos los módulos.
- AC3: Alerta de presupuesto configurada en 1 EUR y recursos activos restringidos a Google Cloud Always Free.
Definition of Done (DoD):
- Código Terraform modular validado sin errores en Linux y commiteado en main.
## Tarjeta 2: [2 SP] [Est: 0h 45m] Microservicio contenedorizado y script CLI de automatización en Python
Checklist:
1. Crear microservicio HTTP ligero en Python con endpoint /health en formato JSON.
2. Escribir Dockerfile multi-stage con usuario no-root y probar build y ejecución local en Linux.
3. Implementar script CLI en Python con logging estructurado para auditar variables .tf, manifiestos YAML y healthcheck del servicio.
4. Crear suite de tests unitarios en pytest cubriendo casos válidos y errores de validación.
Acceptance Criteria (AC):
- AC1: docker build completa sin errores y el contenedor responde HTTP 200 en /health.
- AC2: pytest ejecuta la suite completa con 100 % de tests en verde.
- AC3: El script CLI finaliza con código de salida distinto de 0 ante configuraciones inválidas.
Definition of Done (DoD):
- Microservicio, Dockerfile, script CLI y tests en verde commiteados en main.
## Tarjeta 3: [3 SP] [Est: 0h 45m] Pipelines CI/CD en GitHub Actions y Jenkinsfile declarativo
Checklist:
1. Configurar autenticación segura entre GitHub Actions y GCP mediante secretos del repositorio.
2. Crear .github/workflows/ci-cd.yml con jobs de pytest, terraform fmt/validate, validación YAML, build/push a Artifact Registry y despliegue a Cloud Run.
3. Escribir Jenkinsfile declarativo multi-stage (Lint/Tests, Terraform Validate, Build/Scan simulado y actualización GitOps).
4. Hacer push a main y comprobar la ejecución completa del pipeline y la respuesta de la URL pública en Cloud Run.
Acceptance Criteria (AC):
- AC1: Todos los jobs del workflow de GitHub Actions terminan en verde sobre main.
- AC2: La URL pública de Google Cloud Run responde HTTP 200 en /health.
- AC3: El Jenkinsfile presenta sintaxis declarativa válida sin credenciales hardcodeadas.
Definition of Done (DoD):
- Despliegue continuo operativo en Cloud Run, badge de CI en verde y Jenkinsfile versionado en main.
## Tarjeta 4: [3 SP] [Est: 0h 45m] Configuración GitOps con ArgoCD y validación en clúster local Linux
Checklist:
1. Escribir manifiestos Kubernetes (Deployment y Service) para el microservicio.
2. Crear manifiesto Application de ArgoCD con automated (prune: true, selfHeal: true).
3. Levantar clúster local efímero en Linux con kind o k3d e instalar ArgoCD.
4. Aplicar la Application, verificar estado Synced y Healthy, y guardar captura del panel en docs/assets/.
5. Eliminar el clúster local efímero al finalizar la comprobación.
Acceptance Criteria (AC):
- AC1: Los manifiestos YAML superan la validación de sintaxis y esquema sin errores.
- AC2: La aplicación alcanza estado Synced y Healthy en la interfaz de ArgoCD.
- AC3: La captura de pantalla de evidencia queda incorporada en el repositorio.
Definition of Done (DoD):
- Manifiestos GitOps, recurso Application y captura de evidencia commiteados en main, con el entorno local limpiado.
## Tarjeta 5: [2 SP] [Est: 0h 45m] Documentación orientada a cliente y envío de candidatura a SEGULA
Checklist:
1. Redactar README.md con enlace a la demo viva en Cloud Run, badge de GitHub Actions y diagrama Mermaid de la arquitectura completa.
2. Incluir la captura de ArgoCD sincronizado y los comandos de verificación local y limpieza (terraform destroy).
3. Comprobar en ventana de incógnito que el repositorio y la URL de Cloud Run son accesibles públicamente.
4. Añadir el enlace del repositorio al texto de candidatura y enviarlo a SEGULA Technologies.