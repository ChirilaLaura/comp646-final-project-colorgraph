# Import necessary libraries
import logging
import pickle
import io
import os
import random
from typing import Set

import fsspec
import huggingface_hub
from PIL import Image
import datasets
from cr_renderer import CrelloV5Renderer
from cr_renderer.fonts import FontManager

# Set up logging
logging.basicConfig(level=logging.INFO)

# Copy the normalize_family function from the original code
def normalize_family(name: str) -> str:
    """Normalize font name."""
    name = name.replace("_", " ").title()
    name = name.replace(" Bold", "")
    name = name.replace(" Regular", "")
    name = name.replace(" Light", "")
    name = name.replace(" Italic", "")
    name = name.replace(" Medium", "")

    FONT_MAP = {
        "Arkana Script": "Arkana",
        "Blogger": "Blogger Sans",
        "Delius Swash": "Delius Swash Caps",
        "Elsie Swash": "Elsie Swash Caps",
        "Gluk Glametrix": "Gluk Foglihtenno06",
        "Gluk Znikomitno25": "Gluk Foglihtenno06",
        "Im Fell": "Im Fell Dw Pica Sc",
        "Medieval Sharp": "Medievalsharp",
        "Playlist Caps": "Playlist",
        "Rissa Typeface": "Rissatypeface",
        "Selima": "Selima Script",
        "Six": "Six Caps",
        "V T323": "Vt323",
        # The rest is unknown.
        "Different Summer": "Montserrat",
        "Dukomdesign Constantine": "Montserrat",
        "Sunday": "Montserrat",
    }
    return FONT_MAP.get(name, name)

# Create a set to track which fonts we've already tried to look up
attempted_fonts = set()

# Create the patched lookup method
def patched_lookup(self, font_family, font_weight="regular", font_style="regular"):
    """A patched version of the lookup method to prevent infinite loops."""
    assert self._fonts is not None, "Fonts not loaded yet."
    
    # Add font to attempted set to prevent loops
    global attempted_fonts
    if font_family in attempted_fonts:
        # Already tried this font, use a known good font directly
        fallback_family = next(iter(self._fonts.values()))
        logging.debug(f"Already attempted {font_family}, directly using fallback font: {fallback_family[0]['fontFamily']}")
        font = fallback_family[0]
        return font["bytes"]
    
    attempted_fonts.add(font_family)
    
    # Check if font weight and style are valid
    from cr_renderer.fonts import FONT_WEIGHTS, FONT_STYLES
    if font_weight not in FONT_WEIGHTS:
        logging.debug(f"Warning: Invalid font weight: {font_weight}, using 'regular' instead")
        font_weight = "regular"
        
    if font_style not in FONT_STYLES:
        logging.debug(f"Warning: Invalid font style: {font_style}, using 'regular' instead")
        font_style = "regular"
    
    # Normal lookup process
    family = []
    for i, family_name in enumerate([font_family, "Montserrat"]):
        try:
            norm_name = normalize_family(family_name)
            if norm_name in self._fonts:
                family = self._fonts[norm_name]
                if i > 0:
                    logging.debug(f"Font family fallback to {family[0]['fontFamily']}")
                break
        except (KeyError, Exception) as e:
            logging.debug(f"Font family not found: {family_name} ({e})")
    
    if not family and self._fonts:
        family = next(iter(self._fonts.values()))
        logging.debug(f"Font family fallback to {family[0]['fontFamily']}")
    
    # Reset attempted fonts for next lookup
    attempted_fonts.clear()
    
    try:
        font = next(
            font
            for font in family
            if font.get("fontWeight", "regular") == font_weight
            and font.get("fontStyle", "regular") == font_style
        )
    except StopIteration:
        font = family[0]
        logging.debug(f"Font style for {font['fontFamily']} not found: {font_weight} {font_style}, fallback to default")
    
    return font["bytes"]

# Patch the lookup method
FontManager.lookup = patched_lookup

# Define a function to render random examples with higher resolution
def render_random_examples(dataset, renderer, num_examples=300, output_dir="dataset", max_size=1920):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get random indices
    dataset_size = len(dataset)
    indices = random.sample(range(dataset_size), min(num_examples, dataset_size))
    
    successful = 0
    for i, idx in enumerate(indices):
        # Reset the attempted fonts for each new example
        attempted_fonts.clear()
        
        # Progress indication
        if i % 10 == 0:
            print(f"Rendering example {i+1}/{num_examples} (dataset index {idx})")
        
        try:
            # Use the max_size parameter to control resolution
            image_bytes = renderer.render(dataset[idx], max_size=max_size)
            
            # Save the image to disk
            image = Image.open(io.BytesIO(image_bytes))
            
            # Print image dimensions occasionally
            if i % 50 == 0:
                print(f"Image dimensions: {image.width}x{image.height}")
                
            # Save as high quality JPEG
            image.save(f"{output_dir}/example_{idx}.jpg", quality=95)
            successful += 1
            
            # Occasional success report
            if successful % 50 == 0:
                print(f"Successfully rendered {successful} images so far")
                
        except Exception as e:
            print(f"Error rendering example {idx}: {str(e)[:100]}...")  # Truncate long error messages

    print(f"Rendering complete! Successfully rendered {successful} out of {num_examples} requested images.")

# Main execution code
def main():
    print("Starting the rendering process...")
    
    # Download fonts explicitly
    fonts_path = huggingface_hub.hf_hub_download(
        repo_id="cyberagent/crello",
        filename="resources/fonts.pickle",
        repo_type="dataset",
        revision="5.0.0",
    )
    
    print(f"Downloaded fonts from {fonts_path}")
    
    # First, let's check what fonts are actually available
    with fsspec.open(fonts_path, "rb") as f:
        fonts_data = pickle.load(f)
    print(f"Number of font families available: {len(fonts_data)}")
    print(f"First few available fonts: {list(fonts_data.keys())[:5]}")
    
    # Load dataset and set up renderer
    print("Loading dataset...")
    dataset = datasets.load_dataset("cyberagent/crello", revision="5.0.0", split="train")
    print(f"Dataset loaded with {len(dataset)} examples")
    
    print("Setting up renderer...")
    renderer = CrelloV5Renderer(dataset.features, fonts_path)
    
    # Render examples with higher resolution
    print("Starting to render 300 random examples in high resolution...")
    render_random_examples(dataset, renderer, num_examples=350, max_size=1920)

if __name__ == "__main__":
    main()