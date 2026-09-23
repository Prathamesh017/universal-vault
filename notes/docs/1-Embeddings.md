#### Problems with traditional search and need for embeddings

Example : Imagine you're building a customer support chatbot. You have a knowledge base of 1000 support articles.

A customer asks: "How do I get my money back?"

Traditional search (keyword matching) would look for documents containing "money" or "back" or "refund". It finds articles that have those exact words.

The keyword search might miss it because the article doesn't use the word "money" or "back". It uses "refunds" and "cancelled". Same meaning, different words.


This is the core problem embeddings solve: matching by meaning, not by exact word matches.


#### Embeddings
With Embedding , we can convert words,sentences,paragraphs,etc into vectors of numbers.

Texts with similar meaning end up close together in this space, regardless of exact wording.

These embeddings are then used to find the most similar documents to the query.

This is how embeddings work:

1. Convert the query and documents into vectors
2. Find the most similar documents to the query
3. Return the most similar documents

Text: "How do I get my money back?"
Embedding: [0.12, -0.44, 0.87, 0.21, 0.56, ...]

Text: "Refunds are processed within 5 business days"
Embedding: [0.15, -0.42, 0.85, 0.23, 0.54, ...]

Text: "Money is important to us"
Embedding: [0.91, 0.22, 0.11, 0.05, 0.03, ...]

###### Why Does This Work?

The model that generates embeddings was trained on billions of text examples. During training, it learned patterns like:

Words that appear in similar contexts tend to mean similar things
Sentences that express similar ideas should have similar embeddings
The distance between embeddings should reflect meaning distance

So when the model sees your text, it maps it to a position in semantic space based on everything it learned.


###### Key Properties of Embeddings

Fixed size — An embedding is always the same length. OpenAI's embeddings are 1536 numbers. Google's are 3072. This consistency is important.
Continuous space — The numbers can be any decimal value. This lets us measure distance precisely.
Meaningful distance — The further apart two embeddings are, the more different their meanings. The closer, the more similar.
Context-aware — The same word in different sentences gets different embeddings, because context changes meaning. "Bank" (financial) vs "bank" (river) would have different embeddings.

#### Some Observations

1) A Embedding model always generate vectors of a fixed size although we might need few or more vectors according to  our use case.

Reason for this is
Embedding models are neural networks. Neural networks have a fixed architecture:

It was built this way to make it easier to train and use.

ould we have variable-size embeddings?

Theoretically, yes. A model could output anywhere from 10 to 3072 numbers depending on input complexity.

But in practice:

Harder to train — Variable-size outputs are complex for neural networks
Harder to search — Vector databases are optimized for fixed dimensions. Searching variable-size vectors is slower
Standardization — Fixed-size embeddings are a standard. Comparing embeddings from different sources requires same dimensions

Example of the problem:

If you have a 1536-dim embedding and a 512-dim embedding, how do you compare them? You can't directly calculate distance. You'd need to convert one to match the other, which loses information.




2) What to embedd depends on us 
for example - we might want to embedd a single word, a sentence, a paragraph, a document, a collection of documents, etc.

The embedding model works on all of these. It's designed to take text of any length.

But there's a practical constraint:

Most embedding models have a token limit. OpenAI's text-embedding-3-large can handle up to ~8000 tokens. Google's gemini-embedding-001 can handle ~2000 tokens.

One token ≈ 4 characters. So:

2000 tokens ≈ 8000 characters ≈ 1-2 pages of text

If you try to embed 10 pages at once, the model truncates (cuts off) everything beyond its limit.

So the practical answer:

You need to decide:

Embedding a single sentence? Good, go ahead
Embedding a paragraph? Good
Embedding an entire 20-page document? Bad, truncates

This is why chunking exists. You break documents into smaller pieces (paragraphs, 2000-char chunks, etc.), embed each chunk, then retrieve them later.


3) Vector DBs

we store the embeddings in a vector database. example - FAISS, Chroma, Pinecone, etc.
Vector databases are optimized for storing and searching vectors.

They store the embeddings and the text that was used to generate themThey also provide a way to search the embeddings.They are optimized for storing and searching vectors.



---
Dimensions in Embeddings

Imagine describing movies on different dimensions:
Movie: "John Wick"
- Action level: 9/10
- Humor level: 2/10
- Romance level: 1/10
- Drama level: 7/10
- Emotional impact: 8/10

Movie: "Deadpool"
- Action level: 8/10
- Humor level: 9/10
- Romance level: 3/10
- Drama level: 4/10
- Emotional impact: 5/10

Movie: "The Notebook"
- Action level: 1/10
- Humor level: 3/10
- Romance level: 9/10
- Drama level: 8/10
- Emotional impact: 9/10


Now if someone asks "Find me a movie like John Wick", you look for movies with:

High action (9)
Low humor (2)
Low romance (1)
Medium-high drama (7)

And Deadpool is closer than The Notebook because they share the "high action, low romance" dimensions.

Embeddings Work Exactly Like This . Text embedding has multiple dimensions, each capturing different aspects:


#### How do we find the most similar documents to the query?

We use something called cosine similarity to find the most similar documents to the query.

But the important thing is what should be similarity metric , for example 2 things might be related to each other but the distance between them might be high or low.

But so we need to have a similarity threshold to decide if 2 things are similar or not.

Cosine distance scale: 0 to 2

Threshold = 0.3 (STRICT):
- Only get very similar chunks
- Precision: HIGH (what you get is definitely relevant)
- Recall: LOW (you miss some relevant chunks)
- Risk: Say "I don't know" too often

Threshold = 0.6 (BALANCED):
- Get somewhat similar chunks
- Precision: MEDIUM
- Recall: MEDIUM
- Risk: Balanced between being helpful and accurate

Threshold = 0.8 (LENIENT):
- Get anything somewhat related
- Precision: LOW (get irrelevant stuff)
- Recall: HIGH (find everything possibly relevant)
- Risk: Hallucinate using wrong context

like if it is medical chatbot we have to more strict  , compared to a general chatbot we can be more lenient.

I think in our case we can ask user to the threshold as ours is general rag system.