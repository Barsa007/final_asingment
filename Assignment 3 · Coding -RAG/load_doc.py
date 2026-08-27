import argparse
import os
import re
from langchain_community.document_loaders import Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

DEFAULT_PERSIST_DIR = "./chroma_docx_db"


def split_document_into_books(document: Document) -> list[Document]:
    bible_books = [
        "Genesis",
        "Exodus",
        "Leviticus",
        "Numbers",
        "Deuteronomy",
        "Joshua",
        "Judges",
        "Ruth",
        "1 Samuel",
        "2 Samuel",
        "1 Kings",
        "2 Kings",
        "1 Chronicles",
        "2 Chronicles",
        "Ezra",
        "Nehemiah",
        "Esther",
        "Job",
        "Psalms",
        "Proverbs",
        "Ecclesiastes",
        "Song of Solomon",
        "Isaiah",
        "Jeremiah",
        "Lamentations",
        "Ezekiel",
        "Daniel",
        "Hosea",
        "Joel",
        "Amos",
        "Obadiah",
        "Jonah",
        "Micah",
        "Nahum",
        "Habakkuk",
        "Zephaniah",
        "Haggai",
        "Zechariah",
        "Malachi",
        "Matthew",
        "Mark",
        "Luke",
        "John",
        "Acts",
        "Romans",
        "1 Corinthians",
        "2 Corinthians",
        "Galatians",
        "Ephesians",
        "Philippians",
        "Colossians",
        "1 Thessalonians",
        "2 Thessalonians",
        "1 Timothy",
        "2 Timothy",
        "Titus",
        "Philemon",
        "Hebrews",
        "James",
        "1 Peter",
        "2 Peter",
        "1 John",
        "2 John",
        "3 John",
        "Jude",
        "Revelation",
    ]

    pattern = re.compile(
        r"^(?P<book>" + "|".join(re.escape(name) for name in bible_books) + r")\s+\d+:\d+",
        re.MULTILINE,
    )

    text = document.page_content
    matches = list(pattern.finditer(text))
    if not matches:
        return [document]

    book_offsets = []
    previous_book = None
    for match in matches:
        book = match.group("book").strip()
        if book != previous_book:
            book_offsets.append((book, match.start()))
            previous_book = book

    book_documents: list[Document] = []
    if book_offsets[0][1] > 0:
        preface = text[: book_offsets[0][1]].strip()
        if preface:
            book_documents.append(
                Document(
                    page_content=preface,
                    metadata={**document.metadata, "book": "Preamble"},
                )
            )

    for index, (book, start_index) in enumerate(book_offsets):
        end_index = book_offsets[index + 1][1] if index + 1 < len(book_offsets) else len(text)
        book_text = text[start_index:end_index].strip()
        if book_text:
            book_documents.append(
                Document(
                    page_content=book_text,
                    metadata={**document.metadata, "book": book},
                )
            )

    return book_documents


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load a .docx file, split it into chunks, embed it, and persist the data to Chroma."
    )
    parser.add_argument(
        "docx_path",
        nargs="?",
        default="otkjb.docx",
        help="Path to the .docx file to process.",
    )
    parser.add_argument(
        "--persist-directory",
        default=DEFAULT_PERSIST_DIR,
        help="Directory where Chroma will persist the embedded vector store.",
    )
    return parser.parse_args()


def load_document(docx_path: str, persist_directory: str = DEFAULT_PERSIST_DIR) -> Chroma:
    if not os.path.isfile(docx_path):
        raise FileNotFoundError(
            f"File path {docx_path!r} is not a valid file. Provide an existing .docx path."
        )

    loader = Docx2txtLoader(docx_path)
    docs = loader.load()
    print(f"Loaded {len(docs)} document(s) from {docx_path}")

    book_documents: list[Document] = []
    for doc in docs:
        split_books = split_document_into_books(doc)
        book_documents.extend(split_books)

    print(f"Split into {len(book_documents)} book-level document(s)")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=60,
    )
    chunks = splitter.split_documents(book_documents)
    print(f"Split into {len(chunks)} chunks")

    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory,
    )
    print(f"Vector store created and persisted to {persist_directory}")
    return vectorstore


if __name__ == "__main__":
    args = parse_args()
    load_document(args.docx_path, args.persist_directory)
