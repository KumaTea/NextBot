# https://huggingface.co/Salesforce/blip-image-captioning-large
# https://huggingface.co/microsoft/git-large

import argparse
from PIL import Image
from transformers import AutoProcessor, GitVisionModel
from transformers import BlipProcessor, BlipForConditionalGeneration


def blip_cap(file: str) -> str:
    processor = BlipProcessor.from_pretrained('Salesforce/blip-image-captioning-large')
    model = BlipForConditionalGeneration.from_pretrained('Salesforce/blip-image-captioning-large')

    image = Image.open(file)
    image = image.convert('RGB')

    # text = 'A picture of'
    inputs = processor(image, return_tensors='pt')
    outputs = model(**inputs)
    caption = processor.decode(outputs[0], skip_special_tokens=True)
    return caption


def git_cap(file: str) -> str:
    processor = AutoProcessor.from_pretrained('microsoft/git-large')
    model = GitVisionModel.from_pretrained('microsoft/git-large')

    image = Image.open(file)
    image = image.convert('RGB')

    # text = 'A picture of'
    inputs = processor(image, return_tensors='pt')
    outputs = model(**inputs)
    caption = processor.decode(outputs[0], skip_special_tokens=True)
    return caption


def cap_main(input_file, output_file, model='blip'):
    if 'blip' in model.lower():
        output = blip_cap(input_file)
    elif 'git' in model.lower():
        output = git_cap(input_file)
    else:
        raise ValueError(f'{model=} undefined')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)


if __name__ == '__main__':
    arg = argparse.ArgumentParser()
    arg.add_argument('-i', '--input', help='input image path')
    arg.add_argument('-o', '--output', help='output text path')
    arg.add_argument('-m', '--model', help='model name')
    args = arg.parse_args()
    cap_main(args.input, args.output, args.model)
