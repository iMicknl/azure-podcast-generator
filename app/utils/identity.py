from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.core.credentials import AccessToken
from datetime import timedelta
import streamlit as st


def get_token_provider():
    """Get Azure Token Provider."""
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
    )
    return token_provider


@st.cache_data(
    ttl=timedelta(minutes=60)
)  # Temporary fix, need to add cache for exact lifetime of token
def get_token(
    scope: str = "https://cognitiveservices.azure.com/.default",
) -> AccessToken:
    """Get Azure token for scope."""
    token_credential = DefaultAzureCredential()
    token = token_credential.get_token(scope)

    return token


def create_speech_token(resource_id: str) -> str:
    """Create Azure Speech Service token."""

    aadToken = get_token()
    # You need to include the "aad#" prefix and the "#" (hash) separator between resource ID and Microsoft Entra access token.
    authorization_token = "aad#" + resource_id + "#" + aadToken.token

    return authorization_token
