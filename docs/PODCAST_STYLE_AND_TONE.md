# Podcast Style and Tone Parameters

This document explains the available **podcast style** and **tone** parameters in the Azure Podcast Generator, and how they influence the generated podcast script.

---

## Podcast Style

The `podcast_style` parameter determines the overall structure, format, and storytelling approach of the podcast. Each style is inspired by a well-known podcast or format:

| Style Name      | Description |
|-----------------|-------------|
| **Huberman Lab** | Scientific, educational focus. Begins with a scientific question, explains research in accessible language, and concludes with actionable insights. |
| **Joe Rogan Experience** | Conversational, long-form. Free-flowing dialogue, personal anecdotes, and deep dives into topics. |
| **Radiolab** | Narrative-driven with storytelling. Uses creative storytelling, character development, and sound design elements. |
| **Planet Money** | Explains complex topics through real-world examples and analogies. Breaks down concepts step by step. |
| **TED Talks Daily** | Concise, idea-focused. Clear thesis, structured points, and inspiring conclusions. |
| **News Briefing** | Brief updates with minimal elaboration. Factual, headline-style summaries. |

**Tip:**

- For more analogies and real-world examples, choose **Planet Money** style.
- For story-driven explanations, choose **Radiolab**.

---

## Podcast Tone

The `podcast_tone` parameter controls the language, mood, and delivery style of the podcast. It affects how the hosts speak and how information is presented:

| Tone Name         | Description |
|-------------------|-------------|
| **Conversational** | Friendly, casual dialogue. Feels like a chat between friends, with humor and anecdotes. |
| **Educational**    | Clear, structured explanations. Like a lesson with intro, explanation, and summary. |
| **Analytical**     | Logical, evidence-based. Examines multiple perspectives and cites research. |
| **Narrative**      | Story-driven, with characters and emotional arcs. Immersive storytelling. |
| **Inspirational**  | Uplifting, motivational, and empowering language. |
| **Technical**      | Detailed, precise, and uses domain-specific terminology. For knowledgeable audiences. |

**Tip:**

- For more analogies, use **Conversational** or **Educational** tone with the **Planet Money** style.

---

## How to Use

You can set the podcast style and tone in the app's UI under "Podcast Settings". These parameters help tailor the generated script to your preferred format and audience.

---

For more details, see the code in `app/utils/llm.py`.
