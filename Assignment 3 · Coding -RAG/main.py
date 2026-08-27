import argparse
from load_doc import load_document
from ask_questions import ask_questions

DEFAULT_DOCX_PATH = "otkjb.docx"
DEFAULT_PERSIST_DIR = "./chroma_docx_db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load a DOCX into Chroma or ask questions against an existing persisted store."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    load_parser = subparsers.add_parser("load", help="Load and embed a DOCX file.")
    load_parser.add_argument("docx_path", nargs="?", default=DEFAULT_DOCX_PATH, help="Path to the DOCX file to load.")
    load_parser.add_argument("--persist-directory", default=DEFAULT_PERSIST_DIR, help="Directory to persist the vector store.")

    ask_parser = subparsers.add_parser("ask", help="Ask questions from an existing persisted store.")
    ask_parser.add_argument("questions", nargs="*", help="Questions to ask the persisted document.")
    ask_parser.add_argument("--persist-directory", default=DEFAULT_PERSIST_DIR, help="Directory where the vector store is persisted.")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.command == "load":
        load_document(args.docx_path, args.persist_directory)
    elif args.command == "ask":
        questions = args.questions or [
            "What is the main topic of this document?",
            "Who are the key people or characters mentioned?",
            "Why was Moses not allowed to enter the Promised Land?",
            "How did David and Saul differ as leaders of Israel?",
            "What examples in the Old Testament show the importance of faith and obedience to God?",
        ]
        ask_questions(questions, args.persist_directory)


if __name__ == "__main__":
    main()
