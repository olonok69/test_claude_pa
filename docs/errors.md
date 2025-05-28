# Logging document errors

On the object returned for each endpoint we have the following keys:
- status = Dictionary with status code and message. Ex. {'code': 200, 'message': 'Success'} 
- data = the documents returned to the index.
- error = log of system stack case that occurs an exception .
- number_documents_treated = Number of documents sucessfully treated by this endpoint.
- number_documents_non_treated = Number of documents not treated by this endpoint.
- list_id_not_treated = List of dictionaries with document_id and reason why the document is not treated. Ex.
```
response['list_id_not_treated']

[{'wQqSOYsBDWjYcrG-vsB4': 'No Input Text in documents'},
 {'wgqSOYsBDWjYcrG-vsB4': 'File type not valid'},
 {'TgqSOYsBDWjYcrG-vsB4': 'File type not valid'},
 {'TwqSOYsBDWjYcrG-vsB4': 'File type not valid'},
 {'WgqSOYsBDWjYcrG-vsB4': 'File type not valid'},
 {'XQqSOYsBDWjYcrG-vsB4': 'File type not valid'},
 {'XwqSOYsBDWjYcrG-vsB4': 'File type not valid'},
 {'ZgqSOYsBDWjYcrG-vsB4': 'File type not valid'},
 {'ZwqSOYsBDWjYcrG-vsB4': 'File type not valid'},
 {'awqSOYsBDWjYcrG-vsB43': 'File type not valid'}]

```

# Example of logging an Exception and returning in the Response
The log include in the 
- first line type of Exception
- Second line the value which cause the exception
- From second like the dump of the stack trace in python

```
print(response['error'])

KeyError
'PII_Type'
File : D:\repos\Detect-AI\nlp\app\classification\endpoint_classification.py , Line : 168, Func.Name : process_tika, Message : mapper = PIIMapper(
File : D:\repos\Detect-AI\nlp\app\classification\pii_codex\utils\pii_mapping_util.py , Line : 83, Func.Name : __init__, Message : self._pii_mapping_data_frame = open_pii_type_mapping_csv_reload(
File : D:\repos\Detect-AI\nlp\app\classification\pii_codex\utils\file_util.py , Line : 145, Func.Name : open_pii_type_mapping_csv_reload, Message : df[col] = df_weigths[col].values
File : C:\Users\HYSTOU\.conda\envs\pii\lib\site-packages\pandas\core\frame.py , Line : 3807, Func.Name : __getitem__, Message : indexer = self.columns.get_loc(key)
File : C:\Users\HYSTOU\.conda\envs\pii\lib\site-packages\pandas\core\indexes\base.py , Line : 3804, Func.Name : get_loc, Message : raise KeyError(key) from err


```
