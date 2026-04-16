from core import model_api, cache
from utils.helpers import estimate_tokens, count_words
from config import settings
import logging

logger = logging.getLogger(__name__)


def expand_prompt(user_text: str, model_id: str) -> str:
    """
    Expands a simple user input into a detailed, structured prompt.
    
    Args:
        user_text: The user's simple idea
        model_id: The model identifier (can be a key from models.yaml or a full model ID)
    """
    logger.info(f"Generating prompt for '{user_text[:50]}...' aimed at '{model_id}'")
    
    # 0. Basic sanitization and safety
    user_text = (user_text or "").strip()
    # Trim very long inputs to keep meta-prompt bounded
    max_tokens = min(settings.TOKEN_DANGER_THRESHOLD, 1200)
    if estimate_tokens(user_text) > max_tokens:
        # Keep the beginning and end context
        half = max(1000, max_tokens * 4 // 2)
        user_text = user_text[:half] + "\n...\n" + user_text[-half:]

    # 1. Get style info for the target model
    all_styles = cache.get_model_styles()
    
    # Check if it's a known model from our config
    model_info = all_styles.get(model_id)
    
    if not model_info:
        # It's a custom model - extract name and use generic style
        logger.warning(f"Model '{model_id}' not found in config, treating as custom model")
        style_guidance = "clear, well-structured instructions with specific examples and context"
        target_model_id = model_id if '/' in model_id else "mistralai/mistral-7b-instruct:free"
        model_display_name = model_id.split('/')[-1] if '/' in model_id else model_id
        model_tips = "Use clear, specific instructions with examples."
    else:
        style_guidance = model_info.get('preferred_format', 'Clear, structured instructions')
        target_model_id = model_info.get('model_id', settings.FREE_MODEL)
        model_display_name = model_id
        model_tips = model_info.get('tips', 'N/A')
        logger.info(f"Using style: {style_guidance}")

    # 2. Create a "meta-prompt"
    # This is the prompt we send to Mistral 7B to generate the *real* prompt
    meta_prompt = f"""You are PromptSmith, an expert prompt engineer with deep knowledge of AI models and prompt optimization.

Your task is to transform a simple user idea into a detailed, high-quality prompt optimized for a specific AI model.

**User's Idea:**
"{user_text}"

**Target AI Model:**
{model_display_name}

**Target AI's Preferred Style:**
"{style_guidance}"

**Your Task:**
Generate a complete, professional prompt that:
1. Uses the preferred format/style mentioned above
2. Includes clear instructions and objectives
3. Provides necessary context
4. Specifies the desired output format
5. Adds relevant examples if appropriate
6. Is immediately ready to use with {model_display_name}

**Important Guidelines:**
- If the target model uses system/user messages, structure accordingly
- If the model prefers XML tags, use them
- Keep the prompt clear, specific, and actionable
- Ensure the prompt will produce the best possible results from {model_display_name}

Additional model-specific tips to consider:
{model_tips}

Generate the optimized prompt now:"""

    # 3. Call the AI to generate the prompt
    logger.debug(f"Calling API with model: {target_model_id}")
    
    # Use configured default model for meta-prompting, or the target model if it's simpler
    generation_model = settings.DEFAULT_MODEL
    
    final_prompt = model_api.call_openrouter(
        prompt=meta_prompt,
        model=generation_model
    )
    
    logger.info("Prompt generation completed")
    return final_prompt

def refine_prompt(previous_prompt: str, feedback: str, model_id: str) -> str:
    """
    Takes an existing prompt and user feedback, then regenerates it.
    """
    logger.info(f"Refining prompt for '{model_id}' with feedback: '{feedback[:50]}...'")
    
    meta_prompt = f"""
You are PromptSmith, an expert prompt engineer.
A user wants to refine a prompt you previously generated.

**Original Prompt:**
{previous_prompt}

**User's Feedback:**
"{feedback}"

Please generate a new, updated prompt that incorporates the user's feedback.
Keep the original topic but adjust the tone, structure, or content as requested.
"""
    
    # Call the API
    logger.debug("Calling API for refinement")
    refined_prompt = model_api.call_openrouter(
        prompt=meta_prompt,
        model=settings.DEFAULT_MODEL  # Use configured default model for refinement
    )
    
    logger.info("Prompt refinement completed")
    return refined_prompt


def analyze_prompt_quality(prompt: str, model_id: str) -> dict:
    """
    Analyze a prompt and return a quality score with actionable suggestions.

    Heuristics considered:
    - Length (not too short, not excessively long)
    - Presence of structure (sections, lists, formatting cues)
    - Clarity indicators (explicit task, constraints, output format)
    - Examples/context presence
    - Safety (no obvious placeholder text)

    Returns a dictionary with:
    - score: 0-100
    - issues: list[str]
    - suggestions: list[str]
    - stats: tokens, words, characters
    - model: model_id
    """
    text = (prompt or "").strip()
    words = count_words(text)
    chars = len(text)
    tokens = estimate_tokens(text)

    score = 100
    issues = []
    suggestions = []

    # Length checks
    if words < 20:
        score -= 20
        issues.append("Prompt is very short; may lack context and specifics.")
        suggestions.append("Add background, constraints, and an explicit objective.")
    elif words > 800:
        score -= 10
        issues.append("Prompt is quite long; may be verbose.")
        suggestions.append("Trim unnecessary text; keep only what's essential for the task.")

    # Structure cues
    has_list = any(bullet in text for bullet in ["\n- ", "\n* ", "1.", "2.", "3."])
    has_sections = any(h in text.lower() for h in [
        "instructions", "context", "examples", "output", "constraints", "role"
    ])
    if not has_list and not has_sections:
        score -= 15
        issues.append("Missing structure (lists or clear sections).")
        suggestions.append("Use headings like 'Instructions', 'Context', 'Output Format' and bullet points.")

    # Role cue
    if not text.lower().startswith("you are") and "role" not in text.lower():
        score -= 5
        issues.append("No clear role or persona specified.")
        suggestions.append("Begin with a role statement (e.g., 'You are an expert ...').")

    # Output format
    mentions_output = any(k in text.lower() for k in ["output format", "return", "produce", "json", "markdown"])
    if not mentions_output:
        score -= 10
        issues.append("Doesn't specify a desired output format.")
        suggestions.append("Specify how the answer should be formatted (e.g., JSON, table, bullet list).")

    # Examples and context
    mentions_examples = any(k in text.lower() for k in ["example", "for instance", "e.g."])
    mentions_context = "context" in text.lower()
    if not (mentions_examples or mentions_context):
        score -= 10
        issues.append("No examples or context provided.")
        suggestions.append("Add 1-2 brief examples or relevant background.")

    # Ambiguity indicators
    if any(k in text.lower() for k in ["etc.", "something", "some", "maybe"]):
        score -= 5
        issues.append("Contains vague terms that reduce specificity.")
        suggestions.append("Replace vague words with concrete, testable requirements.")

    # Token warnings using settings thresholds
    if tokens > settings.TOKEN_DANGER_THRESHOLD:
        score -= 10
        issues.append("Prompt likely exceeds model context window.")
        suggestions.append("Shorten the prompt or move long context to attachments/links.")
    elif tokens > settings.TOKEN_WARNING_THRESHOLD:
        score -= 5
        issues.append("Prompt is large and may be slow/costly.")
        suggestions.append("Consider summarizing context or narrowing the task.")

    # Baseline floor/ceiling
    score = max(0, min(100, score))
    
    # Determine rating class for UI styling
    if score >= 80:
        rating_class = "excellent"
    elif score >= 60:
        rating_class = "good"
    elif score >= 40:
        rating_class = "fair"
    else:
        rating_class = "poor"
    
    # Count sentences (simple approximation - may overcount with abbreviations)
    # This is intentionally simple for performance; more accurate counting would require NLP
    sentences = max(1, len([s for s in text.split('.') if s.strip()]))

    return {
        "score": score,
        "rating_class": rating_class,
        "issues": issues,
        "suggestions": suggestions,
        "metrics": {
            "tokens": tokens,
            "words": words,
            "characters": chars,
            "sentences": sentences,
        },
        "checks": {
            "has_context": mentions_context,
            "has_examples": mentions_examples,
            "has_structure": has_list or has_sections,
            "has_output_format": mentions_output,
        },
        "model": model_id,
    }
