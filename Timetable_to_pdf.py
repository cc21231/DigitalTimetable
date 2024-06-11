import json
import math
import os
import sys
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
# from reportlab.lib. import
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib.units import inch
from reportlab.platypus import (
      BaseDocTemplate, Frame, Paragraph, NextPageTemplate,
      PageBreak, PageTemplate, Image, Table, TableStyle, Spacer)
from reportlab.lib import colors

from reportlab.platypus.flowables import Flowable

import tkinter as tk
#
# class ExportAsPDFMenu(tk.Toplevel):
# 	def __init__(self, *args, **kwargs):
# 		super().__init__(*args, **kwargs)
#
# 		self.presets_selector
# 		self.width_entry
# 		self.height_entry
# 		self.units_selector
#
# 		self.expand_x_toggle
# 		self.expand_y_toggle
# 		self.bottom_padding
#
# 		self.corner_radius
#
# 		self.page_preview
#
# 		self.format_preview_frame
# 		self.h_header_preview
# 		self.v_header_preview
# 		self.session_break_preview
# 		self.room_preview
# 		self.teacher_preview
# 		self.day_preview
#
# 		self.header_font_family
# 		self.header_font_style
# 		self.header_font_size
# 		self.header_font_colour
# 		self.header_background
#
# 		self.session_font_family
# 		self.session_font_style
# 		self.session_font_size
# 		self.session_font_colour
# 		self.session_background
#
# 		self.cell_font_family
# 		self.cell_font_style
# 		self.cell_font_size
# 		self.cell_font_colour
# 		self.cell_background
#
# 		self.table_border_width
# 		self.table_border_colour


class FormattingOption(tk.Frame):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.class_dropdown = tk


class verticalText(Flowable):
	'''
	Rotates a text in a table cell.
	From: https://stackoverflow.com/a/40349017
	'''

	def __init__(self, text, bottompadding=0):
		Flowable.__init__(self)
		self.text = text
		self.bottompadding = bottompadding

	def draw(self):
		canvas = self.canv
		canvas.rotate(90)
		fs = canvas._fontsize
		canvas.translate(1, -fs/1.2)  # canvas._leading?
		canvas.drawString(0, self.bottompadding, self.text)

	def wrap(self, aW, aH):
		canv = self.canv
		fn, fs = canv._fontname, canv._fontsize
		return canv._leading, 1 + canv.stringWidth(self.text, fn, fs)

from PyPDF2 import PdfMerger
from reportlab.lib.units import cm
import reportlab.lib.units
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph
from webbrowser import open as webbrowser_open
from more_itertools import divide

# reportlab.lib.units.toLength(String(150,100, 'Hello World', fontSize=18, fillColor=colors.red))

def hex_to_rgb(hex_string, divisions=3):
	sections = [''.join(i) for i in divide(divisions, hex_string[1:])]
	return list(map(lambda v: int(v * (3 - len(v)), 16) / 255, sections))


styles = getSampleStyleSheet()

pdfmetrics.registerFont(TTFont(f'Calibri-Bold', 'calibrib.ttf'))
pdfmetrics.registerFont(TTFont(f'Calibri', 'calibri.ttf'))

styles.add(ParagraphStyle(name='Heading',
                          parent=styles['Normal'],
                          fontName='Calibri-Bold',
                          wordWrap='LTR',
                          alignment=TA_CENTER,
                          fontSize=12,
                          leading=13,
                          textColor=colors.black,
                          borderPadding=0,
                          leftIndent=0,
                          rightIndent=0,
                          spaceAfter=0,
                          spaceBefore=0,
                          splitLongWords=True,
                          spaceShrinkage=0.05,
                          ))
styles.add(ParagraphStyle(name='Vert_Heading',
                          parent=styles['Normal'],
                          fontName='Calibri-Bold',
                          wordWrap='LTR',
                          alignment=TA_CENTER,
                          orient='vertica',
                          fontSize=12,
                          leading=13,
                          textColor=colors.black,
                          borderPadding=0,
                          leftIndent=0,
                          rightIndent=0,
                          spaceAfter=0,
                          spaceBefore=0,
                          splitLongWords=True,
                          spaceShrinkage=0.05,
                          ))
styles.add(ParagraphStyle(name='Body',
                          alignment=TA_LEFT,
                          fontName='Calibri',
                          fontSize=7,
                          textColor=colors.darkgray,
                          leading=8,
                          textTransform='uppercase',
                          wordWrap='LTR',
                          splitLongWords=True,
                          spaceShrinkage=0.05,
                          ))



