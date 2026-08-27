"""LangChain chatbot that routes questions to menu/details/other."""

import os
from typing import List
import json, requests

# StrOutputParser converts the LLM's response object into a plain Python string.
from langchain_core.output_parsers import StrOutputParser
# ChatPromptTemplate builds the messages list we send to the LLM.
from langchain_core.prompts import ChatPromptTemplate
# ChatOpenAI is the LangChain wrapper around the OpenAI chat models.
from langchain_openai import ChatOpenAI

from restaurant_db import (
    get_restaurant_details_and_hours,
    search_menu_items,
    book_reservation,
    cancel_reservation,
    get_reservation_email,
)

class RestaurantChatbot:
    """RAG-style restaurant assistant backed by SQLite tables."""

    def __init__(self, db_path: str, model_name: str = "gpt-4o-mini") -> None:
        self.db_path = db_path
        self.llm = None  # start as None — only set if we have an API key

        # os.getenv returns None if the variable is missing — safe to call always.
        if os.getenv("OPENAI_API_KEY"):
            # temperature=0 → deterministic answers (no random creativity).
            # Great for factual tasks like restaurant Q&A.
            self.llm = ChatOpenAI(model=model_name, temperature=0)

        # ── CLASSIFIER PROMPT ────────────────────────────────────────────
        # This prompt instructs the LLM to return exactly one word:
        # "menu", "details", or "other". The | pipe syntax chains the
        # prompt → LLM → parser together into a reusable "chain".
        self.classifier_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a router. Classify each question as exactly one label: "
                    "menu, details, or other. Return only the label.",
                ),
                ("human", "Question: {question}"),
            ]
        )

        # ── ANSWER PROMPT ────────────────────────────────────────────────
        # The {context} placeholder will be filled with the SQLite rows we
        # retrieved. Grounding the LLM in real data prevents hallucination.
        self.answer_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful restaurant assistant. Use only the provided context. "
                    "If context does not contain the answer, say you are not sure and ask a clarifying question. "
                    "Never ask which restaurant the user means.",
                ),
                ("human", "Question: {question}\n\nContext:\n{context}"),
            ]
        )

    def classify_question(self, question: str) -> str:
        """Use the LLM to classify the user's intent."""
        if not self.llm:
            return "general"

        classify_prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are a router for a restaurant chatbot. "
             "Classify the user message into exactly one of these categories:\n"
             "  reservation   — user wants to book a table\n"
             "  cancellation  — user wants to cancel an existing booking\n"
             "  menu          — questions about food, drinks, prices, "
             "  vegetarian options, spicy options, or availability\n"
             "  hours         — questions about opening hours or location\n"
             "  general       — anything else\n"
             "Return ONLY the single category word. No punctuation, no explanation."),
            ("human", "{question}")
        ])

        chain = classify_prompt | self.llm | StrOutputParser()
        result = chain.invoke({"question": question}).strip().lower()
        valid = {"reservation", "cancellation", "menu", "hours", "general"}
        return result if result in valid else "general"

    def _build_menu_context(self, question: str) -> tuple[str, bool]:
        # Search the database for items matching th0e question's keywords.
        rows = search_menu_items(self.db_path, question)
        if not rows:
            return "No menu records matched the question.", False

        lines: List[str] = []
        for row in rows:
            # Convert SQLite integers (0/1) to human-readable labels.
            veg    = "vegetarian"        if row["is_vegetarian"] else "non-vegetarian"
            spicy  = "spicy"              if row["is_spicy"]      else "not spicy"
            status = "available"          if row["is_available"]  else "currently unavailable"
            lines.append(
                f"- {row['item_name']} ({row['category']}): {row['description']} | "
                f"${row['price']:.2f} | {veg}, {spicy}, {status}"
            )
        return "\n".join(lines), True

    def _build_details_context(self) -> str:
        details, hours = get_restaurant_details_and_hours(self.db_path)
        if not details:
            return "No restaurant details found."

        # Format the single restaurant row as readable key-value text.
        details_text = (
            f"Name: {details['name']}\n"
            f"Address: {details['address']}\n"
            f"Phone: {details['phone']}\n"
            f"Email: {details['email']}\n"
            f"Website: {details['website']}"
        )

        # Build one line per weekday, appending any notes in parentheses.
        hours_lines = [
            f"- {h['day_of_week']}: {h['open_time']} to {h['close_time']}"
            + (f" ({h['notes']})" if h.get("notes") else "")
            for h in hours
        ]
        return details_text + "\n\nOpening Hours:\n" + "\n".join(hours_lines)

    def answer(self, question: str) -> str:
        """Route question, retrieve matching SQLite data, and generate an answer."""
        # Step 1: find out which data source we need.
        route = self.classify_question(question)


        # Step 2: fetch the relevant rows from the database.
        if route == "menu":
            context, has_match = self._build_menu_context(question)

            if not has_match:
                return (
                    "I could not find that item in the current menu. "
                    "Ask me to list available mains, starters, desserts, or drinks."
                )
        elif route == "details":
            context = self._build_details_context()
        elif route == "reservation":
            return self._handle_reservation(question)
        elif route == "cancellation":
            return self._handle_cancellation(question)
        else:
            # Off-topic — no database access needed, return a polite refusal.
            return (
                "I can help with booking reservations, menu items, prices, ingredients, and restaurant details "
                "like opening hours, phone, and address."
            )

        # Step 3: if no LLM, return the raw context directly (free fallback mode).
        if not self.llm:
            return f"(Local fallback, no OpenAI key configured)\n{context}"

        # Step 4: hand the context to the LLM and let it write a friendly answer.
        chain = self.answer_prompt | self.llm | StrOutputParser()
        return chain.invoke({"question": question, "context": context})

    def _handle_reservation(self, question: str) -> str:
        # Ask the LLM to extract structured data from the user's message
        extract_prompt = ChatPromptTemplate.from_messages([
            ("system",
             "Extract reservation details from the message. "
             "Return ONLY valid JSON with keys: "
             "customer_name, date, time, party_size, email. "
             "Use null for missing fields. No explanation."),
            ("human", "{question}")
        ])

        if not self.llm:
            return "Please call us directly to make a reservation!"

        chain = extract_prompt | self.llm | StrOutputParser()
        raw = chain.invoke({"question": question})

        try:
            details = json.loads(raw)
            required = ["customer_name", "date", "time", "party_size", "email"]
            if not all(details.get(k) for k in required):
                return ("I need your email,name, date ,time, and party size. "
                        "Example: 'Table for 2 on Friday at 7pm, name is Sara sara_420@gmail.com'")

            res_id = book_reservation(
                self.db_path,
                details["customer_name"], details["date"],
                str(details["time"]), int(details["party_size"]),
                details.get("email")
            )
            self._notify_n8n({**details, "id": res_id}, event="reservation")

            return (f"✅ Reservation confirmed!\n"
                    f"Email: {details['email']}\n"
                    f"Name: {details['customer_name']}\n"
                    f"Date: {details['date']} at {details['time']}\n"
                    f"Party of {details['party_size']} · Booking #{res_id}")
        except (json.JSONDecodeError, ValueError):
            return "Sorry, I couldn't process that. Please try again."


    def _handle_cancellation(self, question: str) -> str:
        # Simple: ask the user for their booking ID
        # (For the bonus: use LLM to extract booking ID from the message)
        import re
        match = re.search(r'\b(\d+)\b', question)
        if match:
            res_id = int(match.group(1))
            email = get_reservation_email(self.db_path, res_id)

            cancel_reservation(self.db_path, res_id)
            self._notify_n8n(
                {
                    "id": res_id,
                    "email": email
                },
                event="cancellation"
            )
            return f"Reservation #{res_id} has been cancelled."
        return "Please provide your booking ID number to cancel."

    def _notify_n8n(self, data: dict, event: str) -> None:
        webhook_url = os.getenv("N8N_WEBHOOK_URL")

        print("N8N_WEBHOOK_URL =", webhook_url)

        if not webhook_url:
            print("ERROR: N8N_WEBHOOK_URL is not set")
            return

        try:
            response = requests.post(
                webhook_url,
                json={**data, "event": event},
                timeout=5
            )

            print("n8n status:", response.status_code)
            print("n8n response:", response.text)

        except Exception as e:
            print("ERROR sending to n8n:", repr(e))