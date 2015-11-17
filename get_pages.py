
'''

Get a listing of 
Static files and such are generated.
    Hosted on an LTI server.
Loader script is generated, based on the desired configuration
    For each page, a set of component assignments and one "real" assignment are generated.
    The URL for each assignment has a parameter describing each of the other assignments.
    The assignment is loaded into the course instance
When an exercise on a page is completed
    It looks at its parameters for a 
    Posts the updated grade to the proper assignment
'''

import requests
import os
import shutil
import traceback
from zipfile import ZipFile
from StringIO import StringIO

import json

with open('secrets.json', 'r') as input:
    secrets = json.load(input)

try:
    import progressbar
except ImportError:
    print "Not using progressbar"
    progressbar = None

def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)
    return f

ACCESS_TOKEN = secrets.get("canvas-token", "ERROR!")
def get(command, data):
    data['access_token'] = ACCESS_TOKEN
    return requests.get('https://canvas.instructure.com/api/v1/'+command, data=data).json()
def post(command, data):
    data['access_token'] = ACCESS_TOKEN
    return requests.post('https://canvas.instructure.com/api/v1/'+command, data=data).json()    
def delete(command, data):
    data['access_token'] = ACCESS_TOKEN
    return requests.delete('https://canvas.instructure.com/api/v1/'+command, data=data).json()    
def put(command, data):
    data['access_token'] = ACCESS_TOKEN
    return requests.put('https://canvas.instructure.com/api/v1/'+command, data=data).json()    

ASSIGNMENT = "QuickSort"
COURSE = 946043
NUMBER_OF_SUBASSIGNMENTS = 5

print "Getting pages"
pages = get('courses/{course}/pages'.format(course=COURSE), {})

if pages > 1 and progressbar is not None:
    pbar = progressbar.ProgressBar(widgets=[progressbar.Bar('>'),
       ' ', progressbar.Percentage(), ' ', progressbar.ETA(), ' ', progressbar.FileTransferSpeed()]).start()
else:
    pbar = list

for page in pbar(pages):
    url = page['url']
    updated_at = page["updated_at"]
    # TODO: Some logic to check if the page has changed
    page_content = get('courses/{course}/pages/{url}'.format(course=COURSE, url=url), {})
    body = page_content['body']
    title = page_content['title']
    published = page_content['published']
    filename= 'courses/{code}/{url}.html'.format(code=COURSE, url=url)
    ensure_dir(filename)
    with open(filename, 'w') as output:
        output.write(body.encode('utf8'))

'''
print "Deleting existing assignments"
for an_id in ids:
    print "\t", an_id
    delete('courses/{course}/assignments/{assignment}'.format(course=COURSE, assignment=an_id), {})
    
print "Adding {count} new assignments".format(count=NUMBER_OF_SUBASSIGNMENTS)
new_assignments = []
for index in xrange(1, NUMBER_OF_SUBASSIGNMENTS+1):
    new = post('courses/{course}/assignments'.format(course=COURSE), {
                        'assignment[name]': "{assignment} #{index}".format(assignment=ASSIGNMENT, index=index),
                        'assignment[external_tool_tag_attributes][new_tab]': False,
                        'assignment[submission_types]': 'external_tool'})
                        
    print "\t", new['id']
    new_assignments.append(new)
new_ids = [assignment['id'] for assignment in new_assignments]
joined_ids = ','.join(map(str, new_ids))

print "Updating each assignments settings to reference each other."
for an_id in new_ids:
    result = put('courses/{course}/assignments/{assignment}'.format(course=COURSE, assignment=an_id), {
        'assignment[external_tool_tag_attributes][url]': "http://example.com?id={assignment}&assignments={ids}".format(assignment=ASSIGNMENT, ids=joined_ids),
        #},
        'assignment[description]': "I have been updated!"
    })
    print "\t", an_id
    
print "Reporting out the new assignment URLs!"
assignments = get('courses/{course}/assignments'.format(course=COURSE), {})
for assignment in assignments:
    print "\t", assignment["id"], "=>", assignment['external_tool_tag_attributes']['url']
'''