def convert_to_pdf_2(input_filename, doc_w, doc_h, offset, dir_name, output_filename, append=False, expand=(False, False), colours=['#fff', '#000', '#000'], bottompadding = [5, 15, 25]):
	with open(input_filename, 'r', encoding='utf-8') as input_file:
		timetable = json.load(input_file)

	# document = BaseDocTemplate(output_filename)
	if append:
		canvas = Canvas(dir_name + '/img2pdf_tmp.pdf', (doc_w, doc_h))
	else:
		canvas = Canvas(output_filename, (doc_w, doc_h))

	elems = []

	if not expand[0]:
		bottompadding = [0, *bottompadding[1:]]
	if not expand[1]:
		bottompadding = [bottompadding[0], 0, 0]

	# title_frame_1 = Frame(0 * cm, 0 * cm, 17.5 * cm, 22.5 * cm, id='col1', showBoundary=0)
	# title_template_1 = PageTemplate(id='OneCol', frames=title_frame_1)
	# canvas.addPageTemplates([title_template_1])

	cw = [0.625 * cm] + [2 * cm] * 7
	rh = [0.625 * cm]

	data = [
		['', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
	]
	ts = [
		('GRID', (0, 0), (-1, -1), 0.5, colors.black),
		('ALIGN', (0, 0), (-1, -1), 'CENTER'),
		('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
		('FONT', (0, 0), (0, -1), 'Calibri-Bold', 7, 7),
		('FONT', (0, 0), (-1, 0), 'Calibri-Bold', 7, 7),
		('FONT', (1, 1), (-1, -1), 'Calibri', 7, 7),
		# ('TOPPADDING', (0, 0), (-1, -1), 0),

		# ('FONTSIZE', (0, 0), (0, -1), 0.625 * cm),
		# ('FONTSIZE', (0, 0), (-1, 0), 0.625 * cm),
		# ('FONTSIZE', (1, 1), (-1, -1), 0.625 * cm),
		# ('ROUNDEDCORNERS', (0, 0), (-1, -1), '5,5,0,0'),
		# ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
		('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
		('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
		('SPAN', (-2, 2), (-2, -1)),
		('SPAN', (-1, 2), (-1, -1)),
	]

	if bottompadding[2]:
		ts.append(('BOTTOMPADDING', (0, 0), (-1, 0), bottompadding[2]))
	if bottompadding[1]:
		ts.append(('BOTTOMPADDING', (1, 1), (-1, -1), bottompadding[1]))


	break_count = 0


	for n, i in enumerate(timetable['sessions']):
		if i[1]:
			line_data = [[verticalText(i[0], bottompadding[0])], [''], ['']]
			ts.extend([('SPAN', (0, len(data)), (0, len(data) + 2)), ('FONT', (1, len(data)), (-1, len(data)), 'Calibri-Bold', 7, 7)])
			rh.extend([0.625 * cm] * 3)
			for day_num, day in enumerate(timetable['timetable']):
				# print(day, n)
				class_index = day[n - break_count]
				line_data[0].append(timetable['classes'][class_index])
				line_data[1].append(timetable['teachers'][class_index])
				line_data[2].append(timetable['rooms'][class_index])
			line_data[0].extend(['', ''])
			line_data[1].extend(['', ''])
			line_data[2].extend(['', ''])

			data.extend(line_data)
		else:
			break_count += 1
			line_data = [i[0]] + [''] * 5
			ts.extend([('SPAN', (0, len(data)), (-3, len(data))), ('FONT', (1, len(data)), (-1, len(data)), 'Calibri-Bold'), ('BACKGROUND', (1, len(data)), (-3, len(data)), colors.lightgrey)])
			if bottompadding[2]:
				ts.append(('BOTTOMPADDING', (0, len(data)), (-3, len(data)), bottompadding[2]))
			rh.append(0.625 * cm)
			data.append(line_data)
	data[1][-1] = 'Homework'
	data[1][-2] = 'Homework'
	for i in data:
		print(i)

	if expand[0]:
		total_w = doc_w - offset[0] * 2
		size_scale = total_w/sum(cw)#*len(cw)
		cw = [(i * size_scale) for i in cw]
		print(size_scale, 'sc')
	if expand[1]:
		total_h = doc_h - offset[1] * 2
		size_scale = total_h/sum(rh)#*len(rh)
		rh = [(i * size_scale) for i in rh]
		print(size_scale, 'sc')

	if expand[1]:
		header_size = 1
		face = pdfmetrics.getFont('Calibri-Bold').face
		h_height = (face.ascent - face.descent) / 1000 * (header_size + 0.5)
		while h_height < rh[0]/2:
			header_size += 0.5
			h_height = (face.ascent - face.descent) / 1000 * (header_size + 0.5)

		# print(face.descent, 'hh', rh[0] - (face.ascent - face.descent) / 1000 * header_size)

		body_size = 1
		face = pdfmetrics.getFont('Calibri').face
		b_height = (face.ascent - face.descent) / 1000 * (body_size + 0.5)
		while b_height < rh[1]/2.5:
			body_size += 0.5
			b_height = (face.ascent - face.descent) / 1000 * (body_size + 0.5)

		# print(face.descent, 'fd', b_height)

		ts.extend([
			('FONTSIZE', (0, 0), (0, -1), header_size),
			('FONTSIZE', (0, 0), (-1, 0), header_size),
			('FONTSIZE', (1, 1), (-1, -1), body_size),
			# ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			# ('VALIGN', (0, 0), (-1, -1), 'TOP'),
			# ('BOTTOMPADDING', (0, 0), (-1, 0), (rh[0]-h_height)/2),
			# ('BOTTOMPADDING', (0, 0), (0, -1), (cw[0]-h_height)/2),
			#
			# ('BOTTOMPADDING', (1, 1), (-1, -1), (rh[1]-b_height)/2),
		])
	# print(ts)


	#
	#
	#
	#
	# ts = [
	# 	('GRID', (0, 0), (-1, -1), 0.5, colors.black),
	# 	('SPAN', (1, 0), (2, 0)),
	# 	('SPAN', (3, 0), (4, 0)),
	# 	('SPAN', (5, 0), (6, 0)),
	# 	('SPAN', (0, 0), (0, 1)),
	# 	('ALIGN', (0, 0), (-1, 1), 'CENTER'),
	# 	('ALIGN', (0, 2), (-1, -1), 'RIGHT'),
	# 	('VALIGN', (0, 0), (-1, -2), 'MIDDLE'),
	# 	('FONT', (0, 0), (-1, 1), 'Helvetica-Bold', 7, 7),
	# 	('FONT', (0, 2), (0, -2), 'Helvetica-Bold', 7, 7),
	# 	('FONT', (1, 2), (-1, -2), 'Helvetica', 7, 7),
	# 	('FONT', (0, -1), (-1, -1), 'Helvetica-Bold', 8, 8),
	# 	('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
	# 	('BACKGROUND', (0, -1), (-1, -1), colors.black),
	# ]

	table = Table(
		data, style=ts,
		colWidths=cw, rowHeights=rh,
		cornerRadii=(5, 5, 5, 5)
	)
	table.wrapOn(canvas, 0, 0)
	table.drawOn(canvas, offset[0], doc_h-offset[1]-sum(rh))
	canvas.save()

	# elems.append(t)
	# document.build(elems)

def convert_to_pdf(input_filename, doc_w, doc_h, offset, dir_name, output_filename, append=False, colours=['#fff', '#000', '#000']):
	with open(input_filename, 'r', encoding='utf-8') as input_file:
		data = json.load(input_file)
	if append:
		canvas = Canvas(dir_name + '/img2pdf_tmp.pdf', (doc_w, doc_h))
	else:
		canvas = Canvas(output_filename, (doc_w, doc_h))

	canvas.setFillColorRGB(*hex_to_rgb(colours[0]), 1)
	canvas.rect(0, 0, doc_w, doc_h, fill=1)

	column_width = 4 * cm
	session_height = 3 * cm
	break_height = 0.5 * cm

	canvas.setFillColorRGB(*hex_to_rgb(colours[1]), 1)

	tt_height = 0
	tt_width = column_width * len(data['timetable'])
	canvas.line(offset[0], doc_h - offset[1], tt_width + column_width * 2 + offset[0], doc_h - offset[1])

	for n, i in enumerate(data['sessions']):
		if i[1]:
			tt_height += session_height
		else:
			tt_height += break_height
		canvas.line(offset[0], doc_h - offset[1] - tt_height, tt_width + ((column_width * 2) if n == len(data['sessions']) - 1 else 0) + offset[0], doc_h - offset[1] - tt_height)

	font_name = 'Calibri-Bold'
	font_size = 12

	# print(os.listdir(r'C:\Windows\Fonts'))


	for n, i in enumerate(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']):
		canvas.line(offset[0] + column_width*n, doc_h - offset[1], offset[0] + column_width*n, doc_h - offset[1] - tt_height)
		string = f'<span fontname={font_name} fontsize={font_size} color="{colours[2]}">{i}</span>'
		p = Paragraph(string, style=styles['Heading'])

		# print(p.hAlign)
		p.wrapOn(canvas, column_width, doc_h)
		p.drawOn(canvas, offset[0] + column_width * n, doc_h - offset[1] + 10)

	canvas.line(offset[0] + column_width*7, doc_h - offset[1], offset[0] + column_width*7, doc_h - offset[1] - tt_height)

	canvas.save()

	webbrowser_open('file://' + os.path.realpath(output_filename))

	# for day, day_num in enumerate(data['timetable']):
	#
	#
	#
	# for day, day_num in enumerate(data['timetable']):
	# 	for session, session_num in enumerate(day):
	# 		canvas.rect()


def find_data_file() -> str:
	"""From: https://stackoverflow.com/a/56748839"""
	if getattr(sys, 'frozen', False):
		# The application is frozen
		return os.path.dirname(os.path.realpath(sys.executable))
	else:
		# The application is not frozen
		return os.path.dirname(os.path.realpath(__file__))

convert_to_pdf_2('new_timetable.json', 29.7 * cm, 29.7 * cm * math.sqrt(2), (1.5*cm, 1.5*cm), find_data_file, 'test_timetable.pdf')