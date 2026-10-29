targetScope = 'resourceGroup'

param location string = resourceGroup().location
param storageAccountName string
param virtualNetworkName string
param tags object = {}

module network 'app/vnet.bicep' = {
  name: 'mcp-private-network'
  params: {
    vNetName: virtualNetworkName
    location: location
    tags: tags
  }
}

module storageEndpoints 'app/storage-PrivateEndpoint.bicep' = {
  name: 'mcp-storage-private-endpoints'
  params: {
    virtualNetworkName: virtualNetworkName
    subnetName: network.outputs.peSubnetName
    resourceName: storageAccountName
    location: location
    tags: tags
    enableBlob: true
    enableQueue: true
  }
}

output integrationSubnetId string = network.outputs.appSubnetID
