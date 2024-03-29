from PIL import Image, ImageFont, ImageDraw
from math import ceil
import time
try:
    from .constants import *
    from . import resize
    from . import mylocale
    from .get_emoji import _re as emoji_re, get_emoji
except ImportError:
    from constants import *
    import resize
    import mylocale
    from get_emoji import _re as emoji_re, get_emoji
# const:
# c_color_* for const colors


def none_or(*args):
    for i in args:
        if(i is not None):
            return i
    return None


def solveCallable(i, **kwargs):
    while(callable(i)):
        i = i(**kwargs)
    return i


def _render_content(i, **kwargs):
    i = solveCallable(i, **kwargs)
    if(isinstance(i, Image.Image)):
        return i.convert("RGBA")
    elif(isinstance(i, Widget)):
        return i.render(**kwargs)
    elif(isinstance(i, list)):
        return [_render_content(j, **kwargs) for j in i]
    elif(i is None):
        return None
    else:

        raise Exception("Unsupported widget content %s" %
                        i+" "+str(callable(i)))


class Widget:
    def get_rendered_contents(self, **kwargs):
        ret = list()
        for i in self.contents:
            ret.append(_render_content(i, **kwargs))
        return ret
    def __call__(self, **kwargs):
        return self.render(**kwargs)


class Grid(Widget):
    def __init__(self, contents, borderWidth=None, outerBorder=None, rankdir=None, bg=None, alignX=None, alignY=None, autoAspectRatio=1):
        self.contents = contents
        self.borderWidth = borderWidth
        self.outerBorder = outerBorder
        self.rankdir = rankdir
        self.bg = bg
        self.alignX = alignX
        self.alignY = alignY
        self.autoAspectRatio = autoAspectRatio
    def render(self, **kwargs):
        contents = super().get_rendered_contents(**kwargs)
        borderWidth = none_or(self.borderWidth, kwargs.get("borderWidth"))
        outerBorder = none_or(
            self.outerBorder, kwargs.get("outerBorder"), False)
        rankdir = none_or(self.rankdir, kwargs.get("rankdir"), "LR")
        bg = self.bg or (0, )*4
        alignX = none_or(self.alignX, 0.5)
        alignY = none_or(self.alignY, 0.5)
        if(isinstance(contents[0], list)):
            columns = len(contents)
            rows = len(contents[0])
        else:
            n = len(contents)
            columns = int((n*self.autoAspectRatio)**0.5)
            rows = ceil(n/columns)
            _contents = [[None for y in range(rows)] for x in range(columns)]
            for idx, i in enumerate(contents):
                if(rankdir == "LR"):
                    x = idx % columns
                    y = idx//columns
                else:
                    y = idx % rows
                    x = idx//rows
                _contents[x][y] = i
            contents = _contents
            if(borderWidth is None):
                _w, _h = i.size
                borderWidth = ((_w*_h)**0.5)//5
        column_widths = [0 for i in range(columns)]
        row_heights = [0 for i in range(rows)]
        for x in range(columns):
            for y in range(rows):
                i = contents[x][y]
                if(i is None):
                    continue
                _w, _h = i.size
                column_widths[x] = max(column_widths[x], _w)
                row_heights[y] = max(row_heights[y], _h)
        left = borderWidth if outerBorder else 0
        lefts = []
        for i in column_widths:
            lefts.append(left)
            left += i+borderWidth
        top = borderWidth if outerBorder else 0
        tops = []
        for i in row_heights:
            tops.append(top)
            top += i+borderWidth
        if(outerBorder):
            w, h = int(left), int(top)
        else:
            w, h = int(left-borderWidth), int(top-borderWidth)
        ret = Image.new("RGBA", (w, h), bg)
        for x in range(columns):
            for y in range(rows):
                i = contents[x][y]
                if(i is None):
                    continue
                _w, _h = i.size
                top = tops[y]+(row_heights[y]-_h)*alignY
                left = lefts[x]+(column_widths[x]-_w)*alignX
                ret.paste(i, box=(int(left), int(top)), mask=i)
        return ret


