import asyncio
import socket
import gradio as gr
from pywizlight import wizlight, PilotBuilder, discovery

# Cache discovered lights to map display label -> IP
discovered_bulbs = {}

def get_subnet_broadcast():
    """Detects local LAN IP and returns subnet broadcast address (e.g. 192.168.1.255)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        ip_parts = local_ip.split('.')
        ip_parts[-1] = '255'
        return ".".join(ip_parts)
    except Exception:
        return "255.255.255.255"

def discover_bulbs():
    """Scans local subnet for WiZ bulbs using explicit subnet broadcast."""
    async def _discover():
        broadcast_ip = get_subnet_broadcast()
        bulbs = await discovery.discover_lights(broadcast_space=broadcast_ip)
        return bulbs

    try:
        bulbs = asyncio.run(_discover())
        global discovered_bulbs
        for b in bulbs:
            label = f"WiZ Light ({b.ip}) - {b.mac}"
            discovered_bulbs[label] = b.ip
        
        choices = list(discovered_bulbs.keys())
        if not choices:
            return gr.Dropdown(choices=["No bulbs found"], value="No bulbs found")
        
        return gr.Dropdown(choices=choices, value=choices[0])
    except Exception as e:
        return gr.Dropdown(choices=[f"Error: {str(e)}"], value=f"Error: {str(e)}")

def add_manual_ip(ip_address):
    """Fallback: Manually register a bulb IP directly."""
    if not ip_address or len(ip_address.strip().split('.')) != 4:
        return gr.Dropdown(), "⚠️ Invalid IP format"
    
    clean_ip = ip_address.strip()
    label = f"WiZ Light ({clean_ip}) - Manual"
    discovered_bulbs[label] = clean_ip
    choices = list(discovered_bulbs.keys())
    return gr.Dropdown(choices=choices, value=label), f"Added manual IP: {clean_ip}"

def toggle_power(selected_bulb_label, is_on):
    """Executes immediately when power checkbox is toggled."""
    if not selected_bulb_label or selected_bulb_label not in discovered_bulbs:
        return "⚠️ Please select a valid bulb first."

    target_ip = discovered_bulbs[selected_bulb_label]

    async def _toggle():
        light = wizlight(target_ip)
        if is_on:
            await light.turn_on()
            return f"⚡ Power turned ON for {target_ip}"
        else:
            await light.turn_off()
            return f"🔌 Power turned OFF for {target_ip}"

    try:
        return asyncio.run(_toggle())
    except Exception as e:
        return f"Error: {str(e)}"

def update_light(selected_bulb_label, color, preset, brightness):
    """Sends color and brightness parameters to the light."""
    if not selected_bulb_label or selected_bulb_label not in discovered_bulbs:
        return "Error: Please select a valid discovered bulb."

    target_ip = discovered_bulbs[selected_bulb_label]

    async def _send():
        light = wizlight(target_ip)
        
        bright_val = int((brightness / 100) * 255)
        pilot_args = {"brightness": bright_val}

        # Apply Preset or Color
        if preset != "None":
            temp_map = {"Warm (2700K)": 2700, "Neutral (4000K)": 4000, "Cold (6500K)": 6500}
            pilot_args["colortemp"] = temp_map[preset]
        elif color:
            hex_clean = color.lstrip('#')
            rgb = tuple(int(hex_clean[i:i+2], 16) for i in (0, 2, 4))
            pilot_args["rgb"] = rgb

        await light.turn_on(PilotBuilder(**pilot_args))
        return f"Successfully updated bulb at {target_ip}"

    try:
        return asyncio.run(_send())
    except Exception as e:
        return f"Error: {str(e)}"

# Custom CSS for modern Widget cards & switch appearance
custom_css = """
.widget-box {
    background: #1e1e24 !important;
    border-radius: 16px !important;
    padding: 20px !important;
    border: 1px solid #2e2e38 !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.25) !important;
    margin-bottom: 12px !important;
}
.btn-primary-action {
    background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
    color: white !important;
    font-size: 1.1rem !important;
    font-weight: bold !important;
    border-radius: 12px !important;
    height: 50px !important;
}
"""

# Build the Gradio UI
with gr.Blocks(css=custom_css, title="WiZ Dashboard") as demo:
    gr.Markdown("# 💡 WiZ Light Controller")
    
    # Widget 1: Target Selection & Manual Fallback
    with gr.Column(elem_classes=["widget-box"]):
        gr.Markdown("### 🔍 Target Bulb Selection")
        with gr.Row():
            btn_discover = gr.Button("Scan Local Network", variant="secondary")
            bulb_dropdown = gr.Dropdown(label="Select Bulb", choices=[], interactive=True, scale=2)
        with gr.Row():
            manual_ip_input = gr.Textbox(placeholder="e.g. 192.168.1.50", label="Manual IP Input (Bypass Scan)", scale=2)
            btn_add_ip = gr.Button("Add IP Directly", variant="secondary", scale=1)

    # Widget 2: Power Checkbox (Guaranteed Compatibility)
    with gr.Column(elem_classes=["widget-box"]):
        gr.Markdown("### ⚡ Power State")
        power_switch = gr.Checkbox(
            label="Bulb Power (ON / OFF)", 
            value=True,
            interactive=True
        )

    # Widget 3: Color & Presets
    with gr.Column(elem_classes=["widget-box"]):
        gr.Markdown("### 🎨 Color & Profiles")
        with gr.Row():
            color_picker = gr.ColorPicker(label="Hue Panel / Color", value="#F3C632")
            preset_radio = gr.Radio(
                label="Color Profiles", 
                choices=["None", "Warm (2700K)", "Neutral (4000K)", "Cold (6500K)"], 
                value="None"
            )

    # Widget 4: Brightness
    with gr.Column(elem_classes=["widget-box"]):
        gr.Markdown("### ☀️ Brightness Level")
        brightness_slider = gr.Slider(minimum=10, maximum=100, value=100, step=1, label="Brightness (%)")

    # Widget 5: Send Action & Response Status
    with gr.Column(elem_classes=["widget-box"]):
        btn_send = gr.Button("🚀 Update Light Settings", elem_classes=["btn-primary-action"])
        output_status = gr.Textbox(label="Status Response", value="Ready", interactive=False)

    # --- Event Bindings ---
    btn_discover.click(fn=discover_bulbs, outputs=bulb_dropdown)
    btn_add_ip.click(fn=add_manual_ip, inputs=[manual_ip_input], outputs=[bulb_dropdown, output_status])
    
    # Instant power toggle when checkbox is clicked
    power_switch.change(
        fn=toggle_power, 
        inputs=[bulb_dropdown, power_switch], 
        outputs=output_status
    )
    
    # Apply color & brightness
    btn_send.click(
        fn=update_light, 
        inputs=[bulb_dropdown, color_picker, preset_radio, brightness_slider], 
        outputs=output_status
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
