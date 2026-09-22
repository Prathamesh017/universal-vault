#### Chunking

Chunking is the process of splitting a document into smaller chunks.
This is important because it allows us to store the embeddings in a vector database.

Also each model has  a token limit ,that decides how many chars/tokens it can handle at once.
4 chars = 1 token roughly


Why Chunking Helps
Scenario 1: Embed entire document
Document: "How to Use Our Product" (20 pages)
- Covers: Installation, Setup, Features, Troubleshooting, FAQs

User asks: "How do I install this?"

Embedding is broad (covers everything)
Result: When searching for installation help, it matches but isn't specific
"This document mentions installation, but also 19 other topics"

Problem: Low precision. Document is relevant but not focused.

---

Scenario 2: Split into chunks
Chunks:
1. "Installation instructions..." (1 page)
2. "Setup configuration..." (1 page)
3. "Features overview..." (1 page)
4. "Troubleshooting guide..." (1 page)
5. "FAQs..." (1 page)

User asks: "How do I install this?"

Chunk 1's embedding is specific (only about installation)
Result: Perfect match. Highly relevant and focused.

Benefit: High precision. Get exactly what user needs.

---
Types of Chunking Strategies

Strategy 1: Fixed-Size Chunking
```
Document text: "Lorem ipsum dolor sit amet... consectetur adipiscing elit..."
             (10,000 characters total)

Chunk size: 2000 characters
Overlap: 200 characters

Result:

Chunk 1: [0-2000 chars]       "Lorem ipsum dolor sit amet... adipiscing"
Chunk 2: [1800-3800 chars]    "sit amet... adipiscing elit... incididunt"
Chunk 3: [3600-5600 chars]    "adipiscing elit... incididunt ut labore"
Chunk 4: [5400-7400 chars]    "ut labore et dolore... tempor incididunt"
Chunk 5: [7200-9200 chars]    "tempor incididunt... elit sed do eiusmod"
Chunk 6: [9000-10000 chars]   "eiusmod tempor... final text"

```

Notice:

Stride (step): 1800 characters (2000 - 200 overlap)
Overlap: 200 chars (20 char sentence might span boundary)
Simple, deterministic, predictable

Pros:
✓ Simple to implement
✓ Predictable output
✓ No external dependencies

Cons:
✗ Might split sentences mid-way (bad for clarity)
✗ 2000 chars might be too large or too small for your use case



Strategy 2: Semantic Chunking (Smart Split Points)

```
Document: "Installation is easy. Just follow these steps. Step 1: Download the file."

Don't split by character count. Split at natural boundaries (sentence/paragraph).

Result:

Chunk 1: "Installation is easy. Just follow these steps."
Chunk 2: "Step 1: Download the file."
Chunk 3: "Step 2: Run the installer."
...
```

How it happens
1. Split by paragraphs (look for \n\n)
2. If paragraph too large, split by sentences (look for . ! ?)
3. If sentence too large, split by phrases (look for , or ;)
4. Combine until reaching target size

Result: Chunks at natural boundaries, no mid-sentence splits

Pros:
✓ Preserves meaning (no broken sentences)
✓ More coherent chunks

Cons:
✗ Slightly more complex to implement
✗ Size varies (some chunks 500 chars, some 2000)



Strategy 3: Hierarchical Chunking (Multi-Level)

```
Document structure:

Section 1: "Getting Started"
  Subsection 1.1: "Installation"
    Paragraph: "To install..."
    Paragraph: "First download..."
  Subsection 1.2: "Configuration"
    Paragraph: "Configure settings..."

Hierarchical chunks:

Level 1 (full section): "Getting Started\nInstallation\nConfiguration..." 
  → Embedding: broad understanding

Level 2 (subsection): "Installation\nTo install... First download..."
  → Embedding: medium specificity

Level 3 (paragraph): "To install the software..."
  → Embedding: specific detail

```
Pros:
✓ Multi-level retrieval (find broad topics AND specific details)
✓ Can traverse from general to specific

Cons:
✗ More complex to implement
✗ Store more embeddings (space/cost)


Tradeoffs
Small chunks (500 chars, 50 overlap):
✓ Very specific ("How to troubleshoot login")
✓ High precision in search
✗ Many embeddings to store/search
✗ Lose surrounding context
✗ Higher cost (more API calls to embed)

Medium chunks (2000 chars, 200 overlap) - Gaspy:
✓ Balanced specificity
✓ Natural information units
✓ Reasonable number of embeddings
✓ Good context preservation

Large chunks (5000 chars, 500 overlap):
✓ Broad context , returns lot of information which might be irrelevant
✓ Few embeddings (cheaper)
✗ Less precise (mix many topics)
✗ User gets "you're in the right document but wrong section"



We can implement this in 2 ways
a) ask user input in particular format (Structured Input) so we can do Semantic or Hierarchical Chunking
b) Use LLM to Extract Structure (No Format Required)



#### Actual Storage

Each chunk we create is stored as a row in vector db. Therefor Different Chunk Sizes = Different Number of Rows


Same document, different chunking:

Chunking 1: Fixed-size (2000 chars per chunk)
Document size: 20,000 chars
Result: 20,000 ÷ 2000 = 10 chunks = 10 rows

Chunking 2: Sentence-based
Document has 100 sentences
Result: 100 chunks = 100 rows

Chunking 3: Hierarchical
- 5 sections (Level 1)
- 30 subsections (Level 2)
- 100 paragraphs (Level 3)
Result: 5 + 30 + 100 = 135 chunks = 135 rows

The key insight: Chunking strategy determines rows, not columns.

Smaller chunks → more rows
Larger chunks → fewer rows
Each row = always 1 vector



---
Retrieval using TopK and Threshold

The question: When a user asks a question, how do we find the relevant chunks?

```
Step 1: User asks a question
"How do I get a refund?"

Step 2: Embed the question
Question embedding: [0.85, 0.3, 0.9, 0.8, ...]

Step 3: Search vector DB
"Find chunks most similar to this embedding"

Vector DB compares question to ALL chunk embeddings
Calculates cosine distance to each

Results (before filtering):
Chunk 1: distance 0.05 ✓ Very close
Chunk 2: distance 0.12 ✓ Close
Chunk 5: distance 0.3  ? Moderate
Chunk 7: distance 0.45 ? Loose
Chunk 12: distance 0.7 ✗ Far
Chunk 19: distance 0.9 ✗ Very far

Step 4: Apply Top-K filter
"Return the top 5 closest"

Results after top-k:
[Chunk 1, Chunk 2, Chunk 5, Chunk 7, Chunk 12]

Step 5: Apply Threshold filter
"Only keep chunks with distance < 0.6"

Results after threshold:
[Chunk 1, Chunk 2, Chunk 5]

Step 6: Pass to Claude
"Here's what I found. Answer based on this context."

Claude reads the 3 chunks and generates answer.

```
Combining TopK and Threshold gives us the final chunks that we will use to answer the user's question.





