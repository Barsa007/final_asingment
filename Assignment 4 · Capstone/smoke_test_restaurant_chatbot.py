"""Smoke test for the SQLite-backed restaurant chatbot."""

import os
import tempfile
import uuid

from dotenv import load_dotenv

from restaurant_chatbot import RestaurantChatbot
from restaurant_db import (
    get_menu_items,
    get_restaurant_details_and_hours,
    initialize_database,
)


# Load variables from .env
load_dotenv()


def run_smoke_test() -> None:
    # ================================================================
    # CREATE TEMPORARY DATABASE
    # ================================================================

    db_path = os.path.join(
        tempfile.gettempdir(),
        f"test_restaurant_{uuid.uuid4().hex}.sqlite",
    )

    try:
        initialize_database(db_path)
        print("Database initialized successfully.")

        # ============================================================
        # VERIFY DATABASE CONTENTS
        # ============================================================

        menu = get_menu_items(db_path)
        details, hours = get_restaurant_details_and_hours(db_path)

        assert len(menu) >= 3, (
            "Menu should have seeded items"
        )

        assert details.get("name"), (
            "Restaurant details should be seeded"
        )

        assert len(hours) == 7, (
            "Opening hours should include all days"
        )

        # ============================================================
        # VERIFY OPENAI API KEY
        # ============================================================

        api_key = os.getenv("OPENAI_API_KEY")

        assert api_key, (
            "OPENAI_API_KEY was not found. "
            "Make sure it is defined in your .env file."
        )

        print("OpenAI API key loaded successfully.")

        # ============================================================
        # CREATE CHATBOT
        # ============================================================

        bot = RestaurantChatbot(db_path=db_path)

        print("Restaurant chatbot created successfully.")

        # ============================================================
        # MENU TEST
        # ============================================================

        menu_reply = bot.answer(
            "What vegetarian dishes are on the menu?"
        )

        print("\nMENU TEST:")
        print(menu_reply)

        assert (
            "Margherita Pizza" in menu_reply
            or "Mushroom Risotto" in menu_reply
            or "Lemon Tart" in menu_reply
            or "Iced Latte" in menu_reply
        ), (
            "Menu question should return a vegetarian menu item"
        )

        print("MENU TEST: PASS")

        # ============================================================
        # MISSING MENU ITEM TEST
        # ============================================================

        missing_item_reply = bot.answer(
            "Do you have fish in the menu?"
        )

        print("\nMISSING ITEM TEST:")
        print(missing_item_reply)

        assert (
            "could not find that item"
            in missing_item_reply.lower()
        ), (
            "Missing menu item should return the expected message"
        )

        print("MISSING ITEM TEST: PASS")

        # ============================================================
        # HOURS / DETAILS TEST
        # ============================================================

        details_reply = bot.answer(
            "What are your opening hours and address?"
        )

        print("\nHOURS / DETAILS TEST:")
        print(details_reply)

        details_lower = details_reply.lower()

        assert (
            "opening hours" in details_lower
            or "monday" in details_lower
        ), (
            "Hours question should return opening hours"
        )

        assert (
            "address" in details_lower
            or "market street" in details_lower
        ), (
            "Hours/location question should return address"
        )

        print("HOURS / DETAILS TEST: PASS")

        # ============================================================
        # HOURS ROUTE TEST
        # ============================================================

        hours_route = bot.classify_question(
            "What are your opening hours?"
        )

        print("\nHOURS ROUTE TEST:")
        print(hours_route)

        assert hours_route == "hours", (
            f"Expected hours route, got: {hours_route}"
        )

        print("HOURS ROUTE TEST: PASS")

        # ============================================================
        # HOURS ANSWER TEST
        # ============================================================

        hours_reply = bot.answer(
            "What are your opening hours?"
        )

        print("\nHOURS ANSWER TEST:")
        print(hours_reply)

        assert (
            "opening hours" in hours_reply.lower()
            or "monday" in hours_reply.lower()
        ), (
            "Hours answer should contain opening-hours information"
        )

        print("HOURS ANSWER TEST: PASS")

        # ============================================================
        # GENERAL QUESTION TEST
        # ============================================================

        other_reply = bot.answer(
            "Can you tell me a joke?"
        )

        print("\nGENERAL TEST:")
        print(other_reply)

        # The exact wording may change, so don't require
        # one specific sentence.
        assert "I can help" in other_reply, (
            "General question should return the restaurant "
            "assistant message"
        )

        print("GENERAL TEST: PASS")

        # ============================================================
        # RESERVATION ROUTE TEST
        # ============================================================

        reservation_route = bot.classify_question(
            "I want to make a reservation"
        )

        print("\nRESERVATION ROUTE TEST:")
        print(reservation_route)

        assert reservation_route == "reservation", (
            f"Expected reservation route, "
            f"got: {reservation_route}"
        )

        print("RESERVATION ROUTE TEST: PASS")

        # ============================================================
        # CANCELLATION ROUTE TEST
        # ============================================================

        cancellation_route = bot.classify_question(
            "I want to cancel my reservation"
        )

        print("\nCANCELLATION ROUTE TEST:")
        print(cancellation_route)

        assert cancellation_route == "cancellation", (
            f"Expected cancellation route, "
            f"got: {cancellation_route}"
        )

        print("CANCELLATION ROUTE TEST: PASS")

        # ============================================================
        # FINAL RESULT
        # ============================================================

        print("\n" + "=" * 60)
        print("ALL SMOKE TESTS PASSED")
        print("=" * 60)

    finally:
        # ============================================================
        # CLEANUP
        # ============================================================

        try:
            os.remove(db_path)
        except OSError:
            pass


if __name__ == "__main__":
    run_smoke_test()
    print("\nsmoke_test_restaurant_chatbot.py: PASS")