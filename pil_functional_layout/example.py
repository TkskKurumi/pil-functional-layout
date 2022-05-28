try:
    from .widgets import *
except Exception:
    from widgets import *
from os import path
result_pth=path.join(path.dirname(__file__),'samples','results')
project_pth=path.dirname(__file__)
avatar_pth=path.join(project_pth,'samples','avatar.jpg')
def profile_renderer():
    def func_avatar(**kwargs):
        avt=kwargs.get("avatar")
        avt=Image.open(avt)
        return avt
    def func_name(**kwargs):
        return kwargs.get("username")
    def func_introduction(**kwargs):
        return kwargs.get("intro")
    
    avt=AvatarCircle(func_avatar,size=50)
    name=Text(func_name,fontSize=36)
    row1=Row([avt,name],alignY=0.618)
    row2=RichText(func_introduction,300,fontSize=24)
    
    ret=Column([row1,row2],width=300)
    return ret
def IM_style_message():
    def func_avatar(**kwargs):
        avt=kwargs.get("avatar")
        if(isinstance(avt,Image.Image)):
            return avt
        else:
            return Image.open(avt)
    def extract_kwa(key):
        def inner(key=key,**kwargs):
            return kwargs.get(key)
        return inner
    w_avt=AvatarCircle(func_avatar,size=100)
    uname=Text(extract_kwa("username"),fontSize=24)
    message=RichText(extract_kwa("message"),alignX=0,alignY=1,fontSize=18,width=300,autoSplit=True,dont_split=True)
    bub=bubble.default(message,border_size=30)
    col=Column([uname,bub],alignX=0.1)
    transparent=Row([w_avt,col],alignY=0)
    with_bg=compositeBG(transparent,extract_kwa("BG"))
    return transparent,with_bg
def im_message_example():
    transparent,with_bg=IM_style_message()
    rich_text_message=[]
    rich_text_message.append("Hi, greets! \nIsn't my avatar cute?\n")
    rich_text_message.append(Image.open(avatar_pth))
    rich_text_message.append("This widget can combine text contents and image contents. Like QQ messages.")
    a=with_bg.render(avatar=avatar_pth,username="TkskKurumi",message=rich_text_message)
    b=transparent.render(avatar=avatar_pth,username="TkskKurumi",message=rich_text_message)
    save_example('im_message_exampleA',a)
    save_example('im_message_exampleB',b)
def setKwargs_example():
    t=Text('content1')
    a=SetKwargs(content=t,fill=c_color_BLUE)
    r=Row([t,a],bg=c_color_WHITE)
    r.render().save(path.join(result_pth,'setKwargs1.png'))
    #wont overwrite bg's own attribute
    b=SetKwargs(content=r,bg=c_color_RED_lighten)
    b.render().save(path.join(result_pth,'setKwargs2.png'))
    #will pass to row renderer because its bg is None
    r.bg=None
    b.render().save(path.join(result_pth,'setKwargs3.png'))
    
if(False and __name__=='__main__'):
    from os import path
    pth=path.dirname(__file__)
    avt=path.join(pth,'samples','avatar.jpg')
    renderer=profile_renderer()
    renderer.render(avatar=avt,username='TkskKurumi',intro='this is users introduction').show()
    _,__=IM_style_message()
    az=[i+' ' for i in "Hi! \nI'm TkskKurumi! Nice to meet you!".split()]+[Image.open(avt)]
    __.render(avatar=avt,username="TkskKurumi",message=az,bg=None).show()
def save_example(name,im):
    p=path.join(result_pth,name+'.png')
    im.save(p)
def row_example():
    a=Text('content1',fill=c_color_RED)
    b=Text('content2',fill=c_color_GREEN)
    c=Text('content3',fill=c_color_BLUE)
    r=Row([a,b,c])
    save_example('row_example',r.render())
def callable_content_example():
    def func(**kwargs):
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d%H%M")+"\n,kwargs=%s"%kwargs
    t=Text(func)
    t.render(bg=c_color_WHITE).save(path.join(result_pth,'callable_content_example1.png'))
    t.render(bg=c_color_BLACK,fill=c_color_WHITE).save(path.join(result_pth,'callable_content_example2.png'))
