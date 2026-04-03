pipeline {
  agent any

  environment {
    RECIPIENTS = "agnieszka.dziubanii@idream.pl, mszylejko@eurotel.pl"
    TEST_FILE = "tests/test_pdp_bundle_offer.py"
  }

  stages {
    stage('Install dependencies') {
      steps {
        sh '''
          python3 -m pip install --upgrade pip
          python3 -m pip install -r requirements.txt
          # Jeśli na Jenkinsie nie masz zainstalowanych przeglądarek Playwright,
          # odkomentuj poniższą linię:
          # python3 -m playwright install --with-deps
        '''
      }
    }

    stage('Run tests') {
      steps {
        sh '''
          python3 -m pytest -q "${TEST_FILE}" --junitxml=results.xml
        '''
      }
    }
  }

  post {
    always {
      junit allowEmptyResults: true, testResults: 'results.xml'
    }
    failure {
      emailext(
        to: "${RECIPIENTS}",
        subject: "BŁĄD ZESTAWÓW: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
        body: "Wykryto brak widocznej sekcji zestawów na następujących stronach PDP:\n\n${FAILED_TESTS, showStack=\\"false\\", showMessage=\\"false\\"}\n\nSprawdź więcej szczegółów na stronie: ${env.BUILD_URL}"
      )
    }
  }
}

