# MLExchange Content Registry
Content registry and its API for the MLExchange platform.

Contents include:  
	- models  
	- apps  
	- workflows  

## How to use
**Running content registry**   
`docker-compose up --build`

**Viewing existing contents**  
Scroll down to the bottom of the page, click on **Refresh** button.

**Delete existing contents**  
Select contents from the table and click **Delete** button.

**Modify existing contents**  
Currently, the **Modify** button is restricted to limited information items. 
Therefore, the easiest way to modify an existing registration is to delete the content, then upload the changed JSON document again (drag and drop, click **Validate** button first, then click the **Upload** button).

## APIs
get\_models()  
get\_model(uid) 


get\_apps()  
get\_app(uid) 


get\_workflows()  
get\_workflow(uid) 


post\_assets(data)  
post\_asset(data) 
get\_assets()  
get\_asset(uid) 
delete\_assets(query)  
delete\_asset(uid) 