class Row(Widget):
    # layouts a row of widgets
    # if row widget has specified height attribute, it will force its children column layout evenly by setting their height attribute.
    # if row widget has specified width attribute, it will layout children evenly. But won't inherit the attribute to children.
    def __init__(self, contents, bg=None, borderWidth=None, borderColor=None,
                 stretchHeight=None, expandHeight=None, cropHeight=None, alignY=None, height=None, width=None, stretchWH=None, outer_border=None):
        self.contents = contents
        self.stretchHeight = stretchHeight
        self.expandHeight = expandHeight
        self.cropHeight = cropHeight
        self.bg = bg
        self.borderColor = borderColor
        self.borderWidth = borderWidth
        self.alignY = alignY
        self.height = height
        self.width = width
        self.stretchWH = stretchWH
        self.outer_border = outer_border

    def get_rendered_contents(self, **kwargs):
        if(self.height):
            for i in self.contents:
                if(isinstance(i, Column)):
                    if(i.height is None):
                        i.height = self.height
        return super().get_rendered_contents(**kwargs)

    def render(self, **kwargs):
        # **kwargs are inherited attributes like bg color from parznt downwards to children when render

        bg = self.bg or kwargs.get('bg') or c_color_TRANSPARENT
        borderWidth = self.borderWidth or kwargs.get('borderWidth') or 0
        borderColor = self.borderColor or kwargs.get('borderColor') or bg
        #alignY=self.alignY or kwargs.get('alignY') or 1
        alignY = none_or(self.alignY, kwargs.get('alignY'), 0.5)
        outer_border = none_or(
            self.outer_border, kwargs.get("outer_border"), False)
        kwargs['bg'] = bg  # inherit settings
        kwargs['borderWidth'] = borderWidth
        kwargs['borderColor'] = borderColor
        # kwargs['alignY']=alignY

        r_contents = self.get_rendered_contents(**kwargs)
        if(self.stretchWH):
            for idx, i in enumerate(r_contents):
                i = i.resize(self.stretchWH, Image.LANCZOS)
                r_contents[idx] = i
        if(self.stretchHeight):
            for idx, i in enumerate(r_contents):
                i = resize.stretchHeight(i, self.stretchHeight)
                r_contents[idx] = i
        elif(self.expandHeight):
            for idx, i in enumerate(r_contents):
                i = resize.expandHeight(i, self.expandHeight)
                r_contents[idx] = i
        mxHeight = 0
        sWidth = 0
        for i in r_contents:
            w, h = i.size
            mxHeight = max(h, mxHeight)
            sWidth += w
        if(self.width):
            width = self.width
            if(outer_border):
                borderWidthX = (width-sWidth)/(1+len(r_contents))
            else:
                if(len(r_contents) != 1):
                    borderWidthX = (width-sWidth)/(len(r_contents)-1)
                else:
                    borderWidthX = 0  # meaningless
        else:
            borderWidthX = borderWidth
            if(outer_border):
                width = sWidth+borderWidthX*(1+len(r_contents))
            else:
                width = sWidth+borderWidthX*(len(r_contents)-1)

        height = mxHeight+(borderWidth if outer_border else 0)*2

        ret = Image.new("RGBA", (width, height), tuple(bg))
        left = (borderWidthX if outer_border else 0)
        for idx, i in enumerate(r_contents):
            w, h = i.size
            top = int((borderWidth if outer_border else 0)+(mxHeight-h)*alignY)
            ret.paste(i, box=(int(left), top), mask=i)
            left += w+borderWidthX
        return ret


