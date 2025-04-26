"""Module for LLM utils."""

import json
import os
import time
import random
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Tuple

import streamlit as st
import tiktoken
from openai import AzureOpenAI, APIError, RateLimitError, APIConnectionError
from openai.types import CompletionUsage
from utils.identity import get_token_provider

AZURE_OPENAI_API_VERSION = "2024-10-21"

class PodcastStyle(Enum):
    """Podcast styles with predefined formats."""
    HUBERMAN_LAB = auto()  # Scientific, educational focus
    JOE_ROGAN = auto()  # Conversational, long-form
    RADIOLAB = auto()  # Narrative-driven with storytelling
    PLANET_MONEY = auto()  # Explaining complex topics through examples
    TED_TALKS = auto()  # Concise, idea-focused
    NEWS_BRIEFING = auto()  # Brief updates with minimal elaboration

class PodcastTone(Enum):
    """Podcast tone options."""
    CONVERSATIONAL = auto()
    EDUCATIONAL = auto()
    ANALYTICAL = auto()
    NARRATIVE = auto()
    INSPIRATIONAL = auto()
    TECHNICAL = auto()

# Define podcast style formats with descriptions
PODCAST_STYLE_FORMATS = {
    PodcastStyle.HUBERMAN_LAB: """
    Huberman Lab (scientific, educational focus):
    - Begins with a scientific question or topic
    - Host presents scientific concepts and research in accessible language
    - Discusses practical applications of the science
    - Methodical, educational approach with clear explanations
    - Concludes with actionable insights based on the research
    """,
    
    PodcastStyle.JOE_ROGAN: """
    Joe Rogan Experience (conversational, long-form):
    - Casual, free-flowing conversation between hosts
    - Deep dives into topics with tangential discussions
    - Personal anecdotes and experiences related to the topic
    - Devil's advocate questioning to explore different angles
    - Emphasis on entertaining dialogue over structured format
    """,
    
    PodcastStyle.RADIOLAB: """
    Radiolab (narrative-driven with storytelling):
    - Creative storytelling approach to explain concepts
    - Uses narrative devices like character development and story arcs
    - Incorporates sound design elements into the script (sound effect descriptions)
    - Weaves between personal stories and factual information
    - Creates moments of surprise and wonder through storytelling techniques
    """,
    
    PodcastStyle.PLANET_MONEY: """
    Planet Money (explaining complex topics through examples):
    - Begins with a relatable real-world scenario
    - Uses concrete examples and analogies to explain complex ideas
    - Breaks down complicated concepts step by step
    - Incorporates relevant history or context
    - Ends with the "so what" - why this matters to the listener
    """,
    
    PodcastStyle.TED_TALKS: """
    TED Talks Daily (concise, idea-focused):
    - Clear thesis statement at the beginning
    - Structured presentation of 2-3 main supporting points
    - Minimal tangents, stays focused on core message
    - Uses compelling evidence or data to support claims
    - Ends with an inspiring call to action or thought-provoking conclusion
    """,
    
    PodcastStyle.NEWS_BRIEFING: """
    News Briefing (brief updates with minimal elaboration):
    - Concise headline-style introduction of topics
    - Brief, factual summaries of the main points
    - Minimal editorializing or opinion
    - Clear transitions between different topics or sections
    - Quick closing with key takeaways
    """
}

# Define podcast tone descriptions
PODCAST_TONE_DESCRIPTIONS = {
    PodcastTone.CONVERSATIONAL: "Friendly, casual dialogue that feels like a chat between friends. Uses colloquial language, personal anecdotes, and humor.",
    PodcastTone.EDUCATIONAL: "Clear explanations with defined concepts. Structured like a lesson with introduction, explanation, and summary.",
    PodcastTone.ANALYTICAL: "Logical, evidence-based approach. Examines multiple perspectives, cites research, and draws reasoned conclusions.",
    PodcastTone.NARRATIVE: "Story-driven format with characters, plot development, and emotional arcs. Creates immersive experiences through storytelling.",
    PodcastTone.INSPIRATIONAL: "Uplifting, motivational tone. Uses emotional appeals, aspirational examples, and empowering language.",
    PodcastTone.TECHNICAL: "Detailed, precise language with domain-specific terminology. In-depth exploration of technical concepts for knowledgeable audiences."
}

