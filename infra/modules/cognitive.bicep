param location string
param environmentName string
param uniqueSuffix string
param tags object

var openAiName = 'ai-${environmentName}-${uniqueSuffix}'
var documentIntelligenceName = 'di-${environmentName}-${uniqueSuffix}'
var speechName = 'sp-${environmentName}-${uniqueSuffix}'
var modelDeploymentName = 'gpt-4o'

resource openAi 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: openAiName
  location: 'swedencentral'
  tags: tags
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: openAiName
    publicNetworkAccess: 'Enabled'
  }
}

resource gpt4oDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openAi
  name: modelDeploymentName
  sku: {
    name: 'Standard'
    capacity: 1
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelDeploymentName
      version: '2024-11-20'
    }
    raiPolicyName: 'Microsoft.Default'
  }
}

resource documentIntelligence 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: documentIntelligenceName
  location: location
  tags: tags
  kind: 'FormRecognizer'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: documentIntelligenceName
    publicNetworkAccess: 'Enabled'
  }
}

resource speech 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: speechName
  location: location
  tags: tags
  kind: 'SpeechServices'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: speechName
    publicNetworkAccess: 'Enabled'
  }
}

output openAiEndpoint string = openAi.properties.endpoint
output documentIntelligenceEndpoint string = documentIntelligence.properties.endpoint
output speechEndpoint string = speech.properties.endpoint
output gpt4oDeploymentName string = gpt4oDeployment.name
output openAiId string = openAi.id
output documentIntelligenceId string = documentIntelligence.id
output speechId string = speech.id
