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

answer_from_chunks_prompt = """You answer the user question using ONLY the provided document chunks.

User question:
{question}

Document chunks:
{chunks}

Rules:
- If the chunks contain enough information to answer, set satisfied=true and write a clear answer for the user in "message".
- If the chunks are not enough or not relevant enough, set satisfied=false and put a short user-facing explanation in "message".
- Do not invent facts that are not in the chunks.
- message should be ready to show directly to the user.

Return ONLY JSON:
{{
  "satisfied": true,
  "message": "exact message for the user"
}}
"""

resolve_followup_prompt = """You handle a follow-up user message using recent conversation turns.

Recent conversation (oldest first):
{history}

Current user message:
{question}

Choose ONE action:
- "answer": prior turns already contain enough to reply. Put the user-facing reply in "message". Prefer this for "tell me more" / "elaborate" when prior answers already cover the topic.
- "search": need NEW document details not in history. Put one clear standalone search question in "question".
- "clarify": topic is unclear. Put a short clarification question in "message".

Rules for "search":
- "question" must be a full standalone question a stranger could search with.
- Good: "What else should I know about CloudSync?" or "Explain CloudSync installation in more detail"
- Bad: "tell me more" or "tell me more (about: ...)" or any vague follow-up phrasing
- Never copy the follow-up wording into "question".

Rules:
- Prefer "answer" when history is enough (including expanding/rephrasing prior answers).
- Use "search" only when the user clearly needs new facts beyond history.
- Use "clarify" only when you cannot tell what they mean.
- Do not invent document facts that are not in history when action is "answer".

Return ONLY JSON:
{{
  "action": "answer",
  "message": "reply for the user",
  "question": ""
}}
"""
