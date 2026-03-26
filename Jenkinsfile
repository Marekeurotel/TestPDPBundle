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
          python3 -m pytest -q "${TEST_FILE}"
        '''
      }
    }
  }

  post {
    failure {
      emailext(
        to: "${RECIPIENTS}",
        subject: "FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
        body: "Testy nie przeszły.\n\nBuild: ${env.BUILD_URL}\n\nSprawdź logi w konsoli Jenkins."
      )
    }
  }
}

