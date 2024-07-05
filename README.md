# Movie Recommender ChatBot by Thomas Bahmandeji, Jackson Sanger

### Project Description
Our project is a Movie Nerd Recommender chatbot agent. The bot knows everything there is to know about movies, and it is respectful and enthusiastic. If the user is not asking specific questions, the movie nerd will offer assistance.

Generally the ChatBot will output a list of movie suggestions that coincide with what the user queried.

### Implementation Details

The data we used to build our Vector Database was a set of 10,000 movies of an Imdb dataset which we got from (Kaggle)[https://www.kaggle.com/datasets/amanbarthwal/imdb-movies-data]. The input json objects include the following information:
* Title: name of the movie.
* Year: year the movie was released.
* Rating: age rating given to the movie. 
* Duration: length of the movie in minutes.
* Genre: genre(s) of the movie
* Imdb Rating: IMDB user rating for the movie.
* Metascore: score from critics.
* Director: director(s) of the movie.
* Cast: main actors in the movie.
* Description: brief summary of the movie's plot.

I implemented the upload of this dataset using dynamic batch upload to avoid timeouts and additionally to vastly increase upload speed.

Moderation:
- We used the OpenAI moderations API to ensure that user prompts were not harmful

Prompt injection prevention:
- We employed the use of delimiters and pre-prompt instruction to ensure that any mal-intented input to the model will be disregarded

ChatBot context:
- We used a system prompt that detailed general instructions for how the bot should behave.
- We used chain-of-thought prompting and specified that it should output HTML format so we could nicely 
- After gathering the relevant vectors from our database, We append this information as a system prompt to the context
- We then append the users prompt and assistants response to the context, so that the bot has a sense of 'memory'.

#### Vector database and LLM cross-referencing implementation details

Handling weaviate client:
- Created a function to handle connecting to already existing weaviate client or creating the client if it did not exist locally
- Used flasks teardown_appcontext functionality to ensure our weaviate client was closed after the application is stopped.

Creating the vector database:
- We used a function to drop and recreate the collection in the case that we made changes to the vector database and needed to re-create it.
- Conditionally either accessed the already existing database if it existed or created the collection if not
- Used descriptive property names to store things about the movie like the Imdb rating so that the vector database could accurately find near text when prompted by the user. 
- Used dynamic batch upload for quick and efficient data uploads

Querying the database:
- Used the near_text search operator to search our database with the users input as natural language, and set specific settings to ensure only relevant data was returned from the vector database (ie setting a minimum certainty of 0.7)

Cross-referencing our vector database results with our LLM:
- For each user input, we retrieved the 5 most similar vectors in our database and uploaded these to our LLM to check if the vector db results retrieved are consistent with what the user was querying.
- To do this, we developed a prompt that instructed the LLM to respond with 'yes' or 'no' indicating if the vector db result is a 'good' answer for what the user wanted.
- We then only passed on the vector db results that got a 'yes' from the LLM to the main LLM query, where we provided the vector db results as a system role to the chatbot context, and instructed the LLM that these results may be useful, but are not binding.


## Usage instructions

To use this movie recommender agent you will have to clone this repository onto your machine. After doing so, make sure to export your openai api key to your environment. For mac, this looks like ```export OPENAI_API_KEY="<YOUR KEY HERE>"```

After this you should be able to run the main.py script and the flask app should be started (the first time you run this, it will have to create the client, and importantly create and upload all movies to the vector database).

You can interact with the chatbot on the flask app.