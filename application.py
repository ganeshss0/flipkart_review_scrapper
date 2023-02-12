from flask import Flask, request, jsonify, render_template
from flask_cors import cross_origin, CORS
import multiprocessing as mp
from bs4 import BeautifulSoup as BS
import requests as R
import json
import time, os

application = Flask(__name__)
CORS(application)



def get_query(baseurl: str) -> str:
    '''Getting the Query in the search field.'''
    
    if request.method == 'GET':
        query = request.args['query']
    elif request.method == 'POST':
        query = request.json['query']

    return baseurl + query
    


def get_response(url: str) -> str:
    '''Return the string containing the HTML of url.''',
    
    try:
        response = R.get(url)
    except ConnectionError:
        return 'Invalid URL'
    
    return response.text

def html_parser(markup: str) -> 'bs4.BeautifulSoup':
    '''Convert string into a Parsed HTML object.'''
    
    return BS(markup, 'html.parser')

def html_tag_finder(html_parsed: 'bs4.BeautifulSoup', tag_name: str, identifier: dict) -> 'list[bs4.BeautifulSoup]':
    '''Return a list of matching HTML tags from a Soup Object.'''
    
    return html_parsed.findAll(tag_name, identifier)

def extract_links(tags: 'list[str]', baseurl: str, tag_identifier: str) -> 'list[str]':
    '''Return a list of string after adding baseurl to a tag's identifier.'''
    
    return [baseurl + tag[tag_identifier] for tag in tags]

def get_reviews(url: str) -> None:
    '''Create a JSON file containing all the Reviews from Flipkart url.'''
    
    data = []
    
    page = get_response(url)
    parsed_page = html_parser(page)
    product_name = html_tag_finder(parsed_page, 'span', {'class':'B_NuCI'})
    comments = html_tag_finder(parsed_page, 'div', {'class': '_16PBlm'})

    for comment in comments:
        
        name = html_tag_finder(comment, 'p', {'class': '_2sc7ZR _2V5EHH'})
        rating = html_tag_finder(comment, 'div', {'class': '_3LWZlK _1BLPMq'})
        heading = html_tag_finder(comment, 'p', {'class': '_2-N8zT'})
        description = html_tag_finder(comment, 'div', {'class': 't-ZTKy'})

        try:
            data.append({
                'product' : product_name[0].text, 
                'name' : name[0].text,
                'rating' : rating[0].text,
                'heading' : heading[0].text,
                'comment' : description[0].div.div.text
                })
        except:
            pass
    
    # Dumping all the data into a File.
    with open(str(time.time_ns())+'.json', 'w') as file:
        json.dump(data, file)


def all_reviews(fileName: str = 'result.json', delete_reviews: bool = True) -> 'list[dict]':
    '''Return a list of dictonary and store a JSON file after merging all the Review JSON files.'''
    result = []
    for file in os.listdir('./'):
        if file.endswith('.json'):
            with open(file) as f:
                data = json.load(f)
            if delete_reviews:
                os.remove(file)
            result.extend(data)
    
    with open('./result.json', 'w') as file:
        json.dump(result, file)
    return result


@app.route('/')
def homepage():
    return render_template('index.html')

@app.route('/review', methods = ['GET', 'POST'])
@cross_origin()
def reviews():
    # Getting the Query
    query = get_query(baseurl = 'https://www.flipkart.com/search?q=')
    
    # Getting the response of query
    page = get_response(query)
    
    # Parsing the response into Soup Object
    parsed_page = html_parser(page)

    # Find links tag from the Parsed HTML
    boxes = html_tag_finder(parsed_page, 'a', {'class': "_1fQZEK"})
    
    # Extracting links from tags
    product_links = extract_links(boxes, 'https://www.flipkart.com', 'href')
    
    # Running all the get_reviews parallely for all the links
    with mp.Pool() as pool:
        pool.map(get_reviews, product_links)
    
    # Getting all the Reviews
    result = all_reviews()

    if request.method == 'GET':
        return render_template('result.html', reviews = result)
    elif request.method == 'POST':
        return jsonify(json.dumps(result))
        
        


        
        
if __name__ == '__main__':
    application.run(host = '0.0.0.0', port = 8000, debug = True)
