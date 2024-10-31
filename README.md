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

If you're running Windows, also make sure you have installed `cmake`, and adding the `cmake` path to your environment variables. You can do this by installing the C++ Desktop Development workload in the Visual Studio Installer and adding `C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin` to your PATH environment variable.

You can install the required dependencies via the command below using uv.

```bash
uv sync
```

Configure the necessary environment variables in the .env file or your environment settings. The required values can be found in the [.env.sample](./app/.env.sample) file. Since this project supports (managed) identity-based authentication for Azure services, it's recommended not to store any keys in the .env file.

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
