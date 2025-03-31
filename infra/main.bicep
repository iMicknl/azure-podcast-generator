targetScope = 'subscription'

@description('The location for all resources')
param location string

@description('Environment name')
param environmentName string

@description('Container image to deploy')
param containerImage string

var uniqueSuffix = substring(uniqueString(subscription().id, environmentName), 0, 5)
var tags = {
  environment: environmentName
  application: 'azure-podcast-generator'
}
var rgName = 'rg-${environmentName}-${uniqueSuffix}'

resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: rgName
  location: location
  tags: tags
}

module cognitive 'modules/cognitive.bicep' = {
  scope: rg
  name: 'cognitive-deployment'
  params: {
    location: location
    environmentName: environmentName
    uniqueSuffix: uniqueSuffix
    tags: tags
  }
}

// Deploy container app after cognitive services and storage
module containerapp 'modules/containerapp.bicep' = {
  scope: rg
  name: 'containerapp-deployment'
  params: {
    location: location
    environmentName: environmentName
    uniqueSuffix: uniqueSuffix
    tags: tags
    containerImage: containerImage
    openAiEndpoint: cognitive.outputs.openAiEndpoint
    documentIntelligenceEndpoint: cognitive.outputs.documentIntelligenceEndpoint
    speechResouceId: cognitive.outputs.speechId
  }
}

// Add role assignments for the container app's system-assigned identity
module containerAppRoleAssignments 'modules/containerapp-roles.bicep' = {
  scope: rg
  name: 'containerapp-role-assignments'
  params: {
    containerAppPrincipalId: containerapp.outputs.containerAppPrincipalId
    openAiId: cognitive.outputs.openAiId
    documentIntelligenceId: cognitive.outputs.documentIntelligenceId
    speechId: cognitive.outputs.speechId
  }
}

output containerAppFqdn string = containerapp.outputs.containerAppFqdn
