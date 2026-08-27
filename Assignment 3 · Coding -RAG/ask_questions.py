import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_classic.chains import RetrievalQA
from langchain_community.vectorstores import Chroma


def get_vectorstore(persist_directory: str = "./chroma_docx_db") -> Chroma:
    if not os.path.isdir(persist_directory):
        raise FileNotFoundError(
            f"Persist directory {persist_directory!r} does not exist. "
            "Run `python main.py load <docx_path>` first to build the vector store."
        )

    embeddings = OpenAIEmbeddings()
    return Chroma(persist_directory=persist_directory, embedding_function=embeddings)


def ask_questions(questions: list[str], persist_directory: str = "./chroma_docx_db") -> None:
    vectorstore = get_vectorstore(persist_directory)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True,
    )

    for question in questions:
        result = qa_chain.invoke({"query": question})
        print(f"\n❓ {question}")
        print(f"🤖 {result['result']}")
        print("\n📚 Retrieved context:")
        for i, src in enumerate(result["source_documents"], 1):
            print(f"  [{i}] ...{src.page_content[:200]}...")


if __name__ == "__main__":
    sample_questions = [
        "What is the main topic of this document?",
        "Who are the key people or characters mentioned?",
    ]
    ask_questions(sample_questions)
