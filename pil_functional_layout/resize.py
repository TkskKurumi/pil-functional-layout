from PIL import Image


def stretchHeight(img, height):
    w, h = img.size
    rate = height/h
    w = int(w*rate)
    return img.resize((w, height), Image.LANCZOS)


def stretchWidth(img, width):
    w, h = img.size
    rate = width/w
    h = int(h*rate)
    return img.resize((width, h), Image.LANCZOS)


def expandHeight(img, height, bg=(0, 0, 0, 0)):
    w, h = img.size
    ret = Image.new(img.mode, (w, height), tuple(bg))
    top = int((height-h)/2)
    ret.paste(img, box=(0, top), mask=img)
    return ret


def expandWidth(img, width, bg=(0, 0, 0, 0)):
    w, h = img.size
    ret = Image.new(img.mode, (width, h), tuple(bg))
    left = int((width-w)/2)
    ret.paste(img, box=(left, 0), mask=img)
    return ret


def expandWH(img, size, bg=(0, 0, 0, 0)):
    w, h = size
    return expandHeight(expandWidth(img, w, bg=bg), h, bg=bg)


def cropWidth(img, width):
    w, h = img.size
    left = int((w-width)/2)
    return img.crop((left, 0, left+width, h))


def cropHeight(img, height):
    w, h = img.size
    upper = int((h-height)/2)
    return img.crop((0, upper, w, upper+height))


def cropWH(img, size):
    width, height = size
    rate = width/height
    w, h = img.size
    r = w/h
    if(r > rate):
        return cropWidth(stretchHeight(img, height), width)
    else:
        return cropHeight(stretchWidth(img, width), height)


def stretchIfExceeds(im, size):
    width, height = size
    w, h = im.size
    r = w/h
    if(width and height):
        rate = width/height
        if(r > rate):
            if(w > width):
                return stretchWidth(im, width)
        elif(h > height):
            return stretchHeight(im, height)
    elif(width):
        if(w > width):
            return stretchWidth(im, width)
    elif(height):
        if(h > height):
            return stretchHeight(im, height)
    return im


if(__name__ == '__main__'):
    im = Image.open(
        r"C:\Users\xiaofan\Downloads\pilloWidget\samples\avatar.jpg")
    # cropWH(im,1000,100).show()
    stretchIfExceeds(im, (80, 120)).show()
    stretchIfExceeds(im, (120, 80)).show()
