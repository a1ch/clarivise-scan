# Clarivise Shield — Self-Hosted (Azure) Deployment

**Version 1.0** | Last Updated: May 2026

*For organizations that want to run Shield in their own Azure environment*

---

## Overview

Clarivise Shield can be deployed as a self-hosted service in your own Microsoft Azure subscription. You control the infrastructure, manage updates, and own the data. Shield is deployed as a containerized application in Azure Container Apps or App Service.

**This guide assumes:**
- ✅ You have an active Azure subscription
- ✅ You're comfortable with Azure (Container Registry, Container Apps, Key Vault, etc.)
- ✅ You have administrative access to Microsoft 365
- ✅ You have a valid SSL certificate or can use Azure's managed certificates

---

## Architecture

```
Your Users (Outlook)
        ↓
Microsoft 365 Mail Flow Rule
        ↓
Your Azure Container App (Shield)
        ↓
Claude AI (Anthropic API)
        ↓
Verdict → Mail Transport Agent (return result)
        ↓
User Inbox
```

Shield runs in your Azure Container Apps instance, calls Claude AI for analysis, and returns verdicts to Exchange Online. All email data stays in-transit; nothing is persisted.

---

## Prerequisites

### Azure Resources

- Azure subscription with enough quota for:
  - Container Registry (for Docker images)
  - Container Apps (managed Kubernetes alternative)
  - Key Vault (secrets management)
  - Application Insights (optional, for logging)
- **Contributor** or **Owner** role on the subscription

### Microsoft 365

- Exchange Online admin rights
- Ability to create mail flow rules

### Credentials & Access

