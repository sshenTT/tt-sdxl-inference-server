import streamlit as st
import requests
import os
import time
import glob
from PIL import Image
from datetime import datetime

# Configuration
API_URL = "http://127.0.0.1:8000/image/generations"
AUTH_TOKEN = "your-secret-key"
OUTPUT_DIR = "generated_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def estimate_generation_time(num_inference_steps):
    """
    Estimate generation time based on actual performance metrics from logs:
    - Prompt encoding: ~1s
    - Denoising: ~1.1s per step
    - Image decoding: ~11s
    """
    prompt_encoding_time = 1
    denoising_time_per_step = 1.1
    image_decoding_time = 11
    
    return prompt_encoding_time + (num_inference_steps * denoising_time_per_step) + image_decoding_time

def generate_image(prompt, num_inference_steps):
    """Generate an image using the API."""
    try:
        # Estimate total generation time
        total_gen_time = estimate_generation_time(num_inference_steps)
        
        # Create progress bar and status
        progress_bar = st.progress(0)
        status = st.empty()
        
        # Prepare API request
        payload = {
            "prompt": prompt,  # API expects a string
            "num_inference_step": int(num_inference_steps)  # Ensure it's an integer
        }
        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Start timing
        start_time = time.time()
        status.info(f"Starting image generation... (ETA: {total_gen_time:.1f}s)")

        # Make API request
        response = requests.post(API_URL, json=payload, headers=headers, timeout=300)
        
        if response.status_code == 200:
            # Generate unique filename with timestamp and prompt preview
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prompt_preview = prompt[:30].replace(" ", "_")
            image_filename = f"{timestamp}_{prompt_preview}_{num_inference_steps}steps.png"
            filepath = os.path.join(OUTPUT_DIR, image_filename)
            
            # Save image
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            # Save metadata
            metadata_filename = filepath.replace('.png', '.txt')
            with open(metadata_filename, 'w') as f:
                generation_time = time.time() - start_time
                f.write(f"Prompt: {prompt}\n")
                f.write(f"Inference Steps: {num_inference_steps}\n")
                f.write(f"Generation Time: {generation_time:.2f}s\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            status.success(f"Image generated in {generation_time:.1f}s!")
            return filepath
        else:
            status.error(f"Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        status.error(f"Error: {str(e)}")
        return None
    finally:
        # Clear progress bar after completion
        if 'progress_bar' in locals():
            progress_bar.empty()

def load_image_gallery():
    """Load all generated images and their metadata."""
    images = []
    for image_path in sorted(glob.glob(os.path.join(OUTPUT_DIR, "*.png")), reverse=True):
        metadata_path = image_path.replace('.png', '.txt')
        metadata = {}
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                for line in f:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
        images.append({
            'path': image_path,
            'metadata': metadata
        })
    return images

def main():
    st.set_page_config(
        page_title="Tenstorrent SD3.5 Image Generator",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("Tenstorrent SD3.5 Image Generator")

    # Sidebar for inputs
    with st.sidebar:
        st.header("Generation Settings")
        prompt = st.text_area("Enter your prompt", height=100)
        # Fixed at 28 inference steps
        num_inference_steps = 28
        st.info(f"Using {num_inference_steps} inference steps")
        
        # Show estimated time
        if prompt:
            eta = estimate_generation_time(num_inference_steps)
            st.info(f"Estimated generation time: {eta:.1f} seconds")
        
        # Generate button
        if st.button("Generate Image", type="primary"):
            if prompt:
                generate_image(prompt, num_inference_steps)
            else:
                st.warning("Please enter a prompt")

    # Main area - Image Gallery
    st.header("Generated Images")
    
    # Load and display images in a grid
    images = load_image_gallery()
    
    if not images:
        st.info("No images generated yet. Use the sidebar to generate your first image!")
    else:
        # Create columns for the grid (3 images per row)
        cols = st.columns(3)
        
        for idx, img_data in enumerate(images):
            col = cols[idx % 3]
            with col:
                # Display image
                image = Image.open(img_data['path'])
                st.image(image, use_container_width=True)  # Updated from deprecated use_column_width
                
                # Display metadata in an expander
                with st.expander("Image Details"):
                    metadata = img_data['metadata']
                    st.write(f"**Prompt:** {metadata.get('Prompt', 'N/A')}")
                    st.write(f"**Steps:** {metadata.get('Inference Steps', 'N/A')}")
                    st.write(f"**Generation Time:** {metadata.get('Generation Time', 'N/A')}")
                    st.write(f"**Generated:** {metadata.get('Generated', 'N/A')}")

if __name__ == "__main__":
    main()