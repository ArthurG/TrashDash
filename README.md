#TrashDash

## Problem

Every year in North America, the average consumer throws out between 95-115 kg of waste in just food products alone. How many drinks can we buy at Phils if we each save that money instead? Too many. In addition, as students, we also purchase many products that we use for one year then throw out such as tables, microwaves, and laptops. 

## Vision

The problem is with purchasing food or products that we think we will eat or use, but end up throwing out. We assume that it won't happen next week/month/term/year. TrashDash uses your trash data to persuade you otherwise. TrashDash aims to minimize the amount of trash that you produce: both before AND after purchase. 
TrashDash seeks to bring Fitbit-level user tracking and gamification to the problem of waste.  


## How it's done

Every time you dispose a piece of garbage, you take a picture of it and send it to the TrashDash Facebook Messenger Bot. The bot recognizes what the product is, and estimates the value of the product. 

Firstly, the bot aims to use this information change users purchase habits. At a grocery store, the bot tells you the food product categories with the most waste. Maybe you would buy less of those categories so you throw out less. Maybe you ignore those aisles completely. Looking to buy oranges but you threw out a bunch last week? TrashDash tells you to put them down. 

The other reason for this problem comes us impulsively purchase products we'll never use. TrashDash aims to reduce the amount of trash by reusing whenever possible. For high value products (such as phones or laptops), the bot will help you to post it to Kijiji. Just specify the title, description, and price and wait for the responses to roll in. 

Both these solutions are held together with gamification.  TrashDash also shows you the amount of trash that your friends throw out as well on your dashboard. This aims to persuade users to lower the trash they throw out relative to their friends and make the bot more addicting.  

## Technology Stack

Flask is used on the backend. Leveraging Clarifai API, Google Maps (Places) API, Facebook Messenger Bots API, and Facebook Graph API. Kijiji Posting accomplished with the KijijiRepostHeadless OSS project. The project also makes use of some natural language processing with TextBlob. Front end made in VueJS and vue-chart for max prettiness. 

## Future Goals

A lot of the potential of this bot relies on changing user habits. So, a natural next step is to analyze real use to identify ways to improve UX. Which actions are taking too long or too many clicks to complete?  It's hard work to change habits, making the process easier helps.

Secondly, integration into a AR headset would be a doable and useful next step. Having a dashboard on the corner of your eye would be really useful for changing use purchasing habits. As well, being able to take pictures of your trash without your phone is really convenient. 

Finally, I would like to integrate TrashDash with Nest Cameras. Cameras would allow TrashDash  to monitor the products (or foods) that are and are not used frequently. This would help make even better recommendations on what to and not to buy when the user is at the store. This would also remove the requirement of taking pictures of your trash.


