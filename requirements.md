* create a fast api server
* should have the option to persist data in multiple dataecosystems like a) postgres b) mysql c) micosoft sql server d) mongodb
* my backend database tables will be based on several focus areas a) users b) user interactions c) workflows orchestrated by useers d) interactions betweenn AI agents where they are sharing information and persisting them in state e) the information shared by different microservies etc.
* should be configuration driven
* should have the ability to handle authentication
* should support multiple personas for authorization and these personas should be configuration driven
* the authrorization should be implemented as route guards on the backend
* should be able to call other microservices
* should have the ability to handle rate limiting
* should have robust error logging
* should have the ability to handle async jobs