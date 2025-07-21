"""Simple smoke test that pings the configured LLM gateway and prints a short
confirmation message.

This module is primarily intended to be invoked from the Makefile::

    $ make smoke

It can also be executed directly::

    $ python -m edgar_ai.smoke
"""

from __future__ import annotations

import sys

from edgar_ai.config import settings
from edgar_ai.llm import chat_completions


def main() -> None:  # noqa: D401 (simple script)
    """Run the smoke test and exit with an appropriate status code."""

    print("Gateway URL:", settings.llm_gateway_url or "(not set)")

    try:
        rsp = chat_completions(
            model="o4-mini",
            messages=[
                {"role": "system", "content": "You are a ping bot."},
                {"role": "user", "content": "ping"},
            ],
            temperature=0.0,
        )
    except Exception as exc:  # noqa: BLE001 (broad exception is fine for CLI)
        print("Smoke-test FAILED:", exc)
        sys.exit(1)

    print("Gateway responded:", rsp["choices"][0]["message"]["content"][:80])


if __name__ == "__main__":
    main()