class Column(Widget):
    def __init__(self, contents, bg=None, borderWidth=None, borderColor=None,
                 stretchWidth=None, expandWidth=None, cropWidth=None, alignX=None, height=None, width=None, stretchWH=None, outer_border=False):
        self.contents = contents
        self.stretchWidth = stretchWidth
        self.stretchWH = stretchWH
        self.expandWidth = expandWidth
        self.cropWidth = cropWidth
        self.bg = bg
        self.borderColor = borderColor
        self.borderWidth = borderWidth
        self.alignX = alignX
        self.height = height
        self.width = width
        self.outer_border = outer_border

    def get_rendered_contents(self, **kwargs):
        if(self.width):
            for i in self.contents:
                if(isinstance(i, Row)):
                    if(i.width is None):
                        i.width = self.width
        return super().get_rendered_contents(**kwargs)

    def render(self, **kwargs):
        # **kwargs are inherited attributes like bg color from parent downwards to children when render
        bg = self.bg or kwargs.get('bg') or c_color_TRANSPARENT
        borderWidth = self.borderWidth or kwargs.get('borderWidth') or 0
        borderColor = self.borderColor or kwargs.get('borderColor') or bg
        outer_border = none_or(
            self.outer_border, kwargs.get("outer_border"), False)
        #alignX=self.alignX or kwargs.get('alignX') or 0.5
        alignX = none_or(self.alignX, kwargs.get('alignX'), 0.5)

        kwargs['bg'] = bg  # inherit settings
        kwargs['borderWidth'] = borderWidth
        kwargs['borderColor'] = borderColor
        kwargs['alignX'] = alignX

        r_contents = self.get_rendered_contents(**kwargs)
        if(self.stretchWH):
            for idx, i in enumerate(r_contents):
                i = i.resize(self.stretchWH, Image.LANCZOS)
                r_contents[idx] = i
        if(self.stretchWidth):
            for idx, i in enumerate(r_contents):
                i = resize.stretchWidth(i, self.stretchWidth)
                r_contents[idx] = i
        elif(self.expandWidth):
            for idx, i in enumerate(r_contents):
                i = resize.expandWidth(i, self.expandWidth)
                r_contents[idx] = i
        mxWidth = 0
        sHeight = 0
        for i in r_contents:
            w, h = i.size
            mxWidth = max(mxWidth, w)
            sHeight += h
        if(self.height):
            height = self.height
            if(outer_border):
                borderWidthY = (height-sHeight)/(len(r_contents)+1)
            else:
                if(len(r_contents) != 1):
                    borderWidthY = (height-sHeight)/(len(r_contents)-1)
                else:
                    borderWidthY = 0
        else:
            borderWidthY = borderWidth
            if(outer_border):
                height = sHeight+borderWidthY*(1+len(r_contents))
            else:
                height = sHeight+borderWidthY*(len(r_contents)-1)
        width = mxWidth+2*(borderWidth if outer_border else 0)

        ret = Image.new("RGBA", (width, height), tuple(bg))
        top = borderWidthY if outer_border else 0
        for idx, i in enumerate(r_contents):
            w, h = i.size
            left = int((borderWidth if outer_border else 0)+(mxWidth-w)*alignX)
            ret.paste(i, box=(int(left), int(top)), mask=i)
            top += h + borderWidthY
        return ret


class SizeBox(Widget):
    def __init__(self, content, stretchWH=None, stretchWidth=None, stretchHeight=None, expandHeight=None, expandWidth=None, cropWH=None):
        self.content = content
        self.stretchWidth = stretchWidth
        self.stretchHeight = stretchHeight
        self.expandHeight = expandHeight
        self.expandWidth = expandWidth
        self.stretchWH = stretchWH
        self.cropWH = cropWH

    def render(self, **kwargs):
        ret = _render_content(self.content, **kwargs)
        if(self.cropWH):
            ret = resize.cropWH(ret, self.cropWH)
            return ret
        if(self.stretchWH):
            ret = ret.resize(self.stretchWH, Image.LANCZOS)
            return ret
        if(self.stretchWidth):
            ret = resize.stretchWidth(ret, self.stretchWidth)
            return ret
        if(self.stretchHeight):
            ret = resize.stretchHeight(ret, self.stretchHeight)
            return ret
        if(self.expandHeight):
            if(isinstance(self.expandHeight, tuple)):
                size, bg = self.expandHeight
                ret = resize.expandHeight(ret, size, bg)
                return ret
            else:
                size = self.expandHeight
                bg = kwargs.get("bg") or c_color_TRANSPARENT
                ret = resize.expandHeight(ret, size, bg)
                return ret
        if(self.expandWidth):
            if(isinstance(self.expandWidth, tuple)):
                size, bg = self.expandWidth
                ret = resize.expandWidth(ret, size, bg)
                return ret
            else:
                size = self.expandWidth
                bg = kwargs.get("bg") or c_color_TRANSPARENT
                ret = resize.expandWidth(ret, size, bg)
                return ret
        if(self.expandWH):
            size, bg = self.expandWH
            if(isinstance(bg, tuple)):
                ret = resize.expandWH(ret, size, bg)
                return ret
            else:
                size = size, bg
                bg = kwargs.get("bg") or c_color_TRANSPARENT
                ret = resize.expandWH(ret, size, bg)
                return ret


