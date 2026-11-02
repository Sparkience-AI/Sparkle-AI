"""Source-checkout compatibility launcher for Sparkle AI."""

from sparkle_ai.desktop import AIAssistant, TextProcessor, main

__all__ = ["AIAssistant", "TextProcessor", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
