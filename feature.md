2. Rate Limiting (by IP)
   - 60 req/min
   - 1000 req/day

3. Streaming Responses
   - Stream answer chunks as generated

4. Conversation History
   - Store previous Q&A in memory
   - Pass context to follow-ups

5. Multi-Document Support
   - Query across multiple docs
   - Track which doc answer came from

6. Query Classification (rule-based)
   - Classify: definition/how-to/comparison/troubleshooting/factual
   - Adjust retrieval strategy per type

7. Context Compression
   - Remove redundancy from chunks
   - Keep essential info only

8. Cost Analysis
   - Track embedding cost
   - Track LLM cost
   - Show per-query breakdown


12. Answer Confidence Score
    - LLM scores answer 0-100
    - Show in response