class SetFont(Widget):
    # used to pass font attribute down to children widgets
    def __init__(self, content, font=None, fontSize=None, lang=None):
        self.font = font
        self.fontSize = fontSize
        self.content = content
        self.lang = lang

    def render(self, **kwargs):
        kwargs['font'] = self.font or kwargs.get('font')
        kwargs['fontSize'] = self.fontSize or kwargs.get('fontSize')
        kwargs['lang'] = self.lang or kwargs.get('lang')
        return self.content.render(**kwargs)


class SetKwargs(Widget):
    def __init__(self, content, **kwargs):
        self.content = content
        self.kwargs = kwargs

    def render(self, **kwargs):
        kwargs.update(self.kwargs)
        return _render_content(self.content, **kwargs)


class _lineFeed:
    pass


class RichText(Widget):
    def __init__(self, contents, width, font=None, fontSize=None, bg=None, lang=None, fill=None, alignY=None, alignX=None, dontSplit=False, imageLimit=None, horizontalSpacing=None, autoSplit=True):
        self.width = width
        self.alignX = alignX
        self.alignY = alignY
        self.font = font
        self.fontSize = fontSize
        self.bg = bg
        self.fill = fill
        self.contents = contents
        self.dontSplit = dontSplit
        self.imageLimit = imageLimit
        self.horizontalSpacing = True
        self.autoSplit = autoSplit

    def render(self, **kwargs):
        font = self.font or kwargs.get('font') or mylocale.get_default_font()
        fontSize = self.fontSize or kwargs.get('fontSize') or 12
        fontSize = solveCallable(fontSize, **kwargs)
        bg = self.bg or kwargs.get('bg') or c_color_TRANSPARENT
        bg = solveCallable(bg, **kwargs)
        fill = self.fill or kwargs.get('fill') or c_color_BLACK
        fill = solveCallable(fill, **kwargs)
        width = self.width or kwargs.get('width')
        alignX = none_or(self.alignX, kwargs.get('alignX'), 0.1)
        alignY = none_or(self.alignY, kwargs.get('alignY'), 1)
        imageLimit = self.imageLimit or kwargs.get(
            'imageLimit') or (width/c_golden_ratio, fontSize*4)
        horizontalSpacing = self.horizontalSpacing or kwargs.get(
            'horizontalSpacing') or int(fontSize/c_golden_ratio)

        fnt = ImageFont.truetype(font, fontSize)

        def render_text(text):
            if(not text):
                return Image.new("RGBA", (1, fontSize), tuple(bg))
            size = fnt.getsize(text)
            ret = Image.new("RGBA", size, tuple(c_color_TRANSPARENT))
            dr = ImageDraw.Draw(ret)
            dr.text((0, 0), text, font=fnt, fill=tuple(fill))
            return ret

        def render_row(_row):
            if(not _row):
                return Image.new("RGBA", (1, fontSize), tuple(bg))
            width = 0
            height = 0
            now_str = ""
            _text_rendered = []
            for i in _row:
                if(isinstance(i, str)):
                    now_str += i
                elif(isinstance(i, Image.Image) or isinstance(i, _lineFeed)):
                    if(now_str):
                        _text_rendered.append(render_text(now_str))
                        now_str = ''
                    if(isinstance(i, Image.Image)):
                        _text_rendered.append(i)

            for i in _text_rendered:
                w, h = i.size
                width += w
                height = max(height, h)
            width += horizontalSpacing*(len(_text_rendered)+1)
            ret = Image.new("RGBA", (width, height), tuple(bg))
            left = horizontalSpacing
            for i in _text_rendered:
                w, h = i.size
                upper = int((height-h)*alignY)
                ret.paste(i, box=(left, upper), mask=i)
                left += w+horizontalSpacing
            return ret

        def calc_row_width(_row):
            nonlocal fnt
            if(not _row):
                return 0
            now_str = ""
            ret = horizontalSpacing
            for i in _row:
                if(isinstance(i, str)):
                    now_str += i
                elif(isinstance(i, Image.Image) or isinstance(i, _lineFeed)):
                    if(now_str):
                        # _text_rendered.append(render_text(now_str))
                        ret += fnt.getsize(now_str)[0]+horizontalSpacing
                        now_str = ''
                    if(isinstance(i, Image.Image)):
                        ret += i.size[0]+horizontalSpacing
            return ret

        __contents = solveCallable(self.contents, **kwargs)
        if(self.autoSplit):
            ___contents = list()
            for i in __contents:
                if(isinstance(i, str)):
                    ___contents.extend([j+' ' for j in i.split(' ')])
                else:
                    ___contents.append(i)
            __contents = ___contents
        _contents = list()
        for i in __contents:
            try:
                content = _render_content(i, **kwargs)
            except Exception as e:
                if(isinstance(i, str)):
                    content = solveCallable(i, **kwargs)  # is string
                else:
                    raise e
            if(isinstance(content, str)):
                if(self.dontSplit):
                    for jdx, j in enumerate(content.split('\n')):
                        if(jdx != 0):
                            _contents.append(_lineFeed())
                        _contents.append(j)
                else:
                    for j in content:
                        if(j == '\n'):
                            _contents.append(_lineFeed())
                        else:
                            if(emoji_re.match(j)):
                                try:
                                    code = hex(ord(j)).upper()[2:]
                                    print("emoji", code)
                                    im = get_emoji(code).convert("RGBA")
                                    im = resize.stretchHeight(im, fontSize)
                                    _contents.append(im)
                                except Exception:
                                    _contents.append(j)
                            else:
                                _contents.append(j)
            elif(isinstance(content, Image.Image)):
                '''if(content.width>width):
                    content=resize.stretchWidth(content,width)'''
                content = resize.stretchIfExceeds(content, imageLimit)
                _contents.append(content)

        rows = list()
        _row = [_lineFeed()]

        for i in _contents:
            if(isinstance(i, _lineFeed)):
                rows.append(_row)
                _row = [_lineFeed()]
                continue
            _row.insert(-1, i)
            if(calc_row_width(_row) > width):
                _row.pop(-2)
                rows.append(_row)
                _row = [i, _lineFeed()]
        rows.append(_row)

        rows = [render_row(_row) for _row in rows]

        width = 0
        height = 0
        for i in rows:
            w, h = i.size
            width = max(width, w)
            height += h
        ret = Image.new("RGBA", (width, height), tuple(bg))
        top = 0
        for i in rows:
            w, h = i.size
            left = int((width-w)*alignX)
            ret.paste(i, box=(left, top), mask=i)
            top += h

        return ret


