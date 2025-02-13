import io
import logging
from PIL import Image
from transformers import AutoTokenizer, ViTImageProcessor, VisionEncoderDecoderModel


device = 'cpu'
model_name = 'nlpconnect/vit-gpt2-image-captioning'

# Initialize the feature extractor, tokenizer, and model
feature_extractor = ViTImageProcessor.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = VisionEncoderDecoderModel.from_pretrained(model_name, low_cpu_mem_usage=True).to(device)
# https://huggingface.co/docs/transformers/main_classes/model#large-model-loading


def input_to_pil(im):
    if isinstance(im, bytes):
        logging.info('  Convert bytes to BytesIO')
        im = io.BytesIO(im)
    if isinstance(im, str) or isinstance(im, io.BytesIO):
        # If the input is a file path, open the image using a context manager
        logging.info('  Convert to PIL.Image')
        with Image.open(im) as image_file:
            image = image_file.convert('RGB')
            image = feature_extractor(image, return_tensors="pt").pixel_values.to(device)
    elif isinstance(im, Image.Image):
        # If the input is a PIL.Image object, convert it to a tensor and move it to the specified device
        image = feature_extractor(im, return_tensors="pt").pixel_values.to(device)
    else:
        raise ValueError(f'Invalid input type: {type(im)}. Expected file path or PIL.Image object.')

    return image


def get_caption(im, max_length=64, num_beams=4):
    logging.info('Caption: loading image...')
    image = input_to_pil(im)

    # Generate the caption using the pre-trained model
    # caption_ids = model.generate(image, max_length=max_length, num_beams=num_beams)[0]
    logging.info('Caption: predicting...')
    caption_ids = model.generate(image, max_length=max_length)[0]
    caption_text = tokenizer.decode(caption_ids)
    caption_text = caption_text.replace('<|endoftext|>', '').split('\n')[0].strip()
    return caption_text
