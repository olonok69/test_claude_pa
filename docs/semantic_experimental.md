# Semantic Analysys Endpoint

file https://dev.azure.com/sceven/DataDetect/_git/Detect-AI?path=/nlp/app/endpoint_semantic-exp.py

## Endpoint to integrate with Detect
Testing Notebook [here](Notebooks/new_api-semantic.ipynb)

Endpoint runing in port 5006 under directory process-tika-output. Expect only POST request. This endpoint take directly the output from tika and return a list of objects to fit into a semantic index
The endpoint receives a dictionary with 2 keys
- rindex : name of the index we are analyzing
- docs: output from TIKA

Example


```python
# in this json file we have output of 100 documents returned from TIKA
with open("test-data.json", "rb") as f:
    docs = f.read() 

d =docs.decode()
docs = json.loads(d)
data1 = json.dumps(docs).encode()

# Semantic Similarity Create Model
url = "http://localhost:5006/process-tika-output" 

try:
    r = requests.post(url, data=data1)
    print(r.json())
finally:

    pass
```
### RESPONSE

The endpoint return a list of classification objects, ready to be load into a semantic index

```python
[
  {
    "language": {
        "language": "en",
        "confidence": "1.0"
    },
    "file_name": "Attendees.docx",
    "file_type": "docx",
    "scan_id": "0b5dd85542112d8e5256e4b0d6786993d8732802c5c0246487bd7fd50ffccb98",
    "file_uri": "file:///home/demofilesystem/test_data/Large%20Control%20DataSet/Office%20Files%20and%20Documents/DOCX/Attendees.docx",
    "embedding": [
        "-0.005066571",
        "-0.02277724",
        "0.027712604",
        "-0.034904663",
        "0.025364734",
        "0.06513663",
  ...... REMOVED FOR CLARITY ............ OTHER DOCUMENTS HERE
        "-0.048861507",
        "0.022066746",
        "0.054200757",
        "-0.049059276",
        "0.0026894126"
    ]
}
]
```



## Local Version using Detect


Testing Notebook [here](Notebooks/API-semantic-endpoint.ipynb)

Endpoint runing in port 5006 under directory semantic-search-create-model. Expect only POST request. With this endpoint we create the model and with this other we can do queries semantic_search_query_model. 
The request to semantic-search-create-model is a dictionary with the following keys 

- query : query to send to Elastic search
- type : type query search_v2-->Internal Docker or outside--> External URL
- rindex : Index where to look for documents
- rindex_post : index where to post outcomes. It has to be a sentiment index
- num_docs : number of doct to post to the bulk index API
- file_types_all : bool if to use default file types or what it is included in this query
- filenames_types : list[strings] list of extensions to use case that file_types_all = True 

The request to semantic-search-query-model is a dictionary with the following keys 

- questions : the sentence or text we want to use to search documents 
- index : Index where to look for documents
- rank : number of documents to return
  

### EXAMPLE semantic-search-create-model

```python 
# query to find documents
query = {
    "pit": {

        "id": ""

    },
    "query":{
        "bool":{
         "must":[
            {
               "exists":{
                  "field":"content"
               }
            },
            {
               "bool":{
                  "should":[
                     {
                        "term":{
                           "file_type":"docx"
                        }
                     },
                     {
                        "term":{
                           "file_type":"doc"
                        }
                     },
                       {
                        "term":{
                           "file_type":"pdf"
                        }
                     }
                  ]
                    
               }
            },
            {
               "range":{
                  "fs.size":{
                     "gt":100,
                     "lt":5000000000
                  }
               }
            }
         ]
      }
   },
    "from": 0,
    "size": 10000,
    "sort": [
        {
            "fs.size": {
                "order": "asc"
            }
        }
    ]
}

# create request
data = {}
data['query'] = query
data['type'] = "search_v2" # ingest or search
data['index'] = "control_data_set_5_resumes_demo-doc" # control_data_set_5_resumes_demo-doc  # enron_data_set_demo_1-doc
data['index_post'] = "control_data_set_5_resumes_demo-doc-semantic"
data['num_docs'] = 5
data['file_types_all'] = 'False'
data['filenames_types']= ["doc", "docx", "pdf"]

# encode dict to bytes
data1 = json.dumps(data).encode()

# Send request to API

url = "http://localhost:5006/semantic-search-create-model" 

try:
    r = requests.post(url, data=data1)
    print(r.text)
finally:

    pass
```