class Pill(Widget):
    def __init__(self, contentA, contentB, height=None, colorBorder=None, colorA=None, colorB=None, borderWidth=None, borderInner=None, alignY=1):
        self.contentA = contentA
        self.contentB = contentB
        self.height = height
        self.colorBorder = colorBorder
        self.colorA = colorA
        self.colorB = colorB
        self.borderWidth = borderWidth
        self.borderInner = borderInner
        self.alignY = alignY

    def render(self, **kwargs):
        contentA = _render_content(self.contentA, **kwargs).convert("RGBA")
        contentB = _render_content(self.contentB, **kwargs).convert("RGBA")
        height = None or max(contentA.size[1], contentB.size[1])
        borderWidth = none_or(self.borderWidth, height//6)
        borderInner = none_or(self.borderInner, borderWidth)
        bw = borderWidth
        bi = borderInner
        colorA = none_or(self.colorA, c_color_RED)
        colorB = none_or(self.colorB, c_color_WHITE)
        colorBorder = none_or(self.colorBorder, c_color_RED)

        w, h = contentA.size[0]+contentB.size[0], height
        w, h = w+bw*2+height, height+bw*2
        w, h = w+bi*2, h+bi*2
        ret = Image.new("RGBA", (w, h), (0, )*4)
        dr = ImageDraw.Draw(ret)

        dr.pieslice((0, 0, h, h), 90, 270, tuple(colorBorder))
        dr.pieslice((bw, bw, h-bw, h-bw), 90, 270, tuple(colorA))
        dr.pieslice((w-h, 0, w, h), -90, 90, tuple(colorBorder))
        dr.pieslice((w-h+bw, bw, w-bw, h-bw), -90, 90, tuple(colorB))

        dr.rectangle((h/2, 0, w-h/2, h), fill=tuple(colorBorder))
        dr.rectangle(
            (h/2, bw, h/2+contentA.size[0]+bi, h-bw), fill=tuple(colorA))
        dr.rectangle((h/2+contentA.size[0]+bi,
                     bw, w-h/2, h-bw), fill=tuple(colorB))

        top = bw+bi+int((height-contentA.size[1])*self.alignY)
        ret.paste(contentA, (h//2, top), mask=contentA)
        top = bw+bi+int((height-contentB.size[1])*self.alignY)
        ret.paste(contentB, (h//2+contentA.size[0]+bi*2, top), mask=contentB)
        return ret


class Text(Widget):
    # content should be str or callable object that returns str
    def __init__(self, content, font=None, fontSize=None, bg=None, lang=None, fill=None):
        self.font = font
        self.fontSize = fontSize
        self.bg = bg
        self.fill = fill
        self.content = content
        # self.lang=lang

    def render(self, **kwargs):
        font = self.font or kwargs.get('font') or mylocale.get_default_font()
        fontSize = self.fontSize or kwargs.get('fontSize') or 12
        fontSize = solveCallable(fontSize, **kwargs)
        #lang=self.lang or kwargs.get('lang') or mylocale.get_default_lang()
        bg = self.bg or kwargs.get('bg') or c_color_TRANSPARENT
        fill = self.fill or kwargs.get('fill') or c_color_BLACK

        content = solveCallable(self.content, **kwargs)

        fnt = ImageFont.truetype(font, fontSize)
        size = fnt.getsize(content)
        ret = Image.new("RGBA", size, tuple(bg))
        dr = ImageDraw.Draw(ret)
        dr.text((0, 0), content, font=fnt, fill=tuple(fill))
        return ret


class AvatarCircle(Widget):
    def __init__(self, content, size=None, bg=None):
        """
            content: Image, Widget, or Callable(kwargs)
            size: Avatar size, w=h=size
            bg: Color
        """
        self.size = size
        self.content = content
        self.bg = bg

    def render(self, **kwargs):
        bg = self.bg or kwargs.get('bg') or c_color_TRANSPARENT

        kwargs['bg'] = bg

        content = _render_content(self.content, **kwargs)
        if(self.size is None):
            size = min(content.size)
        else:
            size = self.size
        mask = Image.new("L", (size, size), 0)
        dr = ImageDraw.Draw(mask)
        dr.ellipse((0, 0, size, size), fill=255)

        content = resize.cropWH(content, (size, size))
        ret = Image.new("RGBA", (size, size), tuple(bg))
        ret.paste(content, mask=mask)
        return ret


class CompositeBG(Widget):
    def __init__(self, content, bg=None):
        self.content = content
        self.bg = bg

    def render(self, **kwargs):
        content = _render_content(self.content, **kwargs)
        # BG=_render_content(self.BG).copy()
        bg = solveCallable(none_or(solveCallable(
            self.bg, **kwargs), kwargs.get("bg"), c_color_WHITE), **kwargs)
        if(isinstance(bg, color)):
            bg = Image.new("RGBA", content.size, tuple(bg))
        else:
            bg = _render_content(bg, **kwargs).copy()
        bg = resize.cropWH(bg, content.size)
        # bg.paste(content, mask=content)
        bg.alpha_composite(content)
        return bg


class colorBox(Widget):
    def __init__(self, bg, width, height=None):
        self.bg = bg
        self.width = width
        self.height = none_or(height, width)

    def render(self, **kwargs):
        return Image.new("RGBA", (self.width, self.height), tuple(self.bg))


class gradientBox(Widget):
    def __init__(self, width=None, height=None, lu=None, ru=None, ll=None, rl=None):
        self.lu = lu
        self.ru = ru
        self.ll = ll
        self.rl = rl
        self.width = width
        self.height = height

    def judge_type(self):
        def tmp(x): return 0 if (x is None) else 1
        bin = tmp(self.lu)
        bin |= tmp(self.ru) << 1
        bin |= tmp(self.ll) << 2
        bin |= tmp(self.rl) << 3
        return bin

    def render(self, **kwargs):
        width = self.width or kwargs.get('grad_width') or 512
        height = self.height or kwargs.get('grad_height') or 512

        type = self.judge_type()

        ret = Image.new("RGBA", (width, height))

        def get(x, y):
            x_norm = x/width
            y_norm = y/height
            if(type == 0b1010):  # lu set and ll set, verticle
                return self.ll*y_norm+self.lu*(1-y_norm)
            elif(type == 0b1100):  # lu set and ru set, horizontal
                return self.ru*x_norm+self.ru*(1-x_norm)
            elif(type == 0b1001):  # lu set and rl set, ////
                x_ = (x_norm+y_norm)/2
                return self.lu*(1-x_)+self.rl*x_
            elif(type == 0b0110):  # ll set and ru set, \\\\
                x_ = (x_norm+1-y_norm)/2
                return self.ll*(1-x_)+self.ru*x_
            else:
                _ = ['lu', 'ru', 'll', 'rl'][::-1]
                __ = []
                for i in range(4):
                    if(type & (1 << i)):
                        __.append(_[i])
                raise Exception("Unsupported gradient(%s)" % (",".join(__)))
        for x in range(width):
            for y in range(height):
                ret.putpixel((x, y), tuple(get(x, y)))
        del get
        return ret


class AddBorder(Widget):
    def __init__(self, content, borderWidth=None, borderColor=None):
        self.content = content
        self.borderWidth = borderWidth
        self.borderColor = borderColor

    def render(self, **kwargs):
        content = _render_content(self.content, **kwargs)
        borderWidth = none_or(self.borderWidth, kwargs.get("borderWidth"))
        invertBG = None if(kwargs.get("bg") is None) else color.fromany(
            kwargs.get("bg")).invert()
        borderColor = none_or(self.borderColor, kwargs.get(
            "borderColor"), invertBG, c_color_TRANSPARENT)
        w, h = content.size
        if(borderWidth is None):
            borderWidth = (w*h)**0.5
            borderWidth = int(borderWidth/20)
        width, height = w+borderWidth*2, h+borderWidth*2
        ret = Image.new("RGBA", (width, height), tuple(borderColor))
        ret.paste(content, box=(borderWidth, borderWidth))
        return ret


addBorder = AddBorder


class bubble(Widget):
    def __init__(self, content, kwa):
        self.content = content
        self.kwa = kwa

    def from_dir(content, pth, **kwa):
        # left-upper upper right-upper left middle right left-lower lower right-lower
        from os import path
        for i in ['lu', 'up', 'ru', 'le', 'mi', 'ri', 'll', 'lo', 'rl']:
            if(path.exists(path.join(pth, i+'.png'))):
                kwa[i] = Image.open(path.join(pth, i+'.png'))
        return bubble(content, kwa)

    def default(content, **kwa):
        from os import path
        pth = path.dirname(__file__)
        pth = path.join(pth, 'samples', 'bubble')
        return bubble.from_dir(content, pth, **kwa)

    def render(self, **kwargs):

        kwa = dict()
        kwa.update(self.kwa)
        kwa.update(**kwargs)
        img = _render_content(self.content, **kwargs)
        lu = kwa.get('lu')
        up = kwa.get('up')
        ru = kwa.get('ru')
        le = kwa.get('le')
        mi = kwa.get('mi')
        ri = kwa.get('ri')
        ll = kwa.get('ll')
        lo = kwa.get('lo')
        rl = kwa.get('rl')
        border_size = kwa.get('border_size')
        mid_border_size = kwa.get('mid_border_size')
        if(border_size is None):
            border_size = int(img.size[1])
        if(mid_border_size is None):
            mid_border_size = int(border_size/1.618)
        _, __ = img.size
        _ -= 2*(border_size-mid_border_size)
        __ -= 2*(border_size-mid_border_size)
        bs = border_size
        w, h = _+border_size*2, __+border_size*2
        ret = Image.new("RGBA", (w, h))
        ret1 = Image.new("RGBA", (w, h))
        if(ru is None):
            ru = lu.transpose(Image.FLIP_LEFT_RIGHT)
        if(ri is None):
            ri = le.transpose(Image.FLIP_LEFT_RIGHT)
        if(rl is None):
            rl = lu.transpose(Image.ROTATE_180)
        if(lo is None):
            lo = up.transpose(Image.FLIP_TOP_BOTTOM)
        if(ll is None):
            ll = lu.transpose(Image.FLIP_TOP_BOTTOM)

        ret.paste(lu.resize((bs, bs), Image.LANCZOS), (0, 0))
        ret.paste(up.resize((_, bs), Image.LANCZOS), (bs, 0))
        ret.paste(ru.resize((bs, bs), Image.LANCZOS), (bs+_, 0))
        # ret.show()

        ret.paste(le.resize((bs, __), Image.LANCZOS), (0, bs))
        ret.paste(mi.resize((_, __), Image.LANCZOS), (bs, bs))
        ret.paste(ri.resize((bs, __), Image.LANCZOS), (bs+_, bs))
        # ret.show()

        ret.paste(ll.resize((bs, bs), Image.LANCZOS), (0, bs+__))
        ret.paste(lo.resize((_, bs), Image.LANCZOS), (bs, bs+__))
        ret.paste(rl.resize((bs, bs), Image.LANCZOS), (bs+_, bs+__))
        # ret.show()

        ret1.paste(img, (mid_border_size, mid_border_size))
        # print(bs,mid_border_size)
        # ret1.show()
        return Image.alpha_composite(ret, ret1)


class gif(Widget):
    def __init__(self, frames, fps):
        self.frames = frames
        self.fps = fps

    def render(self, **kwargs):
        frames = solveCallable(self.frames)
        le = len(frames)
        idx = int(time.time()*self.fps) % le
        return _render_content(frames[idx])


class ProgressBar(Widget):
    def __init__(self, width, bg=None, fill=None, height=None, progress=None, borderColor=None, resizeMethod=resize.cropWH, borderWidth=None):
        self.bg = bg
        self.fill = fill
        self.width = width
        self.height = height  # outer height
        self.progress = progress
        self.borderWidth = borderWidth
        self.borderColor = borderColor
        self.resizeMethod = resizeMethod

    def render(self, **kwargs):
        progress = none_or(self.progress, kwargs.get('progress'))
        progress = solveCallable(progress, **kwargs)
        bg = tuple(none_or(self.bg, kwargs.get("bg"), c_color_WHITE))
        fill = solveCallable(none_or(self.fill, kwargs.get(
            "fill"), c_color_BLUE_lighten), **kwargs)
        width = self.width
        height = none_or(self.height, width//10)
        borderWidth = none_or(self.borderWidth, int(height/6))
        borderColor = tuple(none_or(self.borderColor, c_color_MIKU_darken))

        bw = int(borderWidth)
        pw = (width-bw*2)*progress

        ret = Image.new("RGBA", (width, height), borderColor)
        dr = ImageDraw.Draw(ret)
        dr.rectangle((bw, bw, width-bw-1, height-bw-1), fill=bg)
        if(isinstance(fill, tuple) or isinstance(fill, color)):
            if(isinstance(fill, color)):
                fill = tuple(fill)
            dr.rectangle((bw, bw, bw+pw, height-bw), fill=fill)
        elif(isinstance(fill, Widget) or isinstance(fill, Image.Image)):
            pw = int(pw)
            ph = int(height-bw*2)
            if(isinstance(fill, Widget)):
                kwa = {}
                kwa.update({'progbar_width': pw, 'grad_width': pw})
                kwa.update({'progbar_height': pw, 'grad_height': ph})
                fill = fill.render(**kwargs)
            size = pw, ph
            fill = self.resizeMethod(fill, size)
            ret.paste(fill, box=(bw, bw), mask=fill)
        else:
            raise Exception("Unsupported progress bar fill %s" % fill)
        return ret


def fExtractKwa(key):
    def inner(key=key, **kwargs):
        return kwargs.get(key)
    return inner


if(__name__ == '__main__'):  # test
    contents = ["foo","\n", "bar"]
    rt = RichText(contents, fill=(255,)*4, width=512)
    im = rt.render()

    pth = "/tmp/a.png"
    im.save(pth)
    print(pth)