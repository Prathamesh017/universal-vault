parser_prompt = """You are a markdown structure parser. Extract hierarchical structure from markdown.

EXAMPLE INPUT:
# Getting Started
## What is CloudSync?
This is a file sync tool.
## System Requirements
Windows 10+, 2GB RAM

EXAMPLE OUTPUT:
{
  "title": "Getting Started",
  "sections": [
    {
      "level": 1,
      "title": "Getting Started",
      "heading": "# Getting Started",
      "content": "",
      "children": [
        {
          "level": 2,
          "title": "What is CloudSync?",
          "heading": "## What is CloudSync?",
          "content": "This is a file sync tool.",
          "children": []
        },
        {
          "level": 2,
          "title": "System Requirements",
          "heading": "## System Requirements",
          "content": "Windows 10+, 2GB RAM",
          "children": []
        }
      ]
    }
  ]
}

NOW PARSE THIS DOCUMENT:
"""

question_check_prompt = """You check if a user question should be answered using this document.

Document description:
{description}

User question:
{question}

Rules:
- isValid must be true only if BOTH are true:
  1) The question is about this document's topic
  2) The question is a clear, normal sentence/question (not just keywords like "install sync cloud")
- reason must be a short message written for the end user, explaining why the question is accepted or rejected.
  Examples:
  - "Your question looks unrelated to this document, which is about CloudSync installation."
  - "Please ask a full question instead of just keywords."
  - "Your question looks valid for this document."

Return ONLY JSON:
{{
  "isValid": true,
  "reason": "message for the user"
}}
"""

query_rewrite_prompt = """Rewrite the user question into a better search query for retrieving document chunks.

Original question:
{question}

Nearest document chunks (may be weakly related):
{chunks}

Rules:
- Use vocabulary and topics from the chunks when helpful
- Keep it as one clear search question
- Do not answer the question
- Return ONLY the rewritten question text, nothing else
"""