# ReAct system prompt
REACT_SYSTEM_PROMPT = """
You are an expert podcast script writer creating engaging dual-voice podcasts using a structured ReAct (Reasoning + Acting) approach.

# Overall parameters
- Title: "{title}"
- Target duration: {duration} minutes
- Podcast style: {podcast_style}
- Tone: {podcast_tone}
- Content depth (1-5): {content_depth}
- Host names: {voice_1} and {voice_2}

# Your Task
You will generate a podcast script through a series of reasoning and action steps. Each step builds on the previous ones to create a cohesive, engaging podcast.

# Functions Available
You have access to the following functions:
1. analyze_content - Analyze the document to extract key points and themes
2. plan_structure - Create a podcast structure with timing estimates
3. develop_characters - Define distinct personalities for the hosts
4. generate_section - Generate dialogue for a specific section
5. review_and_refine - Review and improve the script
6. finalize_script - Finalize the script in the required JSON format

# Process
For each step, first REASON about what needs to be done, then select an ACTION to take.
Always include your reasoning and selected action in this format:

<reasoning>
Your detailed reasoning...
</reasoning>

<action>
function_name: The function you want to call
parameters: The parameters for the function
</action>

# Important Notes
- Adapt complexity to content depth level {content_depth} (1=basic overview, 5=technical deep dive)
- Maintain coherent flow from introduction through conclusion
- Use language appropriate to the selected tone and style
- Keep technical accuracy while making content engaging
- Think step by step and follow the ReAct process
""".strip()

# Define function schemas for ReAct process
REACT_FUNCTION_SCHEMAS = [
    {
        "name": "analyze_content",
        "description": "Analyze the document to identify key themes, points, and structure",
        "parameters": {
            "type": "object",
            "properties": {
                "key_points": {
                    "type": "array",
                    "description": "3-5 key points from the document that will form the basis of the podcast",
                    "items": {"type": "string"}
                },
                "themes": {
                    "type": "array",
                    "description": "Main themes identified in the document",
                    "items": {"type": "string"}
                },
                "audience_takeaways": {
                    "type": "array",
                    "description": "Key takeaways for the audience",
                    "items": {"type": "string"}
                }
            },
            "required": ["key_points", "themes", "audience_takeaways"]
        }
    },
    {
        "name": "plan_structure",
        "description": "Plan the podcast structure with time allocations",
        "parameters": {
            "type": "object",
            "properties": {
                "sections": {
                    "type": "array",
                    "description": "Sections of the podcast with timing",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Section title"},
                            "duration": {"type": "number", "description": "Approximate duration in minutes"},
                            "description": {"type": "string", "description": "Brief description of what will be covered"}
                        },
                        "required": ["title", "duration", "description"]
                    }
                },
                "total_duration": {"type": "number", "description": "Total estimated duration in minutes"}
            },
            "required": ["sections", "total_duration"]
        }
    },
    {
        "name": "develop_characters",
        "description": "Define distinct personalities for the podcast hosts",
        "parameters": {
            "type": "object",
            "properties": {
                "host_1": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Host name"},
                        "personality": {"type": "string", "description": "Personality traits and speaking style"},
                        "role": {"type": "string", "description": "Primary role in the podcast"}
                    },
                    "required": ["name", "personality", "role"]
                },
                "host_2": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Host name"},
                        "personality": {"type": "string", "description": "Personality traits and speaking style"},
                        "role": {"type": "string", "description": "Primary role in the podcast"}
                    },
                    "required": ["name", "personality", "role"]
                }
            },
            "required": ["host_1", "host_2"]
        }
    },
    {
        "name": "generate_section",
        "description": "Generate dialogue for a specific section of the podcast",
        "parameters": {
            "type": "object",
            "properties": {
                "section_title": {"type": "string", "description": "Title of the section"},
                "dialogue": {
                    "type": "array",
                    "description": "Dialogue exchanges for this section",
                    "items": {
                        "type": "object",
                        "properties": {
                            "speaker": {"type": "string", "description": "Name of the speaker"},
                            "text": {"type": "string", "description": "What the speaker says"}
                        },
                        "required": ["speaker", "text"]
                    }
                }
            },
            "required": ["section_title", "dialogue"]
        }
    },
    {
        "name": "review_and_refine",
        "description": "Review and improve the script for flow, style, and accuracy",
        "parameters": {
            "type": "object",
            "properties": {
                "improvements": {
                    "type": "array",
                    "description": "Improvements made to the script",
                    "items": {"type": "string"}
                },
                "dialogue_revisions": {
                    "type": "array",
                    "description": "Specific dialogue revisions (optional)",
                    "items": {
                        "type": "object",
                        "properties": {
                            "section": {"type": "string", "description": "Section title"},
                            "original": {"type": "string", "description": "Original dialogue"},
                            "revised": {"type": "string", "description": "Revised dialogue"}
                        },
                        "required": ["section", "original", "revised"]
                    }
                }
            },
            "required": ["improvements"]
        }
    },
    {
        "name": "finalize_script",
        "description": "Finalize the script in the required JSON format",
        "parameters": {
            "type": "object",
            "properties": {
                "config": {
                    "type": "object",
                    "properties": {
                        "language": {"type": "string", "description": "Language code (e.g., en-US)"}
                    },
                    "required": ["language"]
                },
                "script": {
                    "type": "array",
                    "description": "The complete podcast script",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Speaker name"},
                            "message": {"type": "string", "description": "Speaker's dialogue"}
                        },
                        "required": ["name", "message"]
                    }
                }
            },
            "required": ["config", "script"]
        }
    }
]

