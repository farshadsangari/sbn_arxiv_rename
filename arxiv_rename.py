`'''
	this script renames the papers downloaded from arxiv.org
	using the naming format defined by the 'name_format' function

	see the complete documentation at https://github.com/sukiboo/sbn_arxiv_rename
'''

import os
import arxiv
import shutil
import requests
from pdfrw import PdfReader, PdfWriter


'''
	user-selected options:
		- naming_convention
		- paper_update
		- dir_path
'''
# select the paper naming convention:
#	1 -- 'FirstAuthor_Year_Title.pdf' (default option)
#	2 -- 'Authors - Title (Year).pdf' (authors truncated to 'et al.' if more than 2)
#	3 -- custom format, configured below by modifying the 'name_format_3' function
#			(defaults to 'Authors - Title.pdf' with no author list truncation)
naming_convention = 1

# enable/disable paper updates:
#	if True script will download the latest version of the paper from arxiv.org
#	if False script will just rename the paper and keep it the current version
paper_update = True

# select the destination directory for the renamed papers
dir_path = './arxiv_papers/'


''' define paper naming formats '''
# define 'FirstAuthor_Year_Title' naming format
def name_format_1(authors, title, year):
	authors = paper['authors'][0].split(' ')[-1]
	title = title.replace(':', '').replace(',', '')
	pdf_name = authors + ' ' + year + ' ' + title + '.pdf'
	pdf_name = pdf_name.replace(' ', '_')
	return pdf_name

# define 'Authors - Title (Year)' naming format
def name_format_2(authors, title, year):
	if len(authors) <= 2:
		authors = ', '.join(map(lambda s: s.split(' ')[-1], authors))
	else:
		authors = authors[0].split(' ')[-1] + ' et al.'
	pdf_name = authors + ' - ' + title + ' (' + year + ').pdf'
	return pdf_name

# define custom naming format
def name_format_3(authors, title, year):
	authors = ', '.join(authors)
	pdf_name = authors + ' - ' + title + '.pdf'
	return pdf_name

# select the naming format to use in the script
if naming_convention == 1:
	name_format = name_format_1
elif naming_convention == 2:
	name_format = name_format_2
else:
	name_format = name_format_3


''' initial preparations '''
# get the list of pdf files in the current directory
pdfs = [f for f in next(os.walk(os.getcwd()))[2] if f.endswith('.pdf')]
if len(pdfs) > 0:
	# create 'arxiv_papers' directory if it does not exist
	if not os.path.exists(dir_path):
		os.makedirs(dir_path)
	# check the internet connection
	try:
		requests.head('https://arxiv.org/')
	except requests.ConnectionError:
		logging.error('failed to connect to arxiv.org')
		raise SystemExit(0)
else:
	print('there are no pdf files in the current directory...')
	raise SystemExit(0)


''' rename the papers '''
# iterate over all pdf files
for pdf in pdfs:

	# try to retrieve the paper from arxiv
	try:
		# check if arxiv_id is in metadata
		metadata = PdfReader(pdf).Info
		if '/arxiv_id' in metadata and '/updated' in metadata:
			paper = arxiv.query(id_list=[metadata['/arxiv_id'][1:-1]])[0]
			updated = metadata['/updated'][1:-1]
		# else assume that arxiv_id is in the name
		else:
			paper = arxiv.query(id_list=[pdf[:-4].split('v')[0]])[0]
			updated = ''

		# extract paper's metadata
		# authors list
		authors = paper['authors']
		# title of the paper
		title = ' '.join(paper['title'].split())
		# year of original submission
		year = str(paper['published_parsed'].tm_year)
		# arxiv identifier
		arxiv_id = paper['id'].split('/')[-1].split('v')[0]

		# generate the new name for the paper
		pdf_name = name_format(authors, title, year)
		# download/rename the paper and update metadata
		if paper_update and updated != paper['updated']:
			# download the latest version of the paper
			open(dir_path + pdf_name, 'wb').write(requests.get(paper['pdf_url']).content)
			updated = paper['updated']
			print('{:s} -- the latest version is downloaded from arxiv.org'.format(pdf))
		else:
			# copy and rename the paper
			os.rename(shutil.copy2(pdf, dir_path), dir_path + pdf_name)
			print('{:s} -- metadata is obtained from arxiv.org'.format(pdf))

		# read and update the metadata
		full_metadata = PdfReader(dir_path + pdf_name)
		# add '/arxiv_id' and '/updated' to metadata
		full_metadata.Info.arxiv_id = arxiv_id
		full_metadata.Info.updated = updated
		# save pdf with updated metadata
		PdfWriter(dir_path + pdf_name, trailer=full_metadata).write()

	# otherwise copy the paper without changes
	except:
		shutil.copy2(pdf, dir_path)
		print('{:s} -- no relevant metadata is obtained'.format(pdf))

