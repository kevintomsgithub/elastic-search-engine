"""
Description: This is a program to make the indexing files for elastic search.
Created By: Kevin Toms
"""

import os
import json
import argparse
from nltk.corpus import stopwords

# Argument Parser
parser = argparse.ArgumentParser('document file name')
parser.add_argument('file_name', help="Docuemnt which contains the Question Answer JSON", type=str)
args = parser.parse_args()

# Base directory for the creation of files
base_dir = 'search_index'
# Create folder if not exist
if not os.path.exists(base_dir):
    os.mkdir(base_dir)

# Get the document file name from arguments
raw_doc_file_name = args.file_name
# Document keys for question and answer
question_key = 'question'
answer_key = 'answer'
# File name for saving preprocessed documents
processed_data_file_name = os.path.join(base_dir, 'documents.js')
processed_data_js_variable_name = 'docIndex = '
# File name for saving inverted indexed document
inverted_JSON_file_name = os.path.join(base_dir, 'inverted_indexing.js')
inverted_JSON_js_variable_name = 'invertedIndex = '
# File name for saving prefix hash table
prefix_hash_table_file_name = os.path.join(base_dir, 'prefix_hash.js')
prefix_hash_js_variable_name = 'data = '


# Tree Node withing a trie
class TreeNode:
    def __init__(self, val):
        self.val = val
        self.children = {}
        self.end = False
        self.suggestion_list = []
        self.base = ''
        
# Trie data structure Declaration
class Trie:
    def __init__(self):
        self.root = TreeNode('')
        
    def insert(self, word):
        root = self.root
        for index, letter in enumerate(word):
            if letter not in root.children:
                root.children[letter] = TreeNode(letter)
            root = root.children[letter]
        if index == len(word)-1: root.end = True


def preprocess_raw_data(raw_json):
    """
    Description: This function helps to process the raw JSON data into the structure for indexing
    Parameters:
        raw_json: raw JSON data
    return: processed data
    """
    # Variable to hold the processed data
    data = []
    # Lambda function to remove all stopwords from a sentence
    get_word_tokens = lambda words: [word.lower() for word in words if word.isalpha() and word.lower() not in stopwords.words('english')]
    # Iterate throught the JSON and remove to form a dictonary with processed data
    for index, i in enumerate(raw_json):
        # Remove all stopwords from the question
        qst_words = get_word_tokens(i[question_key].split(' '))
        # Remove all stopwords from the answer
        ans_words = get_word_tokens(i[answer_key].split(' '))
        # Total keywords from both question and answer
        keywords = qst_words + ans_words
        # Processed data dictonary
        data.append({
            'index': index,
            'question': i['question'],
            'answer': i['answer'],
            'keywords': keywords
        })
    return data


def inverted_indexing(data):
    """
    Description: This function helps in invert indexing the processed data
    Parameters:
        data: preprocessed dictonary
    return: inverted index dictonary
    """
    # Keyword mapping to document index
    inverted_json = {}
    # Iterate through the processed data and form the inverted index
    for index, item in enumerate(data):
        # Iterate throught the keywords and form the inverted index
        for keyword in item['keywords']:
            # Logic for entering the new and existing words
            if keyword in inverted_json:
                inverted_json[keyword]['freq'] += 1
                inverted_json[keyword]['doc'].append(index)
            else:
                inverted_json[keyword] = {
                    'freq': 1,
                    'doc': [index]
                }
    # Remove all duplicate document index values
    for key, val in inverted_json.items():
        val['doc'] = list(set(val['doc']))
    return inverted_json


def make_prefix_hash_table(inverted_json):
    """
    Description: This function helps to make the prefix hash table
    Parameters:
        inverted_json: inverted indexed JSON
    return: prefix hash table
    """
    # Prefix hash table declaration
    prefix_hash_table = {}
    # Get all words in inverted index dictonary
    inverted_json_keys = list(inverted_json.keys())
    # Root node of Trie data structure
    trie_root_node = Trie()
    # Make a trie with all the words in the document
    for word in inverted_json_keys:
        trie_root_node.insert(word)
    # Get all the possible words/suggestions from the trie
    def dfs(root, curr_word=''):
        root.base = curr_word
        prefix_hash_table[root.base] = root.suggestion_list
        if root.end: 
            root.suggestion_list.append(curr_word)
            return [curr_word]
        
        for val, node in root.children.items():
            to_return = dfs(node, curr_word+node.val)
            root.suggestion_list += to_return
        
        return root.suggestion_list
    # Call to make the populate the prefix hash table  
    dfs(trie_root_node.root)
    # Remove the null entry
    prefix_hash_table.pop('', None)
    return prefix_hash_table


# Read raw data JSON 
with open(raw_doc_file_name) as f:
    raw_json = json.load(f)

# Pre-process the raw json
data = preprocess_raw_data(raw_json)

# Make the inverted indexed dictonary
inverted_json = inverted_indexing(data)

# Make the prefix hash table from inverted indexed JSON
prefix_hash_table = make_prefix_hash_table(inverted_json)

# Save the preprocessed data
with open(processed_data_file_name, 'w') as w:
    # Variable name used in JavaScript
    w.write(processed_data_js_variable_name)
    json.dump(data, w)

# Save the inverted indexed data
with open(inverted_JSON_file_name, 'w') as w:
    # Variable name used in JavaScript
    w.write(inverted_JSON_js_variable_name)
    json.dump(inverted_json, w)

# Save the prefix hash table
with open(prefix_hash_table_file_name, 'w') as w:
    # Variable name used in JavaScript
    w.write(prefix_hash_js_variable_name)
    json.dump(prefix_hash_table, w)