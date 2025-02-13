# https://huggingface.co/microsoft/git-large

import argparse
from PIL import Image
from transformers import AutoProcessor, GitVisionModel


processor = AutoProcessor.from_pretrained("microsoft/git-large")
model = GitVisionModel.from_pretrained("microsoft/git-large")


def git_cap(file: str) -> str:
    image = Image.open(file)
    image = image.convert('RGB')

    # text = 'A picture of'
    inputs = processor(image, return_tensors="pt")
    outputs = model(**inputs)
    caption = processor.decode(outputs[0], skip_special_tokens=True)
    return caption


def blip_main(input_file, output_file):
    output = blip_cap(input_file)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)


if __name__ == '__main__':
    arg = argparse.ArgumentParser()
    arg.add_argument('-i', '--input', help='input image path')
    arg.add_argument('-o', '--output', help='output text path')
    args = arg.parse_args()
    blip_main(args.input, args.output)
