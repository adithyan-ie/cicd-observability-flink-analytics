pipeline {
    agent any

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        PIP_DISABLE_PIP_VERSION_CHECK = '1'
        PYTHONUNBUFFERED = '1'
         // ── Kafka / observability ──────────────────────────────────────────
        KAFKA_BOOTSTRAP  = credentials('kafka-bootstrap-servers')  // e.g. kafka:9092
        KAFKA_TOPIC      = 'cicd-events'
        SERVICE_NAME     = 'cicd-observability-flink-analytics'
        DEPLOY_ENV       = 'production'
 
        // ── SonarQube ─────────────────────────────────────────────────────
        SONAR_HOST_URL   = credentials('sonar-host-url')
        SONAR_AUTH_TOKEN = credentials('sonar-auth-token')
 
        // ── Security scanning ─────────────────────────────────────────────
        SNYK_TOKEN       = credentials('snyk-api-token')
 
        // ── Docker / deployment ───────────────────────────────────────────
        DOCKER_IMAGE     = "myregistry.io/${SERVICE_NAME}"
        DOCKER_TAG       = "${BUILD_NUMBER}-${GIT_COMMIT?.take(7) ?: 'unknown'}"
 
        // ── Shared state (set in stages, read in post) ────────────────────
        DEPLOY_ID        = ''
        PREVIOUS_IMAGE   = ''
    }

    stages {
        stage('Prepare Source') {
            steps {
                sh '''
                    cp -R /workspace/cicd-observability-flink-analytics/. .
                    rm -rf .git
                '''
            }
             post {
                success {
                    script {
                        emitCicdEvent(
                            eventType : 'COMMIT',
                            commitSha : env.GIT_COMMIT ?: 'unknown',
                            status    : 'success',
                            message   : 'Source prepared — workspace ready'
                            eventTimestamp: '',
                            eventId: ''
                        )
                    }
                }
            }
        }

        stage('Backend Tests') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    python -m pip install -r requirements.txt
                    python -m pytest
                '''
            }
        }

        stage('Frontend Build') {
            steps {
                dir('frontend') {
                    sh '''
                        npm install
                        npm run build
                    '''
                }
            }
        }

        // STAGE  — Docker Image Build started
        // Builds the Docker image that will be tested and eventually
        // deployed.  Emits a BUILD_STARTED event at the beginning and a
        // BUILD_SUCCESS / BUILD_FAILED event on completion via the `post`
        // block so the DORA lead-time clock starts ticking immediately.
        // ══════════════════════════════════════════════════════════════════
        stage('Build Started') {
            steps {
                script {
                    // Emit event BEFORE the build so Flink can correlate
                    // build duration = BUILD_SUCCESS.ts − BUILD_STARTED.ts
                    emitCicdEvent(
                        eventType : 'BUILD_STARTED',
                        pipelineId: env.BUILD_ID,
                        status    : 'started',
                        message   : "Docker build started — image ${env.DOCKER_IMAGE}:${env.DOCKER_TAG}"
                        eventTimestamp: '',
                        eventId: ''
                    )
                }
 
                sh """
                    echo "==> Building Docker image ${env.DOCKER_IMAGE}:${env.DOCKER_TAG}"
                    docker build \
                        --build-arg BUILD_NUMBER=${BUILD_NUMBER} \
                        --build-arg GIT_COMMIT=${env.GIT_COMMIT ?: 'unknown'} \
                        -t ${env.DOCKER_IMAGE}:${env.DOCKER_TAG} \
                        -t ${env.DOCKER_IMAGE}:latest \
                        .
                    echo "==> Image built successfully"
                """
            }
            post {
                success {
                    script {
                        emitCicdEvent(
                            eventType : 'BUILD_SUCCESS',
                            pipelineId: env.BUILD_ID,
                            status    : 'success',
                            message   : "Image ${env.DOCKER_IMAGE}:${env.DOCKER_TAG} built and tagged"
                            eventTimestamp: '',
                            eventId: ''
                        )
                    }
                }
                failure {
                    script {
                        emitCicdEvent(
                            eventType : 'BUILD_FAILED',
                            pipelineId: env.BUILD_ID,
                            status    : 'failure',
                            message   : "Docker build failed for image ${env.DOCKER_IMAGE}:${env.DOCKER_TAG}"
                            eventTimestamp: '',
                            eventId: ''
                        )
                    }
                }
            }
        }

         stage('SonarQube Scan') {
            steps {
                script {
                    emitCicdEvent(
                        eventType : 'BUILD_STARTED',
                        pipelineId: env.BUILD_ID,
                        status    : 'started',
                        message   : 'SonarQube static analysis scan started'
                    )
                }
 
                withSonarQubeEnv('SonarQube') {
                    sh """
                        sonar-scanner \
                            -Dsonar.projectKey=${env.SERVICE_NAME} \
                            -Dsonar.projectName="${env.SERVICE_NAME}" \
                            -Dsonar.projectVersion=${env.BUILD_NUMBER} \
                            -Dsonar.sources=. \
                            -Dsonar.exclusions=**/node_modules/**,**/.venv/**,**/reports/** \
                            -Dsonar.python.coverage.reportPaths=reports/coverage.xml \
                            -Dsonar.javascript.lcov.reportPaths=frontend/coverage/lcov.info \
                            -Dsonar.host.url=${env.SONAR_HOST_URL} \
                            -Dsonar.login=${env.SONAR_AUTH_TOKEN}
                    """
                }
 
                // Block until SonarQube quality gate result is available
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
            post {
                success {
                    script {
                        emitCicdEvent(
                            eventType : 'BUILD_SUCCESS',
                            pipelineId: env.BUILD_ID,
                            status    : 'success',
                            message   : 'SonarQube quality gate passed'
                        )
                    }
                    echo '✅ SonarQube quality gate passed.'
                }
                failure {
                    script {
                        emitCicdEvent(
                            eventType : 'BUILD_FAILED',
                            pipelineId: env.BUILD_ID,
                            status    : 'failure',
                            message   : 'SonarQube quality gate FAILED — code quality below threshold'
                        )
                    }
                    echo '❌ SonarQube quality gate failed. Review issues in the SonarQube dashboard.'
                }
            }
        }
    }

    post {
        always {
            cleanWs(deleteDirs: true, disableDeferredWipeout: true)
        }
    }


    / ══════════════════════════════════════════════════════════════════════════
// HELPER — emitCicdEvent
//
// Serialises a CI/CD event as JSON and publishes it to the Kafka topic
// configured in the environment block.  All fields are optional except
// eventType; sensible defaults are applied for omitted fields.
//
// Fields published:
//   event_id         – unique UUID for idempotent Kafka consumers
//   event_type       – one of: COMMIT, BUILD_STARTED, BUILD_SUCCESS,
//                              BUILD_FAILED, DEPLOY_STARTED, DEPLOY_SUCCESS,
//                              DEPLOY_FAILED, INCIDENT_OPEN, INCIDENT_CLOSED
//   service          – SERVICE_NAME env var
//   pipeline_id      – Jenkins BUILD_ID
//   deployment_id    – only set for DEPLOY_* events
//   incident_id      – only set for INCIDENT_* events
//   environment      – dev / staging / production
//   commit_sha       – GIT_COMMIT or 'unknown'
//   commit_timestamp – epoch ms of the commit (same as timestamp for now)
//   timestamp        – epoch ms when the event was emitted
//   status           – success / failure / started / rollback / open
//   message          – human-readable description
//   deployment_induced – true when a deploy caused a production incident
// ══════════════════════════════════════════════════════════════════════════
def emitCicdEvent(Map args) {
    def eventId    = UUID.randomUUID().toString()
    def nowMs      = System.currentTimeMillis()
    def commitSha  = args.commitSha   ?: (env.GIT_COMMIT ?: 'unknown')
    def pipelineId = args.pipelineId  ?: env.BUILD_ID
    def deployEnv  = args.environment ?: env.DEPLOY_ENV ?: 'production'
 
    def payload = [
        event_id          : eventId,
        event_type        : args.eventType,
        service           : env.SERVICE_NAME,
        pipeline_id       : pipelineId,
        deployment_id     : args.deploymentId  ?: '',
        incident_id       : args.incidentId    ?: '',
        environment       : deployEnv,
        commit_sha        : commitSha,
        commit_timestamp  : nowMs,
        timestamp         : nowMs,
        status            : args.status  ?: 'unknown',
        message           : args.message ?: '',
        deployment_induced: args.deploymentInduced ?: false
    ]
 
    def json = groovy.json.JsonOutput.toJson(payload)
 
    // kcat (formerly kafkacat) sends a single message to the topic.
    // Replace with your preferred Kafka CLI if kcat is not available.
    sh """
        echo '${json}' | kcat \
            -P \
            -b ${env.KAFKA_BOOTSTRAP} \
            -t ${env.KAFKA_TOPIC} \
            -k "${env.SERVICE_NAME}:${args.eventType}"
    """
 
    echo "[CICD-EVENT] ${args.eventType} → topic '${env.KAFKA_TOPIC}': ${json}"
}
}