- **Anthropic API key** (for Claude AI analysis) — get from https://console.anthropic.com
- **Azure credentials** (service principal or managed identity)
- **SSL certificate** (self-signed, Let's Encrypt, or Azure managed)

---

## Step 1: Set Up Azure Resources

### 1a. Create a Container Registry

```powershell
$resourceGroup = "clarivise-shield-rg"
$location = "eastus"
$registryName = "clariviseregistry"

az group create --name $resourceGroup --location $location

az acr create `
  --resource-group $resourceGroup `
  --name $registryName `
  --sku Basic
```

### 1b. Create a Key Vault

```powershell
$vaultName = "clarivise-vault"

az keyvault create `
  --resource-group $resourceGroup `
  --name $vaultName `
  --location $location

# Store your Anthropic API key
az keyvault secret set `
  --vault-name $vaultName `
  --name "anthropic-api-key" `
  --value "sk-ant-xxxxxxxx..."
```

### 1c. Create a Managed Identity

```powershell
$identityName = "clarivise-shield-identity"

az identity create `
  --resource-group $resourceGroup `
  --name $identityName

# Grant Key Vault access
$identityId = az identity show `
  --name $identityName `
  --resource-group $resourceGroup `
  --query principalId -o tsv

az keyvault set-policy `
  --name $vaultName `
  --object-id $identityId `
  --secret-permissions get list
```

---

## Step 2: Build and Push Docker Image

### 2a. Get the Shield Docker Image

Contact Clarivise support to:
- Download the `Dockerfile` for Shield
- Or receive a pre-built Docker image URI

### 2b. Build the Image Locally

```powershell
# Clone the Shield repository (or get it from Clarivise)
git clone https://github.com/clarivise/shield-self-hosted.git
cd shield-self-hosted

# Build the image
docker build -t shield:latest .

# Tag for your registry
$registryLoginServer = "clariviseregistry.azurecr.io"
docker tag shield:latest $registryLoginServer/shield:latest

# Log in to Azure Container Registry
az acr login --name $registryName

# Push the image
docker push $registryLoginServer/shield:latest
```

### 2c. Or Use a Pre-Built Image (Recommended)

If Clarivise provides a pre-built image:

```powershell
docker pull clarivise/shield:latest
docker tag clarivise/shield:latest $registryLoginServer/shield:latest
docker push $registryLoginServer/shield:latest
```

---

## Step 3: Deploy to Azure Container Apps

### 3a. Create the Container Apps Environment

```powershell
$environment = "clarivise-shield-env"

az containerapp env create `
  --name $environment `
  --resource-group $resourceGroup `
  --location $location
```

### 3b. Deploy the Container App

```powershell
$appName = "clarivise-shield"
$imageName = "$registryLoginServer/shield:latest"

# Configure registry credentials
$registryPassword = az acr credential show `
  --name $registryName `
  --query passwords[0].value -o tsv

az containerapp create `
  --name $appName `
  --resource-group $resourceGroup `
  --environment $environment `
  --image $imageName `
  --registry-server $registryLoginServer `
  --registry-username $registryName `
  --registry-password $registryPassword `
  --target-port 8000 `
  --cpu 0.5 `
  --memory 1.0Gi `
  --env-vars `
    "ANTHROPIC_API_KEY=@Microsoft.KeyVault(VaultName=$vaultName;SecretName=anthropic-api-key)" `
    "ENVIRONMENT=production" `
  --secrets "keyvault-secret=$vaultName" `
  --query properties.configuration.ingress.fqdn -o tsv
```

Note the **FQDN** (fully qualified domain name) returned — this is your Shield endpoint.

### 3c. Enable Ingress & HTTPS

The container app is already accessible via HTTPS at its FQDN. Azure provides a managed certificate.

Retrieve your endpoint:

```powershell
$endpoint = az containerapp show `
  --name $appName `
  --resource-group $resourceGroup `
  --query properties.configuration.ingress.fqdn -o tsv

Write-Host "Shield is running at: https://$endpoint"
```

---

## Step 4: Configure Microsoft 365 Mail Flow Rule

### 4a. Create a Connector (optional, for authentication)

If your Shield instance requires API key authentication:

```powershell
$shieldEndpoint = "https://clarivise-shield.azurecontainers.io"  # Your endpoint from Step 3c
```

### 4b. Create the Mail Flow Rule

In the **Exchange admin center** (https://admin.exchange.microsoft.com):

1. Click **Mail flow** > **Rules**
2. Click **+ New rule** > **Create a new rule**
3. Fill in:

   | Field | Value |
   |-------|-------|
   | **Name** | `Clarivise Shield — Self-Hosted` |
   | **Apply this rule if** | **The sender is located in** > **Outside the organization** |
   | **Do the following** | **Redirect the message to** > **Smart host (relay point)** |
   | **Smart host** | Enter your Shield endpoint (e.g., `clarivise-shield.eastus.azurecontainers.io`) |
   | **Port** | `443` |

   *(Note: Exact steps depend on your Exchange setup. Contact Clarivise for a mail flow rule template.)*

4. Click **Save**

Emails now route through your self-hosted Shield instance.

---

## Step 5: Monitor and Maintain

### View Logs

```powershell
az containerapp logs show `
  --name $appName `
  --resource-group $resourceGroup `
  --tail 50
```

### Monitor Performance

In the **Azure Portal**, go to **Container Apps** > **Clarivise Shield** > **Monitoring** to see:
- CPU and memory usage
- Request latency
- Error rates
- Container restarts

### Update the Image

When a new version is released:

```powershell
# Push the new image to your registry
docker push $registryLoginServer/shield:latest

# Restart the container app (it will pull the latest image)
az containerapp update `
  --name $appName `
  --resource-group $resourceGroup `
  --image $imageName
```

---

## Configuration Options

### Environment Variables

Set these when creating or updating the container app:

| Variable | Value | Required |
|----------|-------|----------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | ✅ Yes |
| `ENVIRONMENT` | `production` or `development` | ✅ Yes |
| `LOG_LEVEL` | `debug`, `info`, `warn`, `error` | ❌ No (default: `info`) |
| `ENABLE_METRICS` | `true` or `false` | ❌ No (default: `true`) |
| `SMTP_RETURN_PATH` | Email address for bounce replies | ❌ No |

### Secrets

Store sensitive values in Azure Key Vault:

```powershell
az keyvault secret set --vault-name $vaultName --name "smtp-password" --value "..."
```

Reference them in your container app as `@Microsoft.KeyVault(VaultName=...;SecretName=...)`.

---

## Scaling

By default, the container app is configured with:
- **CPU:** 0.5
- **Memory:** 1.0 GB
- **Min replicas:** 1
- **Max replicas:** 10

To handle more email volume, update:

```powershell
az containerapp update `
  --name $appName `
  --resource-group $resourceGroup `
  --cpu 1.0 `
  --memory 2.0Gi
```

Azure automatically scales up to `maxReplicas` based on CPU/memory demand.

---

## Troubleshooting

### Emails not flowing through Shield

1. Check the mail flow rule is **enabled** in Exchange
2. Verify the Shield endpoint is reachable:
   ```powershell
   Invoke-WebRequest -Uri "https://$endpoint/health" -ErrorAction SilentlyContinue
   ```
3. Check Azure Container Apps logs for errors

### "Connection timeout" or "502 Bad Gateway"

- Shield app may be crashing. Check logs:
  ```powershell
  az containerapp logs show --name $appName --resource-group $resourceGroup
  ```
- Ensure the Anthropic API key is valid
- Check Azure Key Vault access permissions

### High CPU or out of memory

- Increase container resources in Step 5
- Check logs for infinite loops or memory leaks
- Contact Clarivise support

---

## Cost Estimation

Typical monthly costs for a small organization (~200 users):

| Service | Cost |
|---------|------|
| Azure Container Apps | $25–50 |
| Container Registry | $10 |
| Key Vault | $0.34 (first 10k operations free) |
| Application Insights (optional) | $2–10 |
| **Total** | **~$37–70/month** |

*Anthropic Claude API is billed separately by Anthropic (varies by usage).*

---

## Support

For issues:

1. Check Azure Container Apps logs (this guide, **Step 5**)
2. Verify environment variables and Key Vault access
3. Test Shield health endpoint: `GET /health`
4. Email Clarivise support with:
   - Logs from `az containerapp logs show`
   - Your container app name and resource group
   - The mail flow rule configuration

---

**Self-hosted Shield gives you full control and ownership. Good luck! 🚀**
