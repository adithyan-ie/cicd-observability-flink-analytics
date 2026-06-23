import hudson.security.FullControlOnceLoggedInAuthorizationStrategy
import hudson.security.HudsonPrivateSecurityRealm
import jenkins.model.Jenkins
import org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition
import org.jenkinsci.plugins.workflow.job.WorkflowJob

def instance = Jenkins.get()
def adminUser = System.getenv('JENKINS_ADMIN_USER') ?: 'admin'
def adminPassword = System.getenv('JENKINS_ADMIN_PASSWORD') ?: 'admin'

def securityRealm = new HudsonPrivateSecurityRealm(false)
if (securityRealm.getUser(adminUser) == null) {
    securityRealm.createAccount(adminUser, adminPassword)
}
instance.setSecurityRealm(securityRealm)

def authorizationStrategy = new FullControlOnceLoggedInAuthorizationStrategy()
authorizationStrategy.setAllowAnonymousRead(false)
instance.setAuthorizationStrategy(authorizationStrategy)

def jobName = System.getenv('JENKINS_PIPELINE_JOB_NAME') ?: 'smart-incident-platform-ci'
def pipelineFile = new File('/workspace/source/Jenkinsfile')

if (pipelineFile.exists()) {
    def job = instance.getItem(jobName) ?: instance.createProject(WorkflowJob, jobName)
    job.setDescription('Seeded CI pipeline for the Smart Incident Platform.')
    job.setDefinition(new CpsFlowDefinition(pipelineFile.text, true))
    job.save()
}

instance.save()
