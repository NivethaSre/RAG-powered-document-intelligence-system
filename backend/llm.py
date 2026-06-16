import os
from groq import Groq

def generate_answer(question: str, chunks: list, filename: str) -> dict:
    """
    Constructs a retrieval-grounded prompt and requests a response from the Groq API.
    Retries with fallback models if rate limits or other API errors are encountered.
    """
    api_key = os.getenv("GROQ_API_KEY")
    primary_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # Models checklist in order of preference
    models_to_try = [
        primary_model,
        "llama-3.2-11b-text-preview",
        "llama3-8b-8192"
    ]
    # Remove duplicates if primary model is already one of the fallbacks
    models_to_try = list(dict.fromkeys(models_to_try))
    
    if not api_key or api_key == "your_key_here" or api_key.strip() == "":
        return {
            "answer": "Error: GROQ_API_KEY is not configured. Please set a valid API key in your `.env` file.",
            "sources": []
        }
        
    if not chunks:
        return {
            "answer": "No relevant context chunks were found to answer the question. Please verify the document has been fully indexed.",
            "sources": []
        }
        
    # Format context
    context_items = []
    for idx, chunk in enumerate(chunks):
        context_items.append(f"Source [{idx+1}] (Page {chunk['page_number']}):\n{chunk['text']}")
    context = "\n\n".join(context_items)
    
    system_prompt = (
        "You are DocTalk, an advanced document Q&A assistant. Answer the user's question based strictly on the provided context. "
        "For each claim or piece of information you provide, you must cite the source by its index number in square brackets, e.g. [1], [2], etc. "
        "If multiple sources support a point, cite all of them, e.g. [1][3]. "
        "Be concise and factual. If the context does not contain the answer, state that you cannot find the answer in the document. "
        "Do not make up facts."
    )
    
    user_prompt = f"Document: {filename}\n\nContext:\n{context}\n\nQuestion: {question}\n\nAnswer:"
    
    client = Groq(api_key=api_key)
    
    last_error = None
    for model_name in models_to_try:
        try:
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=model_name,
                temperature=0.0,
            )
            answer = response.choices[0].message.content
            
            # Parse citations from answer
            cited_sources = []
            for idx, chunk in enumerate(chunks):
                citation = f"[{idx+1}]"
                if citation in answer:
                    source_item = {
                        "text": chunk["text"],
                        "page": chunk["page_number"],
                        "filename": chunk["filename"]
                    }
                    if source_item not in cited_sources:
                        cited_sources.append(source_item)
                        
            # Fallback to returning top chunks if no citations parsed but chunks exist
            if not cited_sources and chunks:
                cited_sources = [{
                    "text": chunk["text"],
                    "page": chunk["page_number"],
                    "filename": chunk["filename"]
                } for chunk in chunks[:2]]
                
            return {
                "answer": answer,
                "sources": cited_sources
            }
            
        except Exception as e:
            last_error = str(e)
            print(f"Error calling Groq model {model_name}: {last_error}. Retrying with fallback...")
            continue
            
    # If all models fail
    return {
        "answer": f"Error calling Groq API: All models failed. Last error: {last_error}",
        "sources": []
    }
