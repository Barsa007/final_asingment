# Semantic Search Analysis Report

## Analysis

The query **"a hero who defeats stronger enemies through intelligence and careful planning"** gave the best results. 
It returned **Iron Man** and **Batman** as the top matches, which makes sense because both characters rely more on strategy, 
intelligence, and technology than on overwhelming superpowers.

One result that impressed me was **Iron Man**. Even though the query did not use the exact same words as the document, 
the embedding model still understood the overall meaning and returned the correct hero. 
This shows why semantic search is much more powerful than a simple keyword search.

One query was less successful. The query about **surviving almost any injury and joking during dangerous situations** 
returned **Batman** and **The Flash** before **Deadpool**. Deadpool is clearly the best match, 
so this suggests that his document could include a stronger description of his healing factor and 
humorous personality to help the embedding model understand the concept better.

ChromaDB uses **L2 distance**, where a lower distance means the document is more semantically similar to the query. 
A distance of **0.0** would be a perfect match. In my results, distances between **0.55 and 0.65** usually returned the most relevant documents. For example, **Iron Man (0.5585)** and **Batman (0.5638)** were excellent matches for the intelligence and planning query. 
However, once the distance became higher than **0.70**, the results became less accurate. A good example is the Deadpool query, 
where **Batman (0.7061)** and **The Flash (0.7123)** ranked higher than **Deadpool (0.7159)** even though Deadpool matched the idea much better.

Based on these results, I would choose a distance threshold of about **0.65**. Most results below that value were relevant, 
while larger distances often returned weaker semantic matches.
