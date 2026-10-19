// Azure ML platform (Bicep): an Azure Machine Learning workspace and its four
// dependent resources. Deploy with:
//   az deployment group create -g <rg> --template-file infra/ml-platform.bicep \
//     --parameters workspaceName=mlw-adsa
// Companion to labs/lab-01-azure-setup/infra/main.bicep (the storage module).
// Role assignments and private networking are added in Module 9.

@description('Azure ML workspace name')
param workspaceName string

@description('Location for all resources')
param location string = resourceGroup().location

@description('Tags applied to every resource')
param tags object = {
  project: 'adsa'
  env: 'lab'
}

var suffix = uniqueString(resourceGroup().id)

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: 'stml${suffix}'
  location: location
  tags: tags
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    isHnsEnabled: true                 // ADLS Gen2 hierarchical namespace
    allowSharedKeyAccess: false        // Entra-only auth (Module 1)
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'kv-ml-${suffix}'
  location: location
  tags: tags
  properties: {
    sku: { family: 'A', name: 'standard' }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true      // RBAC, not access policies
    enableSoftDelete: true
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-ml-${suffix}'
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
  }
}

resource registry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: 'crml${suffix}'
  location: location
  tags: tags
  sku: { name: 'Basic' }               // bills daily once it exists
  properties: {
    adminUserEnabled: false
  }
}

resource workspace 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: workspaceName
  location: location
  tags: tags
  sku: { name: 'Basic', tier: 'Basic' }
  identity: {
    type: 'SystemAssigned'             // the workspace managed identity (Module 5)
  }
  properties: {
    friendlyName: workspaceName
    storageAccount: storage.id
    keyVault: keyVault.id
    applicationInsights: appInsights.id
    containerRegistry: registry.id
  }
}

output workspaceId string = workspace.id
output workspacePrincipalId string = workspace.identity.principalId
