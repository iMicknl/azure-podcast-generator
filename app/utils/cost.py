"""Module for cost calculation utils."""


def calculate_azure_document_intelligence_costs(pages: int) -> float:
    """
    Calculate Azure Document Intelligence costs.
    The cost for Prebuilt Models (Layout) is $10 per 1,000 pages.

    Output in USD.
    """
    cost = 10 * (pages / 1_000)

    return cost


def calculate_azure_ai_speech_costs(characters: int) -> float:
    """
    Calculate Azure AI Speech costs.
    The cost for HD voices is $30 per 1 million characters.

    Output in USD.
    """
    cost = 30 * (characters / 1_000_000)

    return cost


def calculate_azure_openai_costs(input_tokens: int, output_tokens: int) -> float:
    """
    Calculate Azure OpenAI costs.

    The cost for gpt-4o-2024-08-06 input (per 1,000,000 tokens) is $2.75 (regional deployment)
    The cost for gpt-4o-2024-08-06 output (per 1,000,000 tokens) is $11 (regional deployment)

    Output in USD.
    """
    cost = 2.75 * (input_tokens / 1_000_000) + 11 * (output_tokens / 1_000_000)

    return cost
