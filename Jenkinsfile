pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 15, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    parameters {
        booleanParam(
            name: 'DRY_RUN_GITOPS',
            defaultValue: true,
            description: 'Keep GitOps manifest update in dry-run mode (safe default without pushing).'
        )
    }

    environment {
        APP_NAME      = 'gcp-devops-demo'
        GCP_REGION    = 'us-central1'
        AR_REPOSITORY = 'devops-demo-images'
        IMAGE_TAG     = "${env.GIT_COMMIT ? env.GIT_COMMIT.take(7) : 'local'}"
    }

    stages {
        stage('Lint & Unit Tests') {
            steps {
                sh '''
                    set -euo pipefail
                    python3 -m venv .venv
                    .venv/bin/pip install --upgrade pip
                    .venv/bin/pip install -r requirements-dev.txt
                    .venv/bin/pytest -v
                    .venv/bin/python scripts/audit_cli.py \
                        --terraform-dir terraform \
                        --yaml-dir gitops \
                        --yaml-dir .github/workflows
                '''
            }
        }

        stage('Terraform Format & Validate') {
            steps {
                sh '''
                    set -euo pipefail
                    terraform fmt -check -recursive terraform
                    terraform -chdir=terraform init -backend=false -input=false
                    terraform -chdir=terraform validate
                    terraform -chdir=terraform/modules/cloud-run init -backend=false -input=false
                    terraform -chdir=terraform/modules/cloud-run validate
                    terraform -chdir=terraform/modules/gke-vpc init -backend=false -input=false
                    terraform -chdir=terraform/modules/gke-vpc validate
                '''
            }
        }

        stage('Build & Security Scan (Simulated)') {
            steps {
                sh '''
                    set -euo pipefail
                    docker build -t "${APP_NAME}:${IMAGE_TAG}" .
                    CONTAINER_UID=$(docker run --rm --entrypoint id "${APP_NAME}:${IMAGE_TAG}" -u)
                    echo "Verified non-root container UID: ${CONTAINER_UID}"
                    test "${CONTAINER_UID}" -ne 0

                    echo "[SIMULATED SCAN] Checking image ${APP_NAME}:${IMAGE_TAG} for CRITICAL CVEs..."
                    echo "[SIMULATED SCAN] Base image python:3.12-slim | Non-root UID=${CONTAINER_UID} | Status=PASS"
                '''
            }
        }

        stage('GitOps Manifest Update') {
            when {
                anyOf {
                    branch 'main'
                    expression { return params.DRY_RUN_GITOPS == true }
                }
            }
            steps {
                withCredentials([string(credentialsId: 'gcp-project-id', variable: 'GCP_PROJECT_ID')]) {
                    sh '''
                        set -euo pipefail
                        TARGET_IMAGE="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${AR_REPOSITORY}/${APP_NAME}:${IMAGE_TAG}"
                        echo "Prepared GitOps image reference: ${TARGET_IMAGE}"
                        if [ "${DRY_RUN_GITOPS}" = "true" ]; then
                            echo "[DRY-RUN] Skipping commit/push of gitops/manifests/deployment.yaml"
                        else
                            sed -i "s|image: .*|image: ${TARGET_IMAGE}|" gitops/manifests/deployment.yaml
                            git diff -- gitops/manifests/deployment.yaml
                        fi
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "Pipeline completed successfully for ${env.APP_NAME} (${env.IMAGE_TAG})."
        }
        failure {
            echo "Pipeline failed for ${env.APP_NAME}. Inspect stage logs for details."
        }
        always {
            cleanWs(deleteDirs: true, notFailBuild: true)
        }
    }
}
