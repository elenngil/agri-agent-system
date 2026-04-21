from rag.graph import get_retriever

retriever = get_retriever()

context = retriever.get_context_for_risk("frost_risk")

if context:
    print("FUNCIONA\n")
    print(context.to_prompt_context())
else:
    print("No encontró contexto")