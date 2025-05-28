# OCR Endpoint

file https://dev.azure.com/sceven/DataDetect/_git/Detect-AI/pullrequest/1114?_a=files


## Endpoint to integrate with Detect


Endpoint runing in port 5003 under directory process. Expect only POST request. This endpoint take a json object which contains two attributes. The main attribute , documents is a list of json objects containing the metadata and data , tika outout stile (same attributes) and process them. Per each file we have in obj.get("source").get("content") the base64 version of the file we want to pass trough OCR and extract data.
There is another attribute  "cypher", which by default is False if nothing comes in the Detect request, which contains an encrypted version of the extracted text

Accepted extensions:
['jpeg', 'jpg', 'tiff', 'png', 'tif', 'gif', 'pdf', 'doc', 'docx', 'ppt', 'pptx', 'htm', 'html', 'bmp', 'rtf', 'odt']

Example
{
    "id": "c5613d504ddd3367d15ba6ab9245c062018fa21135aec4d452f9b3e4d88c441b",
            "index": "large_control_dataset-doc",
            "source": {
                "content": "base64 content",
                "fs": {
                    "uri": "file:///home/demofilesystem/test_data/Large%20Control%20DataSet/Office%20Files%20and%20Documents/DOC/senior_python_developer_nlplogix1_sm.jpg"
                },
                "file_name": "senior_python_developer_nlplogix1_sm.jpg",
                "file_type": "jpg",
                "embedded_depth": 0
            }
}






```python
example Json to be send to endpoint

data = {}
data['documents'] = list_docs # list of json objects containing documents from Detect
data['cypher'] = 1

data2 = json.dumps(data1).encode()
url = "http://localhost:5003/process" 

try:
    r = requests.post(url, data=data2)
    print(r.json())
finally:

    pass


```
OUTPUT example
```python
{
    "status": {
        "code": 200,
        "message": "Success"
    },
    "data": [
        {
            "id": "7587bcb2-4ea6-4a64-a426-040b40bf414b",
            "index": "large_control_dataset-doc",
            "source": {
                "content": "Senior Python Developer\nNLP Logix Jacksonville, FL, USA\n\nBenefits Offered\n\n401K, Dental, Life, Medical, Vision\nEmployment Type\n\nFull-Time\n\nWhy Work Here?\n“Working for NLP LOGIX will give you a unique opportunity to learn and play an integral role building new and\n\nexciting products.”\n\nSeeking Senior Software Developer for a cutting-edge computer vision product company,\nScribe Fusion (www.scribefusion.com), a division of NLP Logix. The ideal candidate will be\n\ncomfortable working with multiple technology stacks and operating systems. Responsibilities\n\ninclude developing both back-end and front-end components, however the focus will be\nprimarily on back-end components. Much of the development activities will be focused on new\n\nfeatures and components, however existing product installations need to be maintained as\nwell. We encourage a collaborative, ego-free environment with a focus on producing amazing\n\nproducts and exceeding customer expectations.\nResponsibilities:\n\no Develop and interact with computer vision models.\n\nDevelop Docker components to be consumed by workflow-based applications.\n\ne Work with clients on integrations with existing systems.\n\ne Develop GUI applications, surfacing results of backend processes.\n\nRequirements (Must-Haves):\no 5+ years of software development experience\n\ne Multiple years’ experience with Python is strongly preferred\n\n Experience working with one or more major relational database technology (Oracle,\nSQL\n\nServer, MySQL, PostgreSQL)\no Comfortable working in both Windows and Linux based environments\ne Ability to work effectively with colleagues\n\ne Ability to work with minimal supervision\n",
                "fs": {
                    "uri": "file:///home/demofilesystem/test_data/Large%20Control%20DataSet/Office%20Files%20and%20Documents/DOC/senior_python_developer_nlplogix1_sm.jpg"
                },
                "file_name": "senior_python_developer_nlplogix1_sm.jpg",
                "file_type": "jpg",
                "embedded_depth": 0
            },
            "crypto": "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"
        }
    ],
    "error": "",
    "number_documents_treated": 1,
    "number_documents_non_treated": 0,
    "list_id_not_treated": []
}


```