JSON_SCHEMA = {
    "name": "podcast",
    "strict": True,
    "description": "An AI generated podcast script.",
    "schema": {
        "type": "object",
        "properties": {
            "config": {
                "type": "object",
                "properties": {
                    "language": {
                        "type": "string",
                        "description": "Language code + locale (BCP-47), e.g. en-US or es-PA",
                    }
                },
                "required": ["language"],
                "additionalProperties": False,
            },
            "script": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the host. Use the provided names, don't change the casing or name.",
                        },
                        "message": {"type": "string"},
                    },
                    "required": ["name", "message"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["config", "script"],
        "additionalProperties": False,
    },
}


@dataclass
class PodcastScriptResponse:
    podcast: dict
    usage: CompletionUsage
    generation_steps: List[Dict[str, Any]]  # Track reasoning and actions


def get_podcast_style_name(style: PodcastStyle) -> str:
    """Convert enum to human-readable name."""
    style_names = {
        PodcastStyle.HUBERMAN_LAB: "Huberman Lab (scientific, educational focus)",
        PodcastStyle.JOE_ROGAN: "Joe Rogan Experience (conversational, long-form)",
        PodcastStyle.RADIOLAB: "Radiolab (narrative-driven with storytelling)",
        PodcastStyle.PLANET_MONEY: "Planet Money (explaining complex topics through examples)",
        PodcastStyle.TED_TALKS: "TED Talks Daily (concise, idea-focused)",
        PodcastStyle.NEWS_BRIEFING: "News Briefing (brief updates with minimal elaboration)",
    }
    return style_names.get(style, "Custom Style")


def get_podcast_tone_name(tone: PodcastTone) -> str:
    """Convert enum to human-readable name."""
    tone_names = {
        PodcastTone.CONVERSATIONAL: "Conversational",
        PodcastTone.EDUCATIONAL: "Educational",
        PodcastTone.ANALYTICAL: "Analytical",
        PodcastTone.NARRATIVE: "Narrative",
        PodcastTone.INSPIRATIONAL: "Inspirational",
        PodcastTone.TECHNICAL: "Technical",
    }
    return tone_names.get(tone, "Conversational")


