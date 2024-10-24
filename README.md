# 🗣️ Azure Podcast Generator

Generate an engaging podcast based on your document using Azure OpenAI Service and Azure AI Speech.

This project leverages Streamlit for the front-end, Azure Document Intelligence for the document analysis, Azure OpenAI Service with structured outputs for the text generation, and Azure AI Speech for the text-to-speech. All data will be processed within your Azure subscription, ensuring it remains in your Azure environment and is not shared with any third-party.


> [!NOTE]
> This application is an example implementation and is not intended for production use. It is provided as-is and is not supported.



https://github.com/user-attachments/assets/d9c3b218-1989-42af-adfb-442b450715fe


## Getting started

You can run the application locally or deploy it to Azure, such as on Azure Container Apps. For development, the easiest approach is to use the included [Dev Container](https://code.visualstudio.com/docs/devcontainers/containers), which installs all necessary dependencies and tools to get you started.


### Prerequisites

This project utilizes several Azure services, requiring an active Azure subscription. The services used include:

- Azure Document Intelligence
- Azure OpenAI Service, gpt-4o (2024-08-06) [model availability per region](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models?tabs=python-secure#standard-deployment-model-availability)
- Azure AI Speech (East US, West Europe, and Southeast Asia for Azure HD voices)

### Local deployment

Make sure you have Python 3.12+, [uv](https://docs.astral.sh/uv/getting-started/installation/) and optionally the [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed on your machine.

You can install the required dependencies via the command below using uv.

```bash
uv sync
```

Configure the necessary environment variables in the .env file or your environment settings. The required values can be found in the [.env.sample](./app/.env.sample) file. Create a new .env file in the app directory and add the required values. Since this project supports (managed) identity-based authentication for Azure services, it's recommended not to store any keys in the .env file.

#### (optional) Identity Based Authentication

It is recommended to use managed identity-based authentication for Azure services, even during development. This project leverages the DefaultAzureCredential, which supports multiple authentication methods, such as environment variables, managed identity, and more.

1. Login to Azure using the Azure CLI and select your subscription.

```bash
az login
```

1. Assign roles. Ensure your user account has the necessary roles to access the Azure services. You can assign these roles using the Azure Portal (IAM) or the Azure CLI.

```bash
# Assign roles using Azure CLI
az role assignment create --assignee <your-user-id> --role "Cognitive Service User" --scope <resource-scope>
az role assignment create --assignee <your-user-id> --role "Cognitive Services OpenAI User" --scope <resource-scope>
az role assignment create --assignee <your-user-id> --role "Cognitive Services Speech User" --scope <resource-scope>
```

| Azure Resource              | Roles                                                    |
| --------------------------- | -------------------------------------------------------- |
| Azure Document Intelligence | Cognitive Service User                                   |
| Azure OpenAI Service        | Cognitive Services OpenAI User or Cognitive Service User |
| Azure AI Speech             | Cognitive Services Speech User or Cognitive Service User |


For Microsoft Entra authentication with Speech resources, you need to assign either the Cognitive Services Speech Contributor or Cognitive Services Speech User role.

1. To support Microsoft Entra authentication with Azure AI Speech, you need to [create a custom domain name](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-configure-azure-ad-auth?tabs=portal&pivots=programming-language-python#create-a-custom-domain-name).

1. [Get the Speech resource ID](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-configure-azure-ad-auth?tabs=portal&pivots=programming-language-python#get-the-speech-resource-id) and set the `AZURE_SPEECH_RESOURCE_ID` environment variable.

#### Start the development server

```bash

Start the development Streamlit server using the command below. It will launch on port 8065.

```bash
uv run streamlit run app/app.py
```

### Deploy on Azure

This repository includes the code for the Azure Podcast Generator, but infrastructure-as-code is not currently provided. You can use the [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/) to deploy the container to Azure Container Apps.


```bash
az containerapp up --resource-group your-rg-name \
--name your-app-name --location westeurope \
--ingress external --target-port 9000 --source . \
--env-vars DOCUMENTINTELLIGENCE_ENDPOINT="" AZURE_OPENAI_ENDPOINT="" AZURE_OPENAI_MODEL_DEPLOYMENT="gpt-4o" AZURE_SPEECH_RESOURCE_ID="" AZURE_SPEECH_REGION="westeurope"
```

It is advised to set the [sticky-sessions](https://learn.microsoft.com/en-us/azure/container-apps/sticky-sessions?pivots=azure-portal) to `sticky` using the command below, to prevent any issues with file-uploads.

```bash
az containerapp ingress sticky-sessions set --affinity sticky --name your-app-name --resource-group your-rg-name
```


## Inspired by
- Google NotebookLM
- [New HD voices preview in Azure AI Speech](https://techcommunity.microsoft.com/t5/ai-azure-ai-services-blog/new-hd-voices-preview-in-azure-ai-speech-contextual-and/ba-p/4258325)