### RESPONSE

```python
{'status': 'SUCCESS',
 'Number doc read ': '165',
 'Total Time': '0:05:27.740140'}
```

### Document posted to the Index

```python
{
    "language": {
        "language": "en",
        "confidence": "1.0"
    },
    "file_name": "VOD-SVOD-EST-PayTV Content Protection Schedule V1.doc",
    "file_type": "doc",
    "scan_id": "1d31c20604334c6f2ea22a73df03d13b2ca9e1cdaa797e0a9605bd73c3a7418c",
    "file_uri": "file:///home/demofilesystem/test_data/ControlDataSet%20-%205%20Random%20Resumes/Control%20Data%20Set/Email%20Files/PST%20Files/Deals.pst",
    "embedding": [
        "-0.011919399",
        "-0.028776364",
    ]
}

Note: the embedding only shows two positions , but in fact contains 768
```

### EXAMPLE semantic-search-query-model

```python
data = {}

data['questions'] = "university job history experience school skill institute education professional training certifications"
data['index'] = "control_data_set_5_resumes_demo-doc" # 
data['rank'] =  "5"

data2 = json.dumps(data).encode()

url = "http://localhost:5006/semantic-search-query-model" 

try:
    r = requests.post(url, data=data2)
    print(r.text)
finally:

    pass

```

### Output