def execute_react_step_with_retry(
    client: AzureOpenAI,
    model: str,
    messages: List[Dict],
    function_schemas: List[Dict[str, Any]],
    temperature: float = 0.7,
    max_retries: int = 3,
    initial_retry_delay: float = 1.0,
    status_callback=None
) -> Tuple[Dict[str, Any], CompletionUsage]:
    """Execute a single ReAct step with function calling and retry logic."""
    
    retry_count = 0
    retry_delay = initial_retry_delay
    last_error = None
    
    while retry_count <= max_retries:
        try:
            if retry_count > 0 and status_callback:
                status_callback(f"Retrying... (attempt {retry_count}/{max_retries})")
                
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=[{"type": "function", "function": schema} for schema in function_schemas],
                tool_choice="auto",
                temperature=temperature,
            )
            
            message = response.choices[0].message
            function_call = None
            
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                function_call = {
                    "name": tool_call.function.name,
                    "arguments": json.loads(tool_call.function.arguments)
                }
            
            return {
                "message": message.content or "",  # Ensure content is never None
                "function_call": function_call
            }, response.usage
            
        except (APIError, RateLimitError, APIConnectionError) as e:
            last_error = e
            retry_count += 1
            
            if retry_count <= max_retries:
                # Exponential backoff with jitter
                jitter = random.uniform(0.8, 1.2)
                sleep_time = retry_delay * jitter
                if status_callback:
                    status_callback(f"API error: {str(e)}. Retrying in {sleep_time:.1f}s...")
                time.sleep(sleep_time)
                retry_delay *= 2  # Exponential backoff
            else:
                if status_callback:
                    status_callback(f"Max retries ({max_retries}) exceeded. Last error: {str(e)}")
                raise
                
        except Exception as e:
            # Non-retriable error
            if status_callback:
                status_callback(f"Non-retriable error: {str(e)}")
            raise
    
    # This should not be reached due to the raise in the else clause above
    # But keeping it as a fallback
    raise last_error or Exception("Max retries exceeded with an unknown error")


