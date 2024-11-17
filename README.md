# Sparkle AI - Your Personal Assistant

Welcome to **Sparkle AI**, a sleek and intuitive virtual assistant designed to simplify your life with cutting-edge AI capabilities. With features powered by powerful language models like **Gemini** and **Ollama**, Sparkle AI transforms the way you interact with your digital environment. From clipboard monitoring to intelligent text processing, it’s here to help you streamline your tasks and provide insightful responses.

## 🚀 Key Features

- **Seamless Text Processing**: Sparkle AI intelligently processes text using state-of-the-art AI models. Whether you're pasting text from the clipboard or typing it in, Sparkle analyzes and responds with context-aware replies.
- **Real-Time AI Responses**: Powered by Gemini and Ollama, it generates concise and professional explanations, or even conversational responses depending on the context of the text.
- **System Tray Integration**: Stay in control with Sparkle AI’s system tray icon. Toggle the assistant on or off with a simple click, and monitor its status directly from the tray.
- **Clipboard Monitoring**: Automatically detects copied or selected text, processes it, and provides insightful analysis or answers. It works seamlessly in the background, ready whenever you need it.
- **Animated UI**: Enjoy a modern, fluid interface with animated elements and a sleek design. Sparkle AI’s processing animation and status indicators are not only functional but fun to watch.
- **Customizable Alerts**: Get real-time error notifications and status updates, ensuring you always know what's happening behind the scenes.

## ⚙️ How It Works

1. **Clipboard Monitoring**: The assistant constantly watches for text changes in your clipboard. It activates whenever new content is copied or selected.
   
2. **Processing**: Once the content is detected, Sparkle AI uses either **Gemini** or **Ollama** to process the text:
   - **Gemini**: A cutting-edge Google model designed for precise analysis of both casual and technical texts.
   - **Ollama**: An AI model that streams content progressively, providing insights as it processes.
   
3. **AI Responses**: After processing, the assistant responds directly on your screen with clear, relevant explanations.

4. **Interaction**: You can interact with Sparkle AI through an interactive overlay, where you can send additional messages or request further information.

## 🔧 Requirements

- **Python 3.x**: Sparkle AI is built with Python 3, leveraging libraries like PyQt6 for the UI, Ollama for AI, and Gemini for enhanced text processing.
- **Dependencies**:
    - `pyperclip`: For clipboard interaction.
    - `win32gui`, `win32con`: For system tray and window manipulation on Windows.
    - `ollama`: To interact with the Ollama AI model.
    - `requests`: For internet connectivity checks.
    - `keyboard`: For capturing hotkeys.
    - `langchain_google_genai`: To interface with the Gemini API.

## ⚡ Getting Started

1. **Install Dependencies**:  
   Clone the repository and install the required Python packages.

   ```bash
   pip install -r requirements.txt
   ```

2. **Run Sparkle AI**:  
   Simply run the application, and Sparkle AI will take care of the rest.

   ```bash
   python main.py
   ```

3. **Toggle Sparkle AI**:  
   You can toggle the assistant on and off by pressing **`Ctrl+Shift+Space`**, or by clicking the system tray icon.

4. **Clipboard Monitoring**:  
   Copy any text, and Sparkle AI will automatically process it in the background and give you a helpful response.

## 🎨 Customization

Sparkle AI comes with built-in design flexibility. The sleek modern UI is customizable through CSS for easy theme changes, allowing you to match it to your style or preferences. 

## 🌟 Why Choose Sparkle AI?

- **Real-time Responses**: Sparkle AI provides real-time feedback and analysis based on the text you share.
- **Non-Intrusive**: It quietly works in the background, only notifying you when something important happens.
- **Advanced AI**: With Gemini and Ollama at its core, Sparkle offers the most advanced processing and conversational capabilities.
- **Easy to Use**: No complicated setup. Just install and go!

## 👨‍💻 Developer’s Corner

### Running in Debug Mode

You can track the application’s inner workings by enabling the debug mode. This will give you timestamps for every key action, ensuring you know exactly what’s happening behind the scenes.

```python
def debug_print(message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[DEBUG {timestamp}] {message}")
    sys.stdout.flush()  # Force immediate output
```

### Architecture Overview

Sparkle AI uses a **multi-threaded design**:
- **TextProcessor Thread**: Handles text processing asynchronously, ensuring the UI remains responsive while the AI processes your input.
- **OverlayWidget**: Manages the UI for displaying responses, errors, and processing status.
- **System Tray Icon**: Acts as a control center, where users can toggle the assistant’s active status.

### Handling AI Responses

When text is processed, **Gemini** or **Ollama** are used depending on the settings. These models return either a structured or stream-based response, which Sparkle displays to the user.

```python
response = self._process_with_gemini()
```

### Error Handling

Errors encountered during processing or internet issues are gracefully caught and displayed on the overlay with clear error messages, ensuring a smooth user experience.

## 📲 Join the Sparkience Community

Sparkle AI is an open-source project. If you’d like to contribute or just want to stay updated with new features, feel free to check out the **[GitHub repository](https://github.com/nitin-sagar-b/sparkience-ai)** and get involved.

---

**Let Sparkle AI take your digital experience to the next level!**  
Stay productive, informed, and engaged with the magic of AI at your fingertips. ✨