def plot_bar_chart(items,title,height=512,name_renderer=None,theme_color=c_color_RED_lighten,name_format=None):
    columns=[]
    mx_num=max(items,key=lambda x:x[1])[1]
    font_fill=theme_color.darken().darken()
    borderWidth=height//30
    if(name_renderer is None):
        name_renderer=RichText(width=512,contents=lambda **kwargs:[kwargs.get('name')],fontSize=height//15,fill=font_fill)
    ll=theme_color.alterHSV(theme_color.H-20)
    ru=theme_color.alterHSV(theme_color.H+20)
    bar_fill=gradientBox(width=height,ll=ll,ru=ru).render()
    bar_renderer=progressBar(width=height,borderWidth=0,progress=lambda **kwargs:kwargs.get('progress'),fill=bar_fill)
    name_w=0
    name_h=0
    _items=[]
    for idx,i in enumerate(items):
        name,num=i
        if(name_format is None):
            nm='%s %.1f'%(name,num)
        else:
            nm=name_format(name,num)
        name=name_renderer.render(name=nm)
        w,h=name.size
        name_w=max(name_w,w)
        name_h=max(name_h,h)
        _items.append((name,num))
    for name,num in _items:
        name=resize.expandWH(name,(name_w,name_h))
        bar=bar_renderer.render(progress=num/mx_num).transpose(Image.ROTATE_90)
        r=Column([bar,name])
        columns.append(r)
    bars_renderer=Row(columns,alignY=1)
    title=name_renderer.render(name=title,fontSize=name_renderer.fontSize*2)
    ret_renderer=Column([title,bars_renderer],alignX=0.5,bg=c_color_WHITE,borderWidth=borderWidth)
    return ret_renderer.render()
def plot_bar_chart_horizontal(items,title,size=512,name_renderer=None,theme_color=c_color_RED_lighten,name_format=None):
    rows=[]

    mx_num=max(items,key=lambda x:x[1])[1]
    font_fill=theme_color.darken().darken()
    borderWidth=size//30
    if(name_renderer is None):
        name_renderer=RichText(width=size,contents=lambda **kwargs:[kwargs.get('name')],fontSize=size//20,fill=font_fill)
    ll=theme_color.alterHSV(theme_color.H-20)
    ru=theme_color.alterHSV(theme_color.H+20)
    bar_fill=gradientBox(width=size,ll=ll,ru=ru).render()
    bar_renderer=progressBar(width=size,borderWidth=0,progress=lambda **kwargs:kwargs.get('progress'),fill=bar_fill)
    name_w=0
    name_h=0
    _items=[]
    for idx,i in enumerate(items):
        name,num=i
        if(name_format is None):
            nm='%s %.1f'%(name,num)
        else:
            nm=name_format(name,num)
        name=name_renderer.render(name=nm)
        w,h=name.size
        name_w=max(name_w,w)
        name_h=max(name_h,h)
        _items.append((name,num))
    for name,num in _items:
        name=resize.expandWidth(name,name_w)
        bar=bar_renderer.render(progress=num/mx_num)#.transpose(Image.ROTATE_90)
        r=Row([name,bar])
        rows.append(r)
    #bars_renderer=column(rows,alignY=1)
    title=name_renderer.render(name=title,fontSize=name_renderer.fontSize*2)
    ret_renderer=Column([title]+rows,alignX=0.5,bg=c_color_WHITE,borderWidth=borderWidth)
    return ret_renderer.render()
def plot_example(show=False):
    items=[]
    items.append(("A",3))
    items.append(("B",6))
    items.append(("Our product",8))
    items.append(("Apple",7))
    az=plot_bar_chart(items,"This is a title")
    save_example('bar chart',az)
    az=plot_bar_chart_horizontal(items,"This is a title")
    save_example('bar chart horizontal',az)
    if(show):
        az.show()
if(__name__=='__main__'):
    setKwargs_example()
    callable_content_example()
    row_example()
    im_message_example()
    plot_example()