def document_to_podcast_script(
    document: str,
    title: str = "AI in Action",
    voice_1: str = "Andrew",
    voice_2: str = "Emma",
    max_tokens: int = 8000,
    duration: int = 5,
    podcast_style: PodcastStyle = PodcastStyle.TED_TALKS,
    podcast_tone: PodcastTone = PodcastTone.CONVERSATIONAL,
    content_depth: int = 3,
    temperature: float = 0.7,
    show_steps: bool = False,  # Whether to show the generation steps in the UI
    max_retries: int = 3,  # Maximum number of retries per step
) -> PodcastScriptResponse:
    """Generate podcast script using true multi-turn ReAct approach with retry mechanism."""

    # Authenticate via API key (not advised for production)
    if os.getenv("AZURE_OPENAI_KEY"):
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        )
    # Authenticate via DefaultAzureCredential (e.g. managed identity or Azure CLI)
    else:
        client = AzureOpenAI(
            api_version=AZURE_OPENAI_API_VERSION,
            azure_ad_token_provider=get_token_provider(),
        )

    # Format the ReAct system prompt with user parameters
    formatted_system_prompt = REACT_SYSTEM_PROMPT.format(
        title=title,
        duration=duration,
        podcast_style=PODCAST_STYLE_FORMATS[podcast_style],
        podcast_tone=PODCAST_TONE_DESCRIPTIONS[podcast_tone],
        content_depth=content_depth,
        voice_1=voice_1,
        voice_2=voice_2,
    )
    
    # Initialize conversation with system prompt
    messages = [
        {"role": "system", "content": formatted_system_prompt},
        {"role": "user", "content": f"<title>{title}</title><documents><document>{document}</document></documents>"}
    ]
    
    model = os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT", "gpt-4o")
    
    # Track generation steps for UI display if requested
    generation_steps = []
    
    # Track accumulated tokens to stay within limits
    total_prompt_tokens = 0
    total_completion_tokens = 0
    
    # Display progress in Streamlit if available
    progress_bar = None
    step_status = None
    if show_steps and "st" in globals():
        progress_bar = st.progress(0)
        step_status = st.empty()
    
    def update_status(message):
        """Update status message if Streamlit UI is available."""
        if step_status:
            current_text = step_status.text or ""
            step_status.text(f"{current_text}\n{message}")
    
    # Storage for intermediate results
    content_analysis = {}
    podcast_structure = {}
    host_characters = {}
    sections = {}
    final_script = None
    
    # Recover function to restart from a specific step if needed
    def recover_generation_state(error_step):
        """Generate a simplified state to recover from error."""
        if error_step <= 0:  # Content Analysis failed
            content_analysis = {
                "key_points": ["Key point extracted from document"],
                "themes": ["Main theme of the document"],
                "audience_takeaways": ["What the audience should learn"]
            }
            return content_analysis
        
        if error_step <= 1:  # Structure Planning failed
            return {
                "sections": [
                    {
                        "title": "Introduction",
                        "duration": duration * 0.2,
                        "description": "Introduction to the topic"
                    },
                    {
                        "title": "Main Content",
                        "duration": duration * 0.6,
                        "description": "Main discussion of the topic"
                    },
                    {
                        "title": "Conclusion",
                        "duration": duration * 0.2,
                        "description": "Summary and takeaways"
                    }
                ],
                "total_duration": duration
            }
        
        if error_step <= 2:  # Character Development failed
            return {
                "host_1": {
                    "name": voice_1,
                    "personality": "Friendly and engaging",
                    "role": "Main host who guides the conversation"
                },
                "host_2": {
                    "name": voice_2,
                    "personality": "Curious and insightful",
                    "role": "Co-host who asks questions and provides additional perspectives"
                }
            }
        
        # For other steps, we need context-specific recovery that's harder to generalize
        return None
    
    try:
        # Step 1: Content Analysis
        if show_steps and progress_bar and step_status:
            step_status.text("Step 1/6: Analyzing content...")
            progress_bar.progress(0)
        
        try:
            step_result, usage = execute_react_step_with_retry(
                client, model, messages, REACT_FUNCTION_SCHEMAS[:1], temperature, 
                max_retries=max_retries, status_callback=update_status
            )
            
            messages.append({"role": "assistant", "content": step_result["message"]})
            if step_result["function_call"]:
                content_analysis = step_result["function_call"]["arguments"]
                # Add function call to messages
                tool_call_id = f"call_{len(messages)}"
                messages.append({
                    "role": "assistant", 
                    "content": None,
                    "tool_calls": [{
                        "id": tool_call_id,
                        "type": "function",
                        "function": {
                            "name": step_result["function_call"]["name"],
                            "arguments": json.dumps(step_result["function_call"]["arguments"])
                        }
                    }]
                })
                # Add function response
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": json.dumps({"result": "Analysis completed successfully"})
                })
            
            generation_steps.append({
                "step": "Content Analysis",
                "reasoning": step_result["message"],
                "action": content_analysis
            })
            
            total_prompt_tokens += usage.prompt_tokens
            total_completion_tokens += usage.completion_tokens
        except Exception as e:
            update_status(f"Error in Content Analysis step: {str(e)}")
            # Try to recover with a simplified analysis
            content_analysis = recover_generation_state(0)
            if not content_analysis:
                raise
                
            generation_steps.append({
                "step": "Content Analysis (Recovery)",
                "reasoning": "Error occurred, using simplified analysis",
                "action": content_analysis
            })
            
            # Add recovery content to messages
            tool_call_id = f"recovery_call_{len(messages)}"
            messages.append({
                "role": "assistant", 
                "content": "I've analyzed the content of the document.",
                "tool_calls": [{
                    "id": tool_call_id,
                    "type": "function",
                    "function": {
                        "name": "analyze_content",
                        "arguments": json.dumps(content_analysis)
                    }
                }]
            })
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": json.dumps({"result": "Analysis completed (recovery mode)"})
            })
        
        # Step 2: Structure Planning
        if show_steps and progress_bar and step_status:
            step_status.text("Step 2/6: Planning podcast structure...")
            progress_bar.progress(1/6)
        
        try:
            step_result, usage = execute_react_step_with_retry(
                client, model, messages, REACT_FUNCTION_SCHEMAS[1:2], temperature,
                max_retries=max_retries, status_callback=update_status
            )
            
            messages.append({"role": "assistant", "content": step_result["message"]})
            if step_result["function_call"]:
                podcast_structure = step_result["function_call"]["arguments"]
                # Add function call to messages
                tool_call_id = f"call_{len(messages)}"
                messages.append({
                    "role": "assistant", 
                    "content": None,
                    "tool_calls": [{
                        "id": tool_call_id,
                        "type": "function",
                        "function": {
                            "name": step_result["function_call"]["name"],
                            "arguments": json.dumps(step_result["function_call"]["arguments"])
                        }
                    }]
                })
                # Add function response
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": json.dumps({"result": "Structure planning completed successfully"})
                })
            
            generation_steps.append({
                "step": "Structure Planning",
                "reasoning": step_result["message"],
                "action": podcast_structure
            })
            
            total_prompt_tokens += usage.prompt_tokens
            total_completion_tokens += usage.completion_tokens
        except Exception as e:
            update_status(f"Error in Structure Planning step: {str(e)}")
            # Try to recover with a simplified structure
            podcast_structure = recover_generation_state(1)
            if not podcast_structure:
                raise
                
            generation_steps.append({
                "step": "Structure Planning (Recovery)",
                "reasoning": "Error occurred, using simplified structure",
                "action": podcast_structure
            })
            
            # Add recovery content to messages
            tool_call_id = f"recovery_call_{len(messages)}"
            messages.append({
                "role": "assistant", 
                "content": "I've planned the podcast structure.",
                "tool_calls": [{
                    "id": tool_call_id,
                    "type": "function",
                    "function": {
                        "name": "plan_structure",
                        "arguments": json.dumps(podcast_structure)
                    }
                }]
            })
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": json.dumps({"result": "Structure planning completed (recovery mode)"})
            })
        
        # Step 3: Character Development
        if show_steps and progress_bar and step_status:
            step_status.text("Step 3/6: Developing host characters...")
            progress_bar.progress(2/6)
        
        try:
            step_result, usage = execute_react_step_with_retry(
                client, model, messages, REACT_FUNCTION_SCHEMAS[2:3], temperature,
                max_retries=max_retries, status_callback=update_status
            )
            
            messages.append({"role": "assistant", "content": step_result["message"]})
            if step_result["function_call"]:
                host_characters = step_result["function_call"]["arguments"]
                # Add function call to messages
                tool_call_id = f"call_{len(messages)}"
                messages.append({
                    "role": "assistant", 
                    "content": None,
                    "tool_calls": [{
                        "id": tool_call_id,
                        "type": "function",
                        "function": {
                            "name": step_result["function_call"]["name"],
                            "arguments": json.dumps(step_result["function_call"]["arguments"])
                        }
                    }]
                })
                # Add function response
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": json.dumps({"result": "Character development completed successfully"})
                })
            
            generation_steps.append({
                "step": "Character Development",
                "reasoning": step_result["message"],
                "action": host_characters
            })
            
            total_prompt_tokens += usage.prompt_tokens
            total_completion_tokens += usage.completion_tokens
        except Exception as e:
            update_status(f"Error in Character Development step: {str(e)}")
            # Try to recover with simplified characters
            host_characters = recover_generation_state(2)
            if not host_characters:
                raise
                
            generation_steps.append({
                "step": "Character Development (Recovery)",
                "reasoning": "Error occurred, using simplified character definitions",
                "action": host_characters
            })
            
            # Add recovery content to messages
            tool_call_id = f"recovery_call_{len(messages)}"
            messages.append({
                "role": "assistant", 
                "content": "I've developed the host characters.",
                "tool_calls": [{
                    "id": tool_call_id,
                    "type": "function",
                    "function": {
                        "name": "develop_characters",
                        "arguments": json.dumps(host_characters)
                    }
                }]
            })
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": json.dumps({"result": "Character development completed (recovery mode)"})
            })
        
        # Step 4: Generate Sections (multiple iterations for each section)
        if "sections" in podcast_structure:
            section_retry_counts = {}  # Track retries for each section
            
            for i, section in enumerate(podcast_structure["sections"]):
                section_title = section.get("title", f"Section {i+1}")
                section_retry_counts[section_title] = 0
                section_generated = False
                
                while section_retry_counts[section_title] <= max_retries and not section_generated:
                    try:
                        if show_steps and progress_bar and step_status:
                            progress = (3 + i/len(podcast_structure["sections"]))/6
                            retry_text = f" (retry {section_retry_counts[section_title]})" if section_retry_counts[section_title] > 0 else ""
                            step_status.text(f"Step 4/6: Generating section {i+1}/{len(podcast_structure['sections'])}: {section_title}{retry_text}...")
                            progress_bar.progress(progress)
                        
                        step_result, usage = execute_react_step_with_retry(
                            client, model, messages, REACT_FUNCTION_SCHEMAS[3:4], temperature,
                            max_retries=max_retries, status_callback=update_status
                        )
                        
                        messages.append({"role": "assistant", "content": step_result["message"]})
                        if step_result["function_call"]:
                            section_content = step_result["function_call"]["arguments"]
                            sections[section_content["section_title"]] = section_content
                            # Add function call to messages
                            tool_call_id = f"call_{len(messages)}"
                            messages.append({
                                "role": "assistant", 
                                "content": None,
                                "tool_calls": [{
                                    "id": tool_call_id,
                                    "type": "function",
                                    "function": {
                                        "name": step_result["function_call"]["name"],
                                        "arguments": json.dumps(step_result["function_call"]["arguments"])
                                    }
                                }]
                            })
                            # Add function response
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": json.dumps({"result": f"Section '{section_content['section_title']}' generated successfully"})
                            })
                            
                            generation_steps.append({
                                "step": f"Section Generation: {section_title}",
                                "reasoning": step_result["message"],
                                "action": section_content
                            })
                            
                            section_generated = True
                        
                        total_prompt_tokens += usage.prompt_tokens
                        total_completion_tokens += usage.completion_tokens
                        
                    except Exception as e:
                        section_retry_counts[section_title] += 1
                        update_status(f"Error generating section '{section_title}' (retry {section_retry_counts[section_title]}/{max_retries}): {str(e)}")
                        
                        if section_retry_counts[section_title] > max_retries:
                            # Create a basic fallback section
                            fallback_section = {
                                "section_title": section_title,
                                "dialogue": [
                                    {"speaker": voice_1, "text": f"Let's talk about {section_title}."},
                                    {"speaker": voice_2, "text": f"Yes, this is an important topic from the document."},
                                    {"speaker": voice_1, "text": "The key points to remember are..."},
                                    {"speaker": voice_2, "text": "That's a great summary. Let's move on to the next section."}
                                ]
                            }
                            
                            sections[section_title] = fallback_section
                            
                            # Add fallback to conversation
                            tool_call_id = f"recovery_call_{len(messages)}"
                            messages.append({
                                "role": "assistant", 
                                "content": f"I've generated content for section '{section_title}'.",
                                "tool_calls": [{
                                    "id": tool_call_id,
                                    "type": "function",
                                    "function": {
                                        "name": "generate_section",
                                        "arguments": json.dumps(fallback_section)
                                    }
                                }]
                            })
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": json.dumps({"result": f"Section '{section_title}' generated (fallback mode)"})
                            })
                            
                            generation_steps.append({
                                "step": f"Section Generation: {section_title} (Fallback)",
                                "reasoning": f"Error occurred after {max_retries} retries, using fallback section",
                                "action": fallback_section
                            })
                            
                            section_generated = True
        
        # Step 5: Review and Refine
        if show_steps and progress_bar and step_status:
            step_status.text("Step 5/6: Reviewing and refining...")
            progress_bar.progress(4/6)
        
        try:
            step_result, usage = execute_react_step_with_retry(
                client, model, messages, REACT_FUNCTION_SCHEMAS[4:5], temperature,
                max_retries=max_retries, status_callback=update_status
            )
            
            messages.append({"role": "assistant", "content": step_result["message"]})
            if step_result["function_call"]:
                refinements = step_result["function_call"]["arguments"]
                # Add function call to messages
                tool_call_id = f"call_{len(messages)}"
                messages.append({
                    "role": "assistant", 
                    "content": None,
                    "tool_calls": [{
                        "id": tool_call_id,
                        "type": "function",
                        "function": {
                            "name": step_result["function_call"]["name"],
                            "arguments": json.dumps(step_result["function_call"]["arguments"])
                        }
                    }]
                })
                # Add function response
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": json.dumps({"result": "Review and refinement completed successfully"})
                })
            
            generation_steps.append({
                "step": "Review and Refinement",
                "reasoning": step_result["message"],
                "action": refinements if step_result["function_call"] else None
            })
            
            total_prompt_tokens += usage.prompt_tokens
            total_completion_tokens += usage.completion_tokens
            
        except Exception as e:
            update_status(f"Error in Review step: {str(e)}")
            # Create minimal refinements
            minimal_refinements = {
                "improvements": ["Ensured consistent tone throughout the podcast", 
                                "Balanced speaking time between hosts"]
            }
            
            # Add fallback to conversation
            tool_call_id = f"recovery_call_{len(messages)}"
            messages.append({
                "role": "assistant", 
                "content": "I've reviewed and refined the script.",
                "tool_calls": [{
                    "id": tool_call_id,
                    "type": "function",
                    "function": {
                        "name": "review_and_refine",
                        "arguments": json.dumps(minimal_refinements)
                    }
                }]
            })
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": json.dumps({"result": "Review completed (minimal mode)"})
            })
            
            generation_steps.append({
                "step": "Review and Refinement (Minimal)",
                "reasoning": "Error occurred, providing minimal refinements",
                "action": minimal_refinements
            })
        
        # Step 6: Finalize Script
        if show_steps and progress_bar and step_status:
            step_status.text("Step 6/6: Finalizing podcast script...")
            progress_bar.progress(5/6)
        
        try:
            step_result, usage = execute_react_step_with_retry(
                client, model, messages, REACT_FUNCTION_SCHEMAS[5:], temperature,
                max_retries=max_retries, status_callback=update_status
            )
            
            messages.append({"role": "assistant", "content": step_result["message"]})
            if step_result["function_call"]:
                final_script = step_result["function_call"]["arguments"]
                # Add function call to messages
                tool_call_id = f"call_{len(messages)}"
                messages.append({
                    "role": "assistant", 
                    "content": None,
                    "tool_calls": [{
                        "id": tool_call_id,
                        "type": "function",
                        "function": {
                            "name": step_result["function_call"]["name"],
                            "arguments": json.dumps(step_result["function_call"]["arguments"])
                        }
                    }]
                })
                # Add function response
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": json.dumps({"result": "Script finalization completed successfully"})
                })
            
            generation_steps.append({
                "step": "Script Finalization",
                "reasoning": step_result["message"],
                "action": final_script
            })
            
            total_prompt_tokens += usage.prompt_tokens
            total_completion_tokens += usage.completion_tokens
            
        except Exception as e:
            update_status(f"Error in Script Finalization step: {str(e)}")
            
            # Build emergency final script from collected sections
            emergency_script = {"config": {"language": "en-US"}, "script": []}
            
            # Add introduction
            emergency_script["script"].append({"name": voice_1, "message": f"Welcome to {title}! I'm {voice_1} and with me is {voice_2}."})
            emergency_script["script"].append({"name": voice_2, "message": f"Thanks {voice_1}, I'm excited to discuss this topic with you today."})
            
            # Add content from sections
            for section_title, section in sections.items():
                if "dialogue" in section:
                    for dialogue in section["dialogue"]:
                        emergency_script["script"].append({
                            "name": dialogue["speaker"],
                            "message": dialogue["text"]
                        })
            
            # Add conclusion if script is too short
            if len(emergency_script["script"]) < 6:
                emergency_script["script"].append({"name": voice_1, "message": "Let's summarize what we've discussed today."})
                emergency_script["script"].append({"name": voice_2, "message": "I think the key takeaways are the points we mentioned earlier."})
                emergency_script["script"].append({"name": voice_1, "message": f"Thanks for listening to {title}! I'm {voice_1}..."})
                emergency_script["script"].append({"name": voice_2, "message": f"And I'm {voice_2}. See you next time!"})
            
            final_script = emergency_script
            
            generation_steps.append({
                "step": "Script Finalization (Emergency)",
                "reasoning": "Error occurred, using emergency script compilation",
                "action": final_script
            })
        
        if show_steps and progress_bar and step_status:
            progress_bar.progress(1.0)
            step_status.text("Podcast script generation complete!")
        
        # Build final usage object
        total_usage = CompletionUsage(
            prompt_tokens=total_prompt_tokens,
            completion_tokens=total_completion_tokens,
            total_tokens=total_prompt_tokens + total_completion_tokens
        )
        
        # Return the final script and generation details
        return PodcastScriptResponse(
            podcast=final_script if final_script else {"config": {"language": "en-US"}, "script": []},
            usage=total_usage,
            generation_steps=generation_steps
        )
        
    except Exception as e:
        # Log the error
        error_message = f"Critical error during podcast generation: {str(e)}"
        if "st" in globals():
            st.error(error_message)
        print(error_message)
        
        # Return a fallback response with error info
        return PodcastScriptResponse(
            podcast={"config": {"language": "en-US"}, "script": [
                {"name": voice_1, "message": f"I'm sorry, we encountered an error during podcast generation: {str(e)}"},
                {"name": voice_2, "message": "Please try again with different settings or a different document."}
            ]},
            usage=CompletionUsage(
                prompt_tokens=total_prompt_tokens or 0,
                completion_tokens=total_completion_tokens or 0,
                total_tokens=(total_prompt_tokens or 0) + (total_completion_tokens or 0)
            ),
            generation_steps=generation_steps
        )


@st.cache_resource
def get_encoding() -> tiktoken.Encoding:
    """Get TikToken."""
    encoding = tiktoken.encoding_for_model("gpt-4o")

    return encoding