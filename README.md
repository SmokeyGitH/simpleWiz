# 💡Simple WiZ Light Controller

A simple web-based controller for **WiZ smart bulbs**, built with Python and Gradio.

The app discovers WiZ bulbs on the local network and lets you control them directly from your browser without relying on the WiZ cloud.

## Features

* 🔍 Discover WiZ bulbs automatically
* 💡 Turn lights ON/OFF
* ☀️ Adjust brightness
* 🎨 Select custom RGB colors
* 🔥 Choose warm, neutral, or cool color temperatures
* 🌐 Control bulbs through a simple browser interface
* 🏠 Local network communication

## How it works

The application uses `pywizlight` to discover and communicate with WiZ bulbs over the local network.

```text
Browser → Gradio → Python → pywizlight → WiZ Bulb
```

Both the computer running the application and the WiZ bulb need to be connected to the same network.

## Installation

```bash
pip install gradio pywizlight
```

Run the application:

```bash
python lights_control.py
```

Then open:

```text
http://localhost:7860
```

## Built With

* **Python**
* **Gradio**
* **pywizlight**
* **asyncio**

## Note

This is a personal project made to experiment with local smart-home control and building a simple interface around the WiZ local protocol.

WiZ is a trademark of its respective owner. This project is not affiliated with or endorsed by WiZ.
