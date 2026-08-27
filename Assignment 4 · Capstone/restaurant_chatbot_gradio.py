"""Gradio web UI for the SQLite + LangChain restaurant chatbot."""

from dotenv import load_dotenv
import gradio as gr

from restaurant_chatbot import RestaurantChatbot
from restaurant_db      import initialize_database


def create_bot(db_path: str = "restaurant.sqlite") -> RestaurantChatbot:
    """Load environment variables, ensure DB exists, then build chatbot."""
    # Reads OPENAI_API_KEY from .env if the file exists.
    load_dotenv()

    # Creates tables and seed rows before the very first user question.
    initialize_database(db_path)
    return RestaurantChatbot(db_path=db_path)


def build_demo(bot: RestaurantChatbot) -> gr.Blocks:
    """Construct the Gradio chat interface around the chatbot backend."""

    # chat_handler is an inner function — it captures `bot` from the outer scope.
    def chat_handler(message: str, history: list[dict]) -> tuple[list[dict], str]:
        """Append the user question and bot answer in Gradio messages format."""
        history = history or []
        user_text = (message or "").strip()
        if not user_text:
            return history, ""  # nothing typed — return unchanged history

        answer = bot.answer(user_text)

        # Gradio's chat format is a list of dicts with "role" and "content" keys.
        # We append both the user message and the bot reply, then return the new list.
        updated_history = history + [
            {"role": "user",      "content": user_text},
            {"role": "assistant", "content": answer},
        ]
        return updated_history, ""  # second value clears the text box

    # gr.Blocks lets us arrange components freely (unlike gr.Interface).
    with gr.Blocks(title="Restaurant Chatbot") as demo:
        gr.Markdown("## Restaurant Chatbot\nAsk about menu items, prices, or opening hours.")

        # gr.Chatbot renders the conversation with user/assistant bubbles.
        chatbot = gr.Chatbot(label="Conversation", height=450)

        message_box = gr.Textbox(
            label="Your question",
            placeholder="e.g., What vegetarian dishes do you have?"
        )

        # Place Send and Clear side by side with gr.Row().
        with gr.Row():
            send_btn  = gr.Button("Send", variant="primary")
            clear_btn = gr.Button("Clear")

        # Wire up: clicking Send or pressing Enter both call chat_handler.
        send_btn.click(chat_handler,
                       inputs=[message_box, chatbot],
                       outputs=[chatbot, message_box])

        message_box.submit(chat_handler,
                            inputs=[message_box, chatbot],
                            outputs=[chatbot, message_box])

        # Clear resets the chatbot to an empty list, no loading state needed.
        clear_btn.click(lambda: [], outputs=chatbot, queue=False)

        # Example questions the user can click to auto-fill the text box.
        gr.Examples(
            examples=[
                "What are your opening hours?",
                "What spicy dishes are available?",
                "What is your phone number and address?",
            ],
            inputs=message_box,
        )

    return demo


def main() -> None:
    """Run the web app."""
    bot  = create_bot()
    demo = build_demo(bot)
    # Port 7861 avoids conflict with rag_pdf.py which defaults to 7860.
    demo.launch(server_port=7861)


if __name__ == "__main__":
    main()