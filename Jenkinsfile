// ═══════════════════════════════════════════════════════════════
// Jenkinsfile — PlagiaGuard CI/CD Pipeline
//
// Stages:
//   1. Install Dependencies
//   2. Unit Tests (pytest)
//   3. Selenium UI Tests       [COMMENTED OUT]
//   4. Docker Build & Run      [COMMENTED OUT]
//
// Trigger: Manual / GitHub Webhook on every push to any branch
// ═══════════════════════════════════════════════════════════════

pipeline {

    agent any

    // ── Environment Variables ──────────────────────────────────
    environment {
        APP_NAME       = "plagiaguard"
        IMAGE_NAME     = "plagiaguard-app"
        CONTAINER_NAME = "plagiaguard-container"
        APP_PORT       = "5000"
        APP_URL        = "http://localhost:${APP_PORT}"
        VENV_DIR       = "venv"
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
                bat '''
                    SET PYTHON="C:\\Users\\Trupti\\AppData\\Local\\Programs\\Python\\Python314\\python.exe"
                    IF NOT EXIST %VENV_DIR% (
                        %PYTHON% -m venv %VENV_DIR%
                    )
                    CALL %VENV_DIR%\\Scripts\\activate.bat
                    %PYTHON% -m pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install pytest pytest-cov
                    echo Dependencies installed successfully
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

                bat '''
                    CALL %VENV_DIR%\\Scripts\\activate.bat
                    IF NOT EXIST reports mkdir reports
                    pytest tests/test_unit.py ^
                        -v ^
                        --tb=short ^
                        --junit-xml=reports/unit-test-results.xml ^
                        --cov=backend ^
                        --cov=app ^
                        --cov-report=xml:reports/coverage.xml ^
                        --cov-report=term-missing
                    echo Unit tests passed
                '''
            }

            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/unit-test-results.xml'
                }
                success {
                    echo 'All unit tests passed!'
                }
                failure {
                    echo 'Unit tests FAILED — check logs above'
                }
            }
        }

        
        // ───────────────────────────────────────────────────────
        // STAGE 3: Selenium UI Tests
        // ───────────────────────────────────────────────────────
        stage('Selenium UI Tests') {
            steps {
                echo ' STAGE 3: Running Selenium UI Tests'
                bat '''
                    CALL %VENV_DIR%\\Scripts\\activate.bat
                    pip install selenium webdriver-manager -q
                    mkdir uploads reports 2>nul
                    start /B python app.py
                    timeout /t 10
                    pytest tests/test_selenium.py -v --tb=short --junit-xml=reports/selenium-test-results.xml -x
                    taskkill /IM python.exe /F 2>nul
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/selenium-test-results.xml'
                }
                success { echo 'All Selenium UI tests passed!' }
                failure { echo 'Selenium tests FAILED' }
            }
        }
        /*
        // ───────────────────────────────────────────────────────
        // STAGE 4: Docker Build & Run
        // ───────────────────────────────────────────────────────
        stage('Docker Build & Deploy') {
            steps {
                echo ' STAGE 4: Docker Build & Run'
                bat '''
                    docker stop %CONTAINER_NAME% 2>nul
                    docker rm %CONTAINER_NAME% 2>nul
                    docker build -t %IMAGE_NAME%:latest .
                    docker run -d --name %CONTAINER_NAME% -p %APP_PORT%:5000 --restart unless-stopped %IMAGE_NAME%:latest
                    timeout /t 8
                    docker ps | findstr %CONTAINER_NAME%
                '''
            }
            post {
                success { echo "Docker container is running at http://localhost:${APP_PORT}" }
                failure {
                    bat 'docker logs %CONTAINER_NAME% 2>nul || echo No container logs available'
                }
            }
        }
        */

    }   // ← closes stages { }

    // ── Post-Pipeline Actions ──────────────────────────────────
    post {
        success {
            echo '''
            ╔══════════════════════════════════════════╗
            ║  PIPELINE PASSED - ALL STAGES OK         ║
            ╚══════════════════════════════════════════╝
            '''
        }
        failure {
            echo '''
            ╔══════════════════════════════════════════╗
            ║  PIPELINE FAILED                         ║
            ║  Check the failed stage logs above       ║
            ╚══════════════════════════════════════════╝
            '''
        }
        always {
            echo 'Pipeline execution complete.'
            archiveArtifacts artifacts: 'reports/*.xml', allowEmptyArchive: true
        }
    }

}   // ← closes pipeline { }