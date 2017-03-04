# Requirements
###### Current status: Shippable
###### ...but wouldn't be too happy about it

### Must haves

* ~~Facebook bot must be able to accept photos of product and backend must record the name and category of the product in database~~
* ~~Must be able to handle basic electronic products and produce~~
* ~~Backend must be able to find the estimated price of a product given its name~~
* ~~Web UI must be able to display past value of thrown out trash through graphs~~
* ~~Facebook bot must allow user to get to their Web UI~~

### Should haves

* Facebook bot should attempt to minimze amount of clicks required for must haves ( good UX )
* Facebook bot should assist user in posting old trash to Kijiji if its value is high
* Facebook bot should be able to show relevant trash history if user sends location which is near a store
* Web UI should be able to add friends on social network, and compete to minimize the amount of trash they dispose
* ~~There should be a way to link Kijiji Accounts to your TrashWatch profile~~

### Nice to haves

* All web graphs through Web UI would be nice to have be customly styled
* It would be nice to use eBay API to find product prices in backend
* It would be nice if I didn't have to train my own own neural nets with Clarifai and products were labeled already for us
* It would be nice to ship within 24 hours so I can sleep xD
* Web UI would be nice if it was responsive
* Web UI would be nice if it had custom CSS styling
* Web UI would be nice if it was one page only
* Web UI would be nice if it allowed us to set waste management goals 
* Backend would be nice if it could handle a peer to peer sales marketplace instead of hooking up to Kijiji API

# APIs & Technologies

* Clarifai -> Detecting what product it is
* Kijiji -> Post ads 
* VueJS & Vue-Chart -> Front end
* Flask & Flask-SQLAlchemy -> Back end
* (optional) Google Maps API -> Detecting stores near user location
* (optional) eBay Marketplace API

