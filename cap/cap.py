# https://huggingface.co/Salesforce/blip-image-captioning-large
# https://huggingface.co/microsoft/git-large

import argparse
from PIL import Image
from session import logging
from translate import translate
from transformers import AutoProcessor, AutoModelForCausalLM
from transformers import BlipProcessor, BlipForConditionalGeneration


def gen_cap(processor, model, image, tokenizer=None, device='cpu'):
    """
    https://huggingface.co/spaces/russellc/comparing-captioning-models
    """
    inputs = processor(images=image, return_tensors="pt").to(device)
    outputs = model.generate(pixel_values=inputs.pixel_values, max_length=50)

    if tokenizer is not None:
        processor = tokenizer
    caption = processor.batch_decode(outputs, skip_special_tokens=True)[0]
    return caption


def blip_cap(file: str) -> str:
    logging.info(f'[CAP]\tblip_cap({file=})')
    logging.info(f'[CAP]\tLoading model...')
    processor = BlipProcessor.from_pretrained('Salesforce/blip-image-captioning-large')
    model = BlipForConditionalGeneration.from_pretrained('Salesforce/blip-image-captioning-large')

    logging.info(f'[CAP]\tProcessing image...')
    image = Image.open(file)
    image = image.convert('RGB')

    # text = 'A picture of'
    # inputs = processor(images=image, text=text, return_tensors='pt')
    caption = gen_cap(processor, model, image)
    logging.info(f'[CAP]\t{caption=}')
    return caption


def git_cap(file: str) -> str:
    logging.info(f'[CAP]\tgit_cap({file=})')
    logging.info(f'[CAP]\tLoading model...')
    processor = AutoProcessor.from_pretrained('microsoft/git-large-coco')
    model = AutoModelForCausalLM.from_pretrained('microsoft/git-large-coco')

    logging.info(f'[CAP]\tProcessing image...')
    image = Image.open(file)
    image = image.convert('RGB')

    caption = gen_cap(processor, model, image)
    logging.info(f'[CAP]\t{caption=}')
    return caption


def cap_main(input_file, output_file, model='blip'):
    logging.info(f'[CAP]\tcap_main({input_file=}, {output_file=}, {model=})')
    if 'blip' in model.lower():
        output = blip_cap(input_file)
    elif 'git' in model.lower():
        output = git_cap(input_file)
    else:
        raise ValueError(f'{model=} undefined')
    output = translate(output)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)


if __name__ == '__main__':
    arg = argparse.ArgumentParser()
    arg.add_argument('-i', '--input', help='input image path')
    arg.add_argument('-o', '--output', help='output text path')
    arg.add_argument('-m', '--model', help='model name')
    args = arg.parse_args()
    cap_main(args.input, args.output, args.model)
