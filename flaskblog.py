from flask import Flask, request, render_template
import system # this will be your file name; minus the `.py`
from itertools import groupby
import os
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import gensim.downloader as api
import requests
import time
import json
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from urllib.request import urlopen, urlretrieve
from bs4 import BeautifulSoup as soup 
import csv
import pandas as pd
import markovify
import re
import spacy

app = Flask(__name__)

@app.route('/')
def my_form():
	return render_template('home.html')

@app.route('/', methods=['POST'])
def my_form_post():
	text = request.form['text']
	processed_text = text.lower()
	keywords = system.segment(processed_text)[0]
	keywords.append(processed_text) 
	tags = keywords
	it = 0
	sid = SentimentIntensityAnalyzer()
	for keyword in keywords:
		url='https://www.instagram.com/web/search/topsearch/?context=blended&query={0}&__a=1'.format(keyword)
		r=requests.get(url)
		data=json.loads(r.text)
		hashtags=[data['hashtags'][i]['hashtag']['name'] for i in range(len(data['hashtags']))]
		print(hashtags)
		time.sleep(1)
		sentence_1 = 'body shaming' #improve here 
		sentence_1_avg_vector = system.sentence_vec(sentence_1.split(), emb_size=300)
		for tag in hashtags:
			f = 0 
			y = system.segment(tag)[0]
			segtag = y
			sentence_2 = ' '.join(y)
	#         if len(x) < len(y):
	#             #print(' '.join(x))
	#             sentence_2 = ' '.join(x)
	#             segtag = x
	#         else:
	#             #print(' '.join(y))
			#print(keyword)
			x = system.segment(sentence_1)[0]
			sentence_2_avg_vector = system.sentence_vec(sentence_2.split(), emb_size=300)
			sen1_sen2_similarity =  cosine_similarity(sentence_1_avg_vector.reshape(1,-1),sentence_2_avg_vector.reshape(1,-1))
			if(sen1_sen2_similarity[0][0] > 0.5):
				#print(sentence_2)
				for t in segtag:
					ss = sid.polarity_scores(t)
					if ss['neg'] > ss['pos'] and t not in x:
						newtag = ''.join(sentence_2.split(' '))
	#                     if f:
	#                         print(newtag)
						if newtag not in tags:
							tags.append(newtag)
		it += 1
		if it == 10:
			break #adjust this for more tags. 
	with open('data.csv', 'w') as csvfile:
		title = ['id', 'text', 'text_hashtag','comment_1','comment_2','comment_3','comment_4','comment_5']
		csvwriter = csv.writer(csvfile)
		csvwriter.writerow(title)
		for key in range(0,len(keywords)):
			keyword = keywords[key]
			posts = []
			end_cursor = '' 
			tag = keyword 
			page_count = 5
			print(tag)
			for i in range(page_count):
	#             print(tag)
				try:
					url = "https://www.instagram.com/explore/tags/{0}/?__a=1&max_id={1}".format(tag, end_cursor)
	#             print(i)
				except:
					break
				time.sleep(2)
				r = requests.get(url)
				data = json.loads(r.text)
				end_cursor = data['graphql']['hashtag']['edge_hashtag_to_media']['page_info']['end_cursor'] # value for the next page
				edges = data['graphql']['hashtag']['edge_hashtag_to_media']['edges'] # list with posts

				for item in edges:
					if(item['node']['shortcode'] not in posts):
						posts.append(item['node']['shortcode'])
				 # insurance to not reach a time limit
			print(len(posts))
			DIR = 'pictures'
			if not os.path.isdir(DIR):
				os.makedirs(DIR) 
			for i in range(len(posts)):
				post = posts[i]
				post_url = "https://www.instagram.com/p/"+str(post)+"/"
				#print(url)
				try:
					postClient = urlopen(post_url)
					post_html = postClient.read()
					time.sleep(1)
					post_html = post_html.decode("utf8")
					postClient.close()
					post_soup = soup(post_html, "html.parser")
					post_script = post_soup.find('script', text=lambda t: t.startswith('window._sharedData'))
					post_json = post_script.text.split(' = ', 1)[1].rstrip(';')
					post_data = json.loads(post_json)
					#print(post_data)
					try:
						text_data = post_data['entry_data']['PostPage'][0]['graphql']['shortcode_media']['edge_media_to_caption']['edges'][0]['node']['text']
					except:
						text_data = ""
					text_data = text_data.split('#')
					hashtags = ""
					image_url = post_data['entry_data']['PostPage'][0]['graphql']['shortcode_media']['display_url']
					for j in range(len(text_data)):
						if(j > 0):
							tmp = text_data[j]
							tmp = tmp.split(' ') 
							if(len(tmp) <= 2):
								hashtags += str(" ") + text_data[j]                 
							else: 
								text_data[0] += str(' ') + text_data[j]
					text = text_data[0]
					try: 
						#comment_count = post_data['entry_data']['PostPage'][0]['graphql']['shortcode_media']['edge_media_to_parent_comment']['count']
						comment_list = post_data['entry_data']['PostPage'][0]['graphql']['shortcode_media']['edge_media_to_parent_comment']['edges']
						comment_count = len(comment_list)
					except:
						comment_count = 0 
						comment_list = []
					#print(comment_list[0]['node']['text'])
					#print(comment_count)
					comments = ['N/A','N/A','N/A','N/A','N/A']
					for j in range(min(comment_count, 5)):
						#tmp = comment_list[i]['node']['text'].split('#')
						#tmp = ' '.join(tmp)
						comments[j] = comment_list[j]['node']['text']
						#comments[i] = tmp    
	#                 print(text) #add try and except for no text -> do later. 
	#                 print(hashtags)
	#                 print(comments)
					it += 1
					image_DIR = os.path.join(DIR, str(it) + ".jpg")
					try:
						urlretrieve(str(image_url),image_DIR)
					except:
						print('no image for this post : {0}'.format(post_url))
					image_id = post
					fields = [str(it), text, hashtags] 
					for j in comments:
						fields.append(j)
					# creating a csv writer object 
					csvwriter.writerow(fields)
					print("post written id - {0}, img dir - {1}".format(it, image_DIR))
				except:
					print("url couldn't be read : {0}".format(str(post_url)))
	df = pd.read_csv('data.csv')
	df = df['text_hashtag']
	text_list = []
	for i in df:
		print(i)
		try:
			ls = i.split(' ')
			for word in ls:
				word = word.lower()
				if(word != ''):
		#             print(" ".join(system.segment(word)[0]))
					w = " ".join(system.segment(word)[0])
					if w not in text_list:
						text_list.append(w)
					if(w == '  a r e n t h o o d'):
						print(word)
		except:
			yolo = 1
#         print('no hashtags in this post')
#     break
	for tag in tags:
		w = " ".join(system.segment(word)[0])
		if w not in text_list:
			text_list.append(w)
	txt_file = 'training_hastags.txt'
	with open(txt_file, "w") as my_output_file:
		my_output_file.write("#1\n")
		my_output_file.write("double({},{})\n".format(len(text_list), 2))
		for line in text_list:
			my_output_file.write(" " + line + "\n")
		print('File Successfully written.')
	nlp = spacy.load("en")

	class POSifiedText(markovify.NewlineText):
		def word_split(self, sentence):
			return ["::".join((word.orth_, word.pos_)) for word in nlp(sentence)]

		def word_join(self, words):
			sentence = " ".join(word.split("::")[0] for word in words)
			return sentence
	with open('training_hastags.txt') as f:
		text = f.read()
	text_model = POSifiedText(text)
	syntags = []
	for i in range(50):
		x = text_model.make_short_sentence(30)
		if(x != None and x not in text_list):
			syntags.append(x)
	return render_template('list.html', your_list= syntags)

# @app.route('/')
# def dynamic_page():
#     return your_module.your_function_in_the_module()

if __name__ == '__main__':
	app.run(debug=True)
