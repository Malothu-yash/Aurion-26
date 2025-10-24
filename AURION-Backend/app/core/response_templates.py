"""
Response Templates and System Prompt for AURION
"""

SYSTEM_PROMPT = (
    "You are Aurion, a helpful assistant. Always respond in 2–3 friendly sentences. "
    "Use clear structure and bullet points if needed. If you don’t know, say so politely."
)

def format_definition(term: str, definition: str) -> str:
    return f"**{term}**: {definition}\n\n- {definition[:80]}..."

def format_list(title: str, items: list) -> str:
    bullet_points = '\n'.join([f"- {item}" for item in items])
    return f"**{title}**\n{bullet_points}"

def format_summary(text: str) -> str:
    return f"**Summary:** {text[:120]}..."

def format_fallback() -> str:
    return "I'm not sure about that, but I can help you find more information or clarify your question!"

def format_response(intent: str, content: str, extra=None) -> str:
    """Main response formatter based on intent."""
    if intent == "define" and extra:
        return format_definition(extra.get("term", ""), content)
    elif intent == "list" and extra:
        return format_list(extra.get("title", "List"), extra.get("items", []))
    elif intent == "summarize":
        return format_summary(content)
    elif intent == "fallback":
        return format_fallback()
    else:
        return content
