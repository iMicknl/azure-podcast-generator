param containerAppPrincipalId string
param openAiId string
param documentIntelligenceId string
param speechId string

resource openAiResource 'Microsoft.CognitiveServices/accounts@2023-05-01' existing = {
  name: last(split(openAiId, '/'))
}

resource documentIntelligenceResource 'Microsoft.CognitiveServices/accounts@2023-05-01' existing = {
  name: last(split(documentIntelligenceId, '/'))
}

resource speechResource 'Microsoft.CognitiveServices/accounts@2023-05-01' existing = {
  name: last(split(speechId, '/'))
}

resource openAiRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openAiId, containerAppPrincipalId, 'Cognitive Services User')
  scope: openAiResource
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
    principalId: containerAppPrincipalId
    principalType: 'ServicePrincipal'
  }
}

resource documentIntelligenceRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(documentIntelligenceId, containerAppPrincipalId, 'Cognitive Service User')
  scope: documentIntelligenceResource
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a97b65f3-24c7-4388-baec-2e87135dc908')
    principalId: containerAppPrincipalId
    principalType: 'ServicePrincipal'
  }
}

resource speechRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(speechId, containerAppPrincipalId, 'Cognitive Services Speech User')
  scope: speechResource
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'f2dc8367-1007-4938-bd23-fe263f013447')
    principalId: containerAppPrincipalId
    principalType: 'ServicePrincipal'
  }
}
