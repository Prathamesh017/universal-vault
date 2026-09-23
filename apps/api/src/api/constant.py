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