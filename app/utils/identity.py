"""Module for Azure identity utils."""

import base64
import json
from datetime import timedelta

import streamlit as st
from azure.core.credentials import AccessToken
from azure.identity import DefaultAzureCredential, get_bearer_token_provider


@st.cache_resource
def get_azure_credential():
    return DefaultAzureCredential()


@st.cache_resource
def get_token_provider():
    """Get Azure Token Provider."""

    token_provider = get_bearer_token_provider(
        get_azure_credential(), "https://cognitiveservices.azure.com/.default"
    )
    return token_provider


@st.cache_data(
    ttl=timedelta(minutes=60)
)  # Temporary fix, need to add cache for exact lifetime of token
def get_access_token(
    scope: str = "https://cognitiveservices.azure.com/.default",
) -> AccessToken:
    """Get Microsoft Entra access token for scope."""

    token_credential = get_azure_credential()
    token = token_credential.get_token(scope)

    return token


def get_speech_token(resource_id: str) -> str:
    """Create  Service token."""

    access_token = get_access_token()
    # You need to include the "aad#" prefix and the "#" (hash) separator between resource ID and Microsoft Entra access token.
    authorization_token = "aad#" + resource_id + "#" + access_token.token

    return authorization_token


def check_claim_for_tenant(client_principal: str, authorized_tenants: list):
    """Check if claim is authorized tenant."""

    decoded_bytes = base64.b64decode(client_principal.encode("utf-8"))
    decoded_str = decoded_bytes.decode("utf-8")
    client_principal = json.loads(decoded_str)
    tenant_id = next(
        (
            claim["val"]
            for claim in client_principal["claims"]
            if claim["typ"] == "http://schemas.microsoft.com/identity/claims/tenantid"
        ),
        None,
    )

    return tenant_id in authorized_tenants
