#
# AUTOMATIC1111 Gemini Prompt Writer Extension
#
# Author: Your name/handle
# Version: 1.9 - Reworked prompt for tokenized output, not natural language.
#
# This extension integrates the Google Gemini API into the AUTOMATIC1111 Web UI
# to generate detailed Stable Diffusion prompts from simple user input.
#

import gradio as gr
import modules.scripts as scripts
from modules import shared, script_callbacks
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import json

# --- Configuration ---

# --- MODIFIED SYSTEM PROMPT ---
# This version is heavily modified to force a token-based, comma-separated output
# and strictly avoid natural language sentences.
DEFAULT_SYSTEM_PROMPT = """
You are a technical prompt engineer for the Stable Diffusion image generation model.
Your task is to convert a user's simple idea into a highly detailed, token-based prompt.
The output MUST be a comma-separated list of keywords and descriptive phrases. DO NOT use full sentences.

**Positive Prompt Rules:**
- **Tokenization:** Every descriptive element MUST be a "token" separated by a comma.
- **Structure:** Follow this specific order:
    1.  **Subject:** Start with the main subject, including its count and core identity (e.g., `1girl, solo, cyberpunk mercenary` or `a majestic dragon`).
    2.  **Appearance & Attire:** Detail the subject's physical features, clothing, and gear (e.g., `long pink hair, glowing cybernetic eyes, tactical gear, leather jacket`).
    3.  **Pose & Action:** Describe the subject's pose and what they are doing (e.g., `standing, leaning against a wall, holding a futuristic rifle, looking at viewer`).
    4.  **Setting & Environment:** Describe the background and location (e.g., `neon-lit alleyway, rainy, puddles on the ground, cyberpunk city, skyscrapers in background`).
    5.  **Lighting & Atmosphere:** Detail the lighting conditions and mood (e.g., `dramatic lighting, rim light, volumetric fog, glowing neon signs`).
    6.  **Style & Quality:** End with style and quality keywords (e.g., `(masterpiece), (best quality), ultra-detailed, sharp focus, professional digital art, cinematic`).
- **Emphasis:** Use weighting like `(keyword:1.2)` or `((keyword))` to increase the importance of key concepts.

**Negative Prompt Rules:**
- **Format:** Also a comma-separated list of keywords.
- **Content:** List things to avoid, such as poor quality, mutations, or unwanted elements.
- **Keywords:** Use terms like `(worst quality, low quality:1.4)`, `deformed, ugly, disfigured`, `bad anatomy, mutated hands, extra limbs`, `fused fingers`, `watermark, text, signature`.

**Example:**
- **User's Request:** "A wizard in a library"
- **Correct Output for Positive Prompt:** `1man, old wizard, long white beard, wise expression, wearing ornate blue robes, holding a glowing staff, standing in a vast library, endless bookshelves, floating books, magical atmosphere, shafts of light from high windows, cinematic lighting, masterpiece, best quality, fantasy art, intricate details`

**Output Format:**
You MUST reply with ONLY a JSON object in the following format, with no other text before or after it:
{
  "positive_prompt": "...",
  "negative_prompt": "..."
}
"""

# --- Extension Logic ---
# (The rest of your script remains the same)

class GeminiPromptWriter(scripts.Script):

    def title(self):
        return "Gemini Prompt Writer"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        with gr.Accordion(self.title(), open=False):
            with gr.Row():
                user_input = gr.Textbox(
                    label="Your Idea",
                    lines=3,
                    placeholder="e.g., A portrait of a female mechanic in a futuristic garage."
                )
            with gr.Row():
                generate_button = gr.Button("✨ Generate Prompts", variant="primary")

        json_output_proxy = gr.Textbox(visible=False)

        js_update_prompts = """
        (json_string) => {
            if (!json_string) { return; }
            const data = JSON.parse(json_string);
            if (data.error) {
                console.error("Gemini Extension Error:", data.error);
                return;
            }
            const positive_prompt = data.positive;
            const negative_prompt = data.negative;
            const activeTab = get_uiCurrentTab();
            let prompt_selector, neg_prompt_selector;
            if (activeTab.innerText.trim().toLowerCase().includes("img2img")) {
                prompt_selector = '#img2img_prompt textarea';
                neg_prompt_selector = '#img2img_neg_prompt textarea';
            } else {
                prompt_selector = '#txt2img_prompt textarea';
                neg_prompt_selector = '#txt2img_neg_prompt textarea';
            }
            const positive_textarea = gradioApp().querySelector(prompt_selector);
            const negative_textarea = gradioApp().querySelector(neg_prompt_selector);
            if (positive_textarea) {
                positive_textarea.value = positive_prompt;
                updateInput(positive_textarea);
            }
            if (negative_textarea) {
                negative_textarea.value = negative_prompt;
                updateInput(negative_textarea);
            }
            return "";
        }
        """

        generate_button.click(
            fn=self.generate_prompts_logic,
            inputs=[user_input],
            outputs=[json_output_proxy]
        )

        json_output_proxy.change(
            fn=None,
            inputs=[json_output_proxy],
            outputs=[json_output_proxy],
            _js=js_update_prompts
        )

        return [user_input]

    def generate_prompts_logic(self, user_input):
        api_key = shared.opts.data.get('gemini_api_key', None)
        if not api_key:
            message = "🔴 Gemini API Key not found. Please set it in Settings."
            print(message)
            return json.dumps({"error": message})

        if not user_input:
            message = "🟡 User input is empty."
            print(message)
            return json.dumps({"positive": "", "negative": "", "error": message})

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        print("🔵 Contacting Gemini API for tokenized prompt...")
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            full_prompt = f"{DEFAULT_SYSTEM_PROMPT}\n\nUser's Request: {user_input}"
            
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(response_mime_type="application/json"),
                safety_settings=safety_settings
            )
            
            response_text = response.text
            # The JSON keys are "positive_prompt" and "negative_prompt" as requested in the system prompt
            prompts = json.loads(response_text)
            positive_prompt = prompts.get("positive_prompt", "")
            negative_prompt = prompts.get("negative_prompt", "")
            print("🟢 Successfully generated prompts from Gemini.")
            # The JS expects "positive" and "negative"
            return json.dumps({"positive": positive_prompt, "negative": negative_prompt})
        except Exception as e:
            message = f"🔴 An error occurred: {e}"
            print(message)
            return json.dumps({"error": message})

# --- Settings Integration ---
def on_ui_settings():
    section = ('gemini_prompt_writer', "Gemini Prompt Writer")
    shared.opts.add_option("gemini_api_key", shared.OptionInfo(
        default="",
        label="Google Gemini API Key",
        section=section
    ).info("Get your API key from Google AI Studio."))

script_callbacks.on_ui_settings(on_ui_settings)
