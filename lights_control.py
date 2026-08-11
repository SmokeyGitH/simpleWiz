import asyncio
import gradio as gr
from pywizlight import wizlight, PilotBuilder, discovery

# Cache discovered lights to map display label -> IP
discovered_bulbs = {}

def discover_bulbs():
    """Scans local network for WiZ bulbs and populates the dropdown."""
    async def _discover():
        bulbs = await discovery.discover_lights(broadcast_space="255.255.255.255")
        return bulbs

    bulbs = asyncio.run(_discover())
    
    global discovered_bulbs
    discovered_bulbs = {f"WiZ Light ({b.ip}) - {b.mac}": b.ip for b in bulbs}
    
    choices = list(discovered_bulbs.keys())
    if not choices:
        return gr.Dropdown(choices=["No bulbs found"], value="No bulbs found")
    
    return gr.Dropdown(choices=choices, value=choices[0])

def update_light(selected_bulb_label, power, color, preset, brightness):
    """Sends the update packet to the selected WiZ bulb."""
    if not selected_bulb_label or selected_bulb_label not in discovered_bulbs:
        return "Error: Please select a valid discovered bulb."

    target_ip = discovered_bulbs[selected_bulb_label]

    async def _send():
        light = wizlight(target_ip)
        
        # Power Off
        if not power:
            await light.turn_off()
            return f"Turned OFF bulb at {target_ip}"

        # Convert brightness scale (0-100% -> 0-255)
        bright_val = int((brightness / 100) * 255)
        pilot_args = {"brightness": bright_val}

        # Apply Preset or Color
        if preset != "None":
            temp_map = {"Warm (2700K)": 2700, "Neutral (4000K)": 4000, "Cold (6500K)": 6500}
            pilot_args["colortemp"] = temp_map[preset]
        elif color:
            # Color picker returns hex string "#RRGGBB"
            hex_clean = color.lstrip('#')
            rgb = tuple(int(hex_clean[i:i+2], 16) for i in (0, 2, 4))
            pilot_args["rgb"] = rgb

        await light.turn_on(PilotBuilder(**pilot_args))
        return f"Successfully updated bulb at {target_ip}"

    try:
        status_msg = asyncio.run(_send())
        return status_msg
    except Exception as e:
        return f"Error: {str(e)}"

# Build the Gradio UI
with gr.Blocks(title="WiZ Light Controller") as demo:
    gr.Markdown("# 💡 WiZ Light Controller")
    
    # 1. Target Selection Block
    with gr.Group():
        gr.Markdown("### 1. Target Selection")
        btn_discover = gr.Button("🔍 Discover Bulbs", variant="secondary")
        bulb_dropdown = gr.Dropdown(label="Select Bulb", choices=[], interactive=True)

    # 2. Controls Block
    with gr.Group():
        gr.Markdown("### 2. Controls")
        power_switch = gr.Checkbox(label="Power Switch", value=True)
        
        with gr.Row():
            color_picker = gr.ColorPicker(label="Hue Panel / Color", value="#F3C632")
            preset_radio = gr.Radio(
                label="Color Profiles", 
                choices=["None", "Warm (2700K)", "Neutral (4000K)", "Cold (6500K)"], 
                value="None"
            )
            
        brightness_slider = gr.Slider(minimum=10, maximum=100, value=100, step=1, label="Brightness (%)")

    # 3. Action Block
    with gr.Group():
        btn_send = gr.Button("Update Light", variant="primary")
        output_status = gr.Textbox(label="Status Response", interactive=False)

    # Event Bindings
    btn_discover.click(fn=discover_bulbs, outputs=bulb_dropdown)
    btn_send.click(
        fn=update_light, 
        inputs=[bulb_dropdown, power_switch, color_picker, preset_radio, brightness_slider], 
        outputs=output_status
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
