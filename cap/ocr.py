import argparse
from PIL import Image
from paddleocr import PaddleOCR


CJK = ['ch', 'korean', 'japan', 'chinese_cht']


arg = argparse.ArgumentParser()
arg.add_argument('-i', '--input', help='input image path')
arg.add_argument('-o', '--output', help='output text path')
arg.add_argument('-l', '--lang', help='language', default='ch')


def get_image_resolution(img: str):
    return Image.open(img).size


def is_same_line(box1: list, box2: list, img_size: tuple, threshold: float = 0.02):
    # box1 = [[26.0, 635.0], [810.0, 635.0], [810.0, 657.0], [26.0, 657.0]]
    # box2 = [[836.0, 636.0], [863.0, 636.0], [863.0, 655.0], [836.0, 655.0]]
    # img_size = [1920, 1080]

    image_width = img_size[0]
    box1_right = (box1[1][0] + box1[2][0]) / 2
    box2_left = (box2[0][0] + box2[3][0]) / 2
    judge_0 = box1_right - box2_left > threshold * 5 * image_width
    if judge_0:  # 框1右边界 > 框2左边界 ==> 框1在框2右边
        return False

    image_height = img_size[1]
    box1_y1 = (box1[0][1] + box1[1][1]) / 2
    box1_y2 = (box1[2][1] + box1[3][1]) / 2
    box2_y1 = (box2[0][1] + box2[1][1]) / 2
    box2_y2 = (box2[2][1] + box2[3][1]) / 2
    box1_height = box1_y2 - box1_y1
    box2_height = box2_y2 - box2_y1
    judge_1 = abs(box1_y1 - box2_y1) < threshold * image_height
    judge_2 = abs(box1_y2 - box2_y2) < threshold * image_height
    judge_3 = abs(box1_height - box2_height) < threshold * image_height
    return judge_1 and judge_2 and judge_3


def is_next_to(box1: list, box2: list, img_size: tuple, threshold: float = 0.02):
    # box1 = [[26.0, 635.0], [810.0, 635.0], [810.0, 657.0], [26.0, 657.0]]
    # box2 = [[836.0, 636.0], [863.0, 636.0], [863.0, 655.0], [836.0, 655.0]]
    # img_size = [1920, 1080]

    image_height = img_size[1]
    box1_right = (box1[1][0] + box1[2][0]) / 2
    box2_left = (box2[0][0] + box2[3][0]) / 2
    judge = abs(box1_right - box2_left) < threshold * image_height
    return judge


def process_result(result: list, img_size: tuple, lang: str = 'ch'):
    result = result[0]
    result_text = ''
    last_result = None
    for line in result:
        # [[[108.0, 52.0], [216.0, 54.0], [216.0, 76.0], [107.0, 74.0]], ('19.8Kp0sts', 0.9711775779724121)]
        box, guess = line
        text, prob = guess
        if last_result:
            if is_same_line(last_result[0], box, img_size):
                if is_next_to(last_result[0], box, img_size):
                    result_text += '' if lang in CJK else ' '
                else:
                    result_text += ' '
            else:
                result_text += '\n'
        result_text += text
        last_result = line
    return result_text


if __name__ == '__main__':
    args = arg.parse_args()
    img_path = args.input

    ocr = PaddleOCR(use_angle_cls=True, lang=args.lang)
    ocr_result = ocr.ocr(img_path, cls=True)
    image_size = get_image_resolution(img_path)
    processed = process_result(ocr_result, image_size, args.lang)

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(processed)
