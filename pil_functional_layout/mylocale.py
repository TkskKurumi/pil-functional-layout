def get_default_lang():
	import locale
	lang=locale.getdefaultlocale()
	return lang[0]
def get_default_font():
	'''lang=get_default_lang()
	tmp={'zh_CN':'MSYH.ttc'}
	return tmp.get(lang,'calibri.ttf')'''
	from os import path
	pth=path.dirname(__file__)
	return path.join(pth,'fonts','NotoSansCN.otf')