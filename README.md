# Automatic-1111-Gemini-prompt-engineer-
# Installation Guide

Follow these three steps to install and configure the extension.

### 1. Install the Google API Library

Your AUTOMATIC1111 environment needs this library to communicate with Google. If you have already done this, you can skip this step.

* Open a command prompt or terminal that has access to your AUTOMATIC1111 Python environment.
* Run the following command:
    ```bash
    pip install google-generativeai
    ```

### 2. Add the Script to AUTOMATIC1111

This process requires creating a specific folder structure.

1.  Start inside your main `stable-diffusion-webui\extensions` folder.

2.  Create a new folder here and name it exactly: `a1111-gemini-prompt-writer`

3.  Go inside the new `a1111-gemini-prompt-writer` folder.

4.  Create another new folder inside it and name this one `scripts`.

5.  Place your `gemini_prompt_writer.py` script file inside the `scripts` folder.

When you are done, the final path to the script file should be:
`\stable-diffusion-webui\extensions\a1111-gemini-prompt-writer\scripts\gemini_prompt_writer.py`

6.  Restart your AUTOMATIC1111 Web UI.

### 3. Configure Your API Key

The extension will not work until you provide your Google Gemini API key.

1.  Get a free API Key from the [Google AI Studio](https://aistudio.google.com/app/apikey).
2.  In your AUTOMATIC1111 Web UI, go to the **Settings** tab.
3.  Find **Gemini Prompt Writer** in the menu on the left side of the page.
4.  Paste your API key into the **"Google Gemini API Key"** field.
5.  Click the orange **Apply settings** button at the top of the page.

The extension is now installed correctly and ready to use.