```python
{'scan_id': '0192699d1d7ef8374eecf4c069bfa0b8d81442afaef4d3713cfca8ffe95ddf11',
 'score': '0.16870403992366106',
 'text': '  MARK KORRES\n\n  9561 Arrowhead Dr. Hickory Hills, IL 60457 • (773) 297-3450 • mark@markkorres.com\n\n  Page 1 of 2\n\n  SUMMARY\n\n  An IT Service Management, ITIL certified technical professional with a breadth of experience teaching, designing,\n\n  implementing, and improving IT operations, processes, and frameworks. A leader that emphasizes team success\n\n  and inspires desired outcomes and increased performance with a cross-industry designation and deep experience in\n\n  Life Sciences, Healthcare, Energy, and Insurance/Financial industries for Fortune 500 and large companies.\n\n  Extensive experience leading IT transformations, implementing major initiatives, designing processes, creating\n\n  proposals, responding to RFPs/RFIs, mentoring counselees, and managing infrastructure teams. Recent\n\n  accomplishments include a Continuous Service Improvement implementation that produced a 60% decrease in\n\n  Priority 1 incidents and an 80% improvement in average resolution time and the creation of a three-year roadmap to\n\n  save the client $4.6M annually in addition to $6M in qualitative benefits. Open to travel.\n\n  EXPERIENCE\n\n  ➢ ITIL/ITSM Expertise\n\n  • Led redesign of core ITSM processes including workshops, interviews. Created process documentation, training\n\n  guides and completed train the trainer sessions. Redesigned meta-data for the current and future ITSM tools and\n\n  documented pre-requisites for recommended ITSM tool.\n\n  • Designed and implemented an ITSM governance structure to address ITSM improvements and prioritize\n\n  projects. Mentored client process owners to create improvement projects and charters. Identified 60+ initiatives\n\n  and 20+ projects to support the ITSM Strategy and implement it the over three years.\n\n  • Responsible for regional and global service implementation across 3 regions for trading applications using ITIL\n\n  standards including governance and a standardized CMDB.\n\n  • Developed Service Catalogs, Service Request processes and roadmaps to implement with SLAs and KPIs.\n\n  • Served as IT Service Management Liaison for all Acquisitions and Divestitures.\n\n  ➢ Service Improvement / Application Rationalization / IT Operating Model\n\n  • Led ITSM Tool assessment that included 500+ IT Tools and 380K+ users resulting in $4.6M annual savings.\n\n  • Recommended transition from a legacy tool to ServiceNow to save the organization $1M+ yearly.\n\n  • Assessed current IT Operating Model, including value of major tools and applications for CIO and CFO\n\n  decisions. Developed a plan to reduce IT spend and target a 3% IT cost and a go-forward IT Operating Model\n\n  with a $13M reduction in IT cost. Produced a 14-month roadmap to implement projects and transform to new\n\n  operating model.\n\n  • Lead Strategy to convert from Remedy to ServiceNow, including the definition of Service Catalog offerings,\n\n  data elements and workflow. Coordinated Service Management processes with ServiceNow workflows and\n\n  implemented Incident, Change, Problem, Release, Configuration, Asset, Knowledge, Event, SCM and SLM.\n\n  • Developed and Managed the “Availability is Job #1” Program which resulted in: reduction of P1 Incident Count\n\n  by 60% and P1 Duration by 80%, eliminated outages during planned Infrastructure Maintenance, eliminated\n\n  authentication P1 incidents, Reduced the number P1s due to Change, and reduced the backlog of open Root\n\n  Cause Analysis tickets by 90%.\n\n  ➢ Proposals / RFPs\n\n  • Led team of 20+ to create 70+ page proposal and several supporting presentations to win ServiceNow\n\n  implementation for large financial client.\n\n  • Led large and small teams to create multiple winning proposals for Fortune 500 Life Sciences/Healthcare,\n\n  Energy, and Insurance/Financial clients.\n\n  • RFP Response team member developing and submitting RFP follow-up and clarifying questions.\n\n  • Presentation team member for multiple proposals\n\n  ➢ Assessments / Improvement Roadmaps\n\n  • Led multiple ITSM Maturity Assessments and helped develop and ITSM Maturity Assessment Tool.\n\n  • Led ITSM and PPM Assessments identifying pain points, creating future states, and performing gap analysis.\n\n  • Developed prioritization tools to help clients focus on quick wins and long-term benefits.\n\n  • Created multiple-year roadmaps plotting project sequence and identifying key dependencies and risks.\n\n  MARK KORRES\n\n  9561 Arrowhead Dr. Hickory Hills, IL 60457 • (773) 297-3450 • mark@markkorres.com\n\n  Page 2 of 2\n\n  JOB HISTORY\n\n  ➢ Deloitte Consulting * 7/17 – Present\n\n  Manager – ServiceNow, ITSM and Service Management Practice\n\n  Led engagements for multiple, national, and global Fortune 500 clients (Life Sciences/Healthcare, Financial and\n\n  Energy) to perform ITSM/ITIL/Maturity assessments, gap analysis, and create roadmaps for improvement and\n\n  implementation. Led teams to create Sales Proposals and RFP responses. Served as practice lead for interviewing\n\n  and hiring new resources. Mentored multiple counselees and assisted with career development and firm success.\n\n  ➢ TEK Systems * 8/12 – 7/17\n\n  Managing Consultant – ITIL / IT Service Management\n\n  Served as ITIL and ITSM Subject Matter Expert and Manager. Led several ITSM, ITIL and Service Improvement\n\n  engagements for multiple Insurance/Financial Chicago area companies.\n\n  ➢ The ACE Group * 7/11 – 8/12\n\n  Service Manager, Combined Insurance, North America\n\n  Implemented a Service Improvement Program to streamline service processes, eliminate impactful outages and\n\n  increase overall availability. Instituted a Communication Policy for all desktop distributions reducing the number of\n\n  secondary distributions and outages due to lack of application access.\n\n  ➢ TEK Systems * 4/10 – 7/11\n\n  Managing Consultant – ITIL / IT Service Management\n\n  Served as ITIL and ITSM Subject Matter Expert and Manager. Led several ITSM, ITIL and Service Improvement\n\n  engagements for multiple Insurance/Financial Chicago area companies.\n\n  ➢ Fruition Partners * 8/07 – 4/10\n\n  Consultant – ITIL / IT Service Management / ServiceNow\n\n  Led engagements for multiple, national, and global clients (Travel, Financial and Energy) to perform\n\n  ITSM/ITIL/Maturity assessments, gap analysis, and create roadmaps for improvement and implementation. Led\n\n  teams to create Sales Proposals and RFP responses. Taught ITIL certification classes. Team member selected to\n\n  review first ServiceNow Administration Guide.\n\n  ➢ Northern Trust * 2/03 – 8/07\n\n  Vice-President, Certification/Deployment Coordinator\n\n  Designed and Implemented new certification and release/deployment process for all desktop applications and\n\n  managed 800+ applications for 14K+ endpoints world-wide. Planned 4K+ deployments/certifications/releases and\n\n  became integral part of Initial Review and PMO processes. Designed and Implemented application/distribution\n\n  tracking database and Deployment Tracking Database to record necessary deployment information\n\n  EDUCATION / CERTIFICATIONS\n\n  • ServiceNow Certified Implementation Specialist\n\n  • ITIL V3 Foundations Certified – Exin U.S.A.\n\n  • Ed Jones "Train-the-Trainer" seminars\n\n  • Illinois Institute of Technology – CS / EE\n\n  • Illinois State Scholar - National Honor Society\n\n  • Who\'s Who in American High School Students\n\n  GENERAL ASSETS\n\n  * ITIL, Cobit, IT Service Management\n\n  * ServiceNow (ITSM, ITOM, ITBM, CSDM), Remedy, IBM Maximo, LANDesk, Track-IT, Magic Helpdesk\n\n  * Teams, SharePoint, InfoPath, Hyperion, MS Access, HTML, Java Scripts, Citrix\n\n  * Windows, Microsoft Office, MS Project, Visio, Exchange, Lotus Notes, Google Apps, QuickBooks, Timberline\n\n  * Familiar with Novell, UNIX, Linux, MS SQL, Sybase, Oracle, Paradox, CGI, Perl, Cold Fusion, Visual Basic\n\n  * 20 + Years of Management, Training, and Customer Service experience\n\n  * Excellent Organizational, Interpersonal, Training and Developmental Skills\n\n  * A generally nice guy\n\n  FULL CV AND REFERENCES AVAILABLE UPON REQUEST\n'}
```

### Other testing Endpoints

We have another endpoints to compare two documents versus cosine similarity and levenshtein distance --> /api/compare_files

### Example /api/compare-files

```python

files_path = "D:\\files\\nlp6"
file1 ="4SD.ThreeStoogesbw.OL.txt.txt"
file2 = "612CCORSONY2410.txt.txt"
file3 = "14070413.fs.txt"
# open files 
fin = open(os.path.join(files_path, file1), 'rb')
minuta = open(os.path.join(files_path, file2), 'rb')
data1=fin.read()
data2=minuta.read()
data3 = open(os.path.join(files_path, file3), 'rb').read()
payload_dict={'file1': data2, 'file2': data3}


url = "http://localhost:5006/api/compare-files" 

try:
    r = requests.post(url, data=payload_dict)
    print(eval(r.text))
finally:
    pass

```

### Output

```python
{
  "status": "SUCCESS",
  "results": {
    "Cosine-Similarity": 0.8714479207992554,
    "Simple Ratio": 16,
    "Partial Ratio": 29,
    "Token Sort Ratio": 15,
    "Token Set Ratio": 16,
    "Partial Token Sort Ratio": 40
  }
}
```

