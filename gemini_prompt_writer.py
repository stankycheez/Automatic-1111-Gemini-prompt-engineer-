#
# AUTOMATIC1111 Gemini Prompt Writer Extension
#
# Author: Your name/handle
# Version: 1.7 - Disabled safety filters and diversified prompt language.
#
# This extension integrates the Google Gemini API into the AUTOMATIC1111 Web UI
# to generate detailed Stable Diffusion prompts from simple user input.
#

import gradio as gr
import modules.scripts as scripts
from modules import shared, script_callbacks
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold # <-- ADDED THIS IMPORT
import json

# --- Configuration ---

# --- MODIFIED SYSTEM PROMPT ---
DEFAULT_SYSTEM_PROMPT = """
You are an expert prompt engineer for generative AI image models, specifically Stable Diffusion.
Your goal is to take a user's simple idea and expand it into a detailed, highly-creative, and diverse prompt.

Generate a positive prompt and a negative prompt based on the user's request.

**Positive Prompt Rules:**
- **Structure:** Start with the core subject, describe it in detail, then describe the environment, atmosphere, lighting, and composition. End with a varied list of quality and style keywords.
- **Be Creative:** Do not use repetitive or generic phrases. Your goal is to generate a unique and artistic prompt every time.
- **Keywords:** Use descriptive, evocative keywords separated by commas.
- **Emphasis:** Use parentheses `()` to add weight to important concepts, but do so sparingly and on different keywords each time.
- **Quality Keywords:** AVOID using the same quality keywords repeatedly. Cycle through a diverse vocabulary like `(best quality)`, `(ultra-detailed)`, `(masterpiece)`, `photorealistic`, `sharp focus`, `8k`, `vivid colors`, `professional photo`, `cinematic`, `intricate details`. DO NOT use all of them at once.
- **Subject:** Describe the subject's appearance, clothing, pose, action, and expression in detail. Build a narrative.
- **Environment & Lighting:** Describe the background, time of day, and atmosphere with evocative language (e.g., 'eerie twilight', 'sun-drenched ruins', 'neon-soaked cyberpunk alley'). Specify the lighting source and style (e.g., 'dramatic rim lighting', 'soft volumetric light', 'caustic reflections').

**Negative Prompt Rules:**
- **Content:** List everything you want to avoid in the image. Be thorough.
- **Keywords:** Use terms like `(worst quality, low quality:1.4)`, `ugly`, `deformed`, `blurry`, `disfigured`, `bad anatomy`, `mutated hands`, `extra limbs`, `fused fingers`, `watermark`, `text`, `signature`, `grainy`.

**Output Format:**
You MUST reply with ONLY a JSON object in the following format, with no other text before or after it:
{
  "positive_prompt": "...",
  "negative_prompt": "..."
}
"""

# --- Extension Logic ---

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

        # --- ADDED SAFETY SETTINGS ---
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        print("🔵 Contacting Gemini API with minimal safety filters...")
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            full_prompt = f"{DEFAULT_SYSTEM_PROMPT}\n\nUser's Request: {user_input}"
            
            # --- MODIFIED API CALL ---
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(response_mime_type="application/json"),
                safety_settings=safety_settings # <-- ADDED THIS PARAMETER
            )
            
            response_text = response.text
            prompts = json.loads(response_text)
            positive_prompt = prompts.get("positive_prompt", "")
            negative_prompt = prompts.get("negative_prompt", "")
            print("🟢 Successfully generated prompts from Gemini.")
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
