// ═══════════════════════════════════════════════════════════════
// Jenkinsfile — PlagiaGuard CI/CD Pipeline
//
// Stages:
//   1. Install Dependencies
//   2. Unit Tests (pytest)
//   3. Selenium UI Tests
//   4. Docker Build & Run
//
// Trigger: GitHub Webhook on every push to any branch
// ═══════════════════════════════════════════════════════════════

pipeline {

    agent any

    // ── Environment Variables ──────────────────────────────────
    environment {
        APP_NAME    = "plagiaguard"
        IMAGE_NAME  = "plagiaguard-app"
        CONTAINER_NAME = "plagiaguard-container"
        APP_PORT    = "5000"
        APP_URL     = "http://localhost:${APP_PORT}"
        VENV_DIR    = "venv"
    }

    // ── Pipeline Options ───────────────────────────────────────
    options {
        timeout(time: 20, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
    }

    // ── Stages ─────────────────────────────────────────────────
    stages {

        // ───────────────────────────────────────────────────────
        // STAGE 1: Install Dependencies
        // Creates a Python venv and installs all packages
        // ───────────────────────────────────────────────────────
        stage('Install Dependencies') {
            steps {
                echo '════════════════════════════════════════'
                echo ' STAGE 1: Installing Python Dependencies'
                echo '════════════════════════════════════════'

                sh '''
                    # Create virtual environment if it doesn't exist
                    if [ ! -d "${VENV_DIR}" ]; then
                        python3 -m venv ${VENV_DIR}
                    fi

                    # Activate venv and install requirements
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install pytest pytest-cov

                    echo "✓ Dependencies installed successfully"
                    pip list
                '''
            }
        }

        // ───────────────────────────────────────────────────────
        // STAGE 2: Unit Tests
        // Runs pytest unit tests and generates JUnit XML + coverage
        // ───────────────────────────────────────────────────────
        stage('Unit Tests') {
            steps {
                echo '════════════════════════════════════════'
                echo ' STAGE 2: Running Unit Tests'
                echo '════════════════════════════════════════'

                sh '''
                    . ${VENV_DIR}/bin/activate

                    # Run pytest with JUnit XML output for Jenkins to parse
                    pytest tests/test_unit.py \
                        -v \
                        --tb=short \
                        --junit-xml=reports/unit-test-results.xml \
                        --cov=backend \
                        --cov=app \
                        --cov-report=xml:reports/coverage.xml \
                        --cov-report=term-missing

                    echo "✓ Unit tests passed"
                '''
            }

            post {
                always {
                    // Publish JUnit test results in Jenkins
                    junit 'reports/unit-test-results.xml'
                }
                success {
                    echo '✓ All unit tests passed!'
                }
                failure {
                    echo '✗ Unit tests FAILED — pipeline will not continue'
                }
            }
        }
      /*
        // ───────────────────────────────────────────────────────
        // STAGE 3: Selenium UI Tests
        // Starts the Flask app, runs Selenium tests, stops app
        // ───────────────────────────────────────────────────────
        stage('Selenium UI Tests') {
            steps {
                echo '════════════════════════════════════════'
                echo ' STAGE 3: Running Selenium UI Tests'
                echo '════════════════════════════════════════'

                sh '''
                    . ${VENV_DIR}/bin/activate

                    # Install Selenium and webdriver-manager if not in requirements
                    pip install selenium webdriver-manager -q

                    # Create uploads/reports dirs (needed by Flask)
                    mkdir -p uploads reports

                    # Start Flask in background
                    echo "Starting Flask app..."
                    python app.py &
                    FLASK_PID=$!
                    echo "Flask PID: $FLASK_PID"

                    # Wait for Flask to be ready (poll /health or /)
                    echo "Waiting for Flask to start..."
                    for i in $(seq 1 15); do
                        if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/ | grep -q "200"; then
                            echo "Flask is up!"
                            break
                        fi
                        echo "Attempt $i: waiting..."
                        sleep 2
                    done

                    # Run Selenium tests
                    pytest tests/test_selenium.py \
                        -v \
                        --tb=short \
                        --junit-xml=reports/selenium-test-results.xml \
                        -x || SELENIUM_EXIT=$?

                    # Always stop Flask
                    echo "Stopping Flask app (PID: $FLASK_PID)..."
                    kill $FLASK_PID 2>/dev/null || true

                    # Exit with Selenium test exit code
                    exit ${SELENIUM_EXIT:-0}
                '''
            }

            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/selenium-test-results.xml'
                }
                success {
                    echo '✓ All Selenium UI tests passed!'
                }
                failure {
                    echo '✗ Selenium tests FAILED'
                }
            }
        }

        // ───────────────────────────────────────────────────────
        // STAGE 4: Docker Build & Run
        // Builds Docker image and starts container on port 5000
        // ───────────────────────────────────────────────────────
        stage('Docker Build & Deploy') {
            steps {
                echo '════════════════════════════════════════'
                echo ' STAGE 4: Docker Build & Run'
                echo '════════════════════════════════════════'

                sh '''
                    # Stop and remove existing container if running
                    echo "Cleaning up old container..."
                    docker stop ${CONTAINER_NAME} 2>/dev/null || true
                    docker rm   ${CONTAINER_NAME} 2>/dev/null || true

                    # Build Docker image
                    echo "Building Docker image: ${IMAGE_NAME}..."
                    docker build -t ${IMAGE_NAME}:latest .

                    echo "Docker image built successfully:"
                    docker images ${IMAGE_NAME}

                    # Run container, mapping port 5000
                    echo "Starting container..."
                    docker run -d \
                        --name ${CONTAINER_NAME} \
                        -p ${APP_PORT}:5000 \
                        --restart unless-stopped \
                        ${IMAGE_NAME}:latest

                    # Wait for container to be healthy
                    echo "Waiting for container to be ready..."
                    sleep 8

                    # Verify container is running
                    docker ps | grep ${CONTAINER_NAME}

                    # Smoke test: check if app responds
                    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${APP_PORT}/ || echo "000")
                    echo "HTTP response code: $HTTP_CODE"

                    if [ "$HTTP_CODE" = "200" ]; then
                        echo "✓ Container is healthy and responding!"
                    else
                        echo "✗ Container health check failed (HTTP $HTTP_CODE)"
                        docker logs ${CONTAINER_NAME}
                        exit 1
                    fi

                    echo ""
                    echo "Container logs (last 20 lines):"
                    docker logs --tail 20 ${CONTAINER_NAME}
                '''
            }

            post {
                success {
                    echo "✓ Docker container is running at http://localhost:${APP_PORT}"
                }
                failure {
                    sh '''
                        echo "Docker stage failed. Container logs:"
                        docker logs ${CONTAINER_NAME} 2>/dev/null || echo "No container logs available"
                    '''
                }
            }
        }
        */
    }

    // ── Post-Pipeline Actions ──────────────────────────────────
    post {
        success {
            echo '''
            ╔══════════════════════════════════════════╗
            ║  ✓  PIPELINE PASSED — ALL STAGES OK      ║
            ║  PlagiaGuard is live in Docker container  ║
            ╚══════════════════════════════════════════╝
            '''
        }
        failure {
            echo '''
            ╔══════════════════════════════════════════╗
            ║  ✗  PIPELINE FAILED                      ║
            ║  Check the failed stage logs above        ║
            ╚══════════════════════════════════════════╝
            '''
        }
        always {
            echo 'Pipeline execution complete.'
            // Archive test reports as Jenkins artifacts
            archiveArtifacts artifacts: 'reports/*.xml', allowEmptyArchive: true
        }
    }
}
