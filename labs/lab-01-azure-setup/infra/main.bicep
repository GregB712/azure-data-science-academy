// Lab 01 as infrastructure as code: the same storage setup that
// scripts/01_create_resources.sh creates imperatively.
//
// Deploy (WSL, after `az group create`):
//   az deployment group create \
//     --resource-group rg-adsa-lab01 \
//     --template-file infra/main.bicep \
//     --parameters storageAccountName=<globally-unique-name> \
//                  principalId=$(az ad signed-in-user show --query id -o tsv)
//
// Preview changes first with `az deployment group what-if` (same arguments).

@description('Azure region for the storage account. Defaults to the resource group region.')
param location string = resourceGroup().location

@description('Globally unique storage account name: 3-24 lowercase letters and digits.')
@minLength(3)
@maxLength(24)
param storageAccountName string

@description('Object ID of the user, group or managed identity that gets data-plane access.')
param principalId string

@allowed([
  'User'
  'Group'
  'ServicePrincipal'
])
param principalType string = 'User'

param tags object = {
  project: 'adsa'
  lab: 'lab-01'
  env: 'lab'
}

@description('File systems (containers) to create for the medallion layers.')
param fileSystems array = [
  'bronze'
  'silver'
  'gold'
]

// Built-in role: Storage Blob Data Contributor
var storageBlobDataContributor = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
)

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    isHnsEnabled: true // ADLS Gen2
    allowSharedKeyAccess: false // Entra ID auth only
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    accessTier: 'Hot'
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
}

resource containers 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = [
  for fs in fileSystems: {
    parent: blobService
    name: fs
    properties: {
      publicAccess: 'None'
    }
  }
]

// Deterministic name so redeployments are idempotent.
resource dataContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, principalId, storageBlobDataContributor)
  scope: storage
  properties: {
    roleDefinitionId: storageBlobDataContributor
    principalId: principalId
    principalType: principalType
  }
}

output storageAccountId string = storage.id
output dfsEndpoint string = storage.properties.primaryEndpoints.dfs
