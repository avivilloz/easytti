# TTI Utils (Text-to-Image)

This Python package automates the process of generating and downloading images from Bing's image creation service using Selenium WebDriver. It handles user authentication, navigates through the image creation process, and manages the download of generated images with built-in error handling and retry mechanisms.

## Description:

This Python package provides a comprehensive solution for generating images using Bing's image creation service. It utilizes Selenium WebDriver to automate browser interactions, allowing users to:
- Authenticate: Log in to Bing accounts securely.
- Generate Images: Navigate to the image creation page, input image descriptions, and initiate the generation process.
- Download Images: Automatically download the generated images to a specified directory.

Key features of the package include:
- User Authentication: Securely log in to Bing accounts.
- Image Generation: Submit prompts and wait for image generation.
- Download Management: Handle the downloading of generated images to a specified directory.
- Error Handling: Robust error management for various scenarios (e.g., no more prompts available, unsafe content detection).
- Retry Mechanism: Implement retries for certain operations to improve reliability.
- Input Validation: Ensure all required parameters are provided and valid.
- Logging: Comprehensive logging throughout the process for debugging and monitoring.

The package uses a synchronous approach for all operations, including downloads. It's designed to work sequentially, processing one image at a time, which ensures stability and simplifies error handling.

This tool is ideal for developers, researchers, and content creators who need to automate the process of generating and collecting images from Bing's AI image generation service. It's particularly useful for tasks involving data collection, content creation, or any application requiring programmatic access to AI-generated images.

## How to install:

Run the following command in your python venv:

```sh
pip install git+https://github.com/avivilloz/tti_utils.git@main#egg=tti_utils
```

Or add the following line to your project's `requirement.txt` file:

```
git+https://github.com/avivilloz/tti_utils.git@main#egg=tti_utils
```

And run the following command:

```sh
pip install -r requirements.txt
```

## How to use:

```python
from tti_utils import generate_images
from tti_utils.exceptions import NoMorePrompts, UnsafeImageContent, ContentWarning

# Define your parameters
dst_dir = "/path/to/download/directory"
image_description = "A serene landscape with mountains and a lake at sunset"
bing_email = "your_bing_email@example.com"
bing_password = "your_bing_password"

try:
    # Generate images
    successful, total = generate_images(
        dst_dir=dst_dir,
        image_description=image_description,
        bing_email=bing_email,
        bing_password=bing_password
    )
    
    print(f"Successfully generated and downloaded {successful} out of {total} images.")

except NoMorePrompts:
    print("No more prompts available for this account.")
except UnsafeImageContent:
    print("The image content was deemed unsafe.")
except ContentWarning:
    print("There was a content warning for this prompt.")
except Exception as e:
    print(f"An unexpected error occurred: {str(e)}")
```

## Logging:

TTI uses Python's built-in logging module. To see log messages, you can set up basic logging in your script:

```python
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
```