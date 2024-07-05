import weaviate
import weaviate.classes as wvc
import os
import json
from openai import OpenAI
"""
File: vdb.py
Author: <Thomas Bahmandeji, Jackson Sanger>
Date: 06-07-2024
"""
from chat_api import get_user_completion

def create_client(weaviate_version="1.24.10") -> weaviate.WeaviateClient:
    # create the client
    client = weaviate.connect_to_embedded(
        version=weaviate_version,
        headers={
            # this pulls your OPENAI_API_KEY from your environment (do not put it here)
            "X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY")
        }) 
    return client

# Function to connect to vdb in the case that the weaviate instance is already running on some port
# defaulted to 8079, 50050 since thats where ours initially was running
def connect_to_local(port="8079", grpc_port="50050") -> weaviate.WeaviateClient:
    # create the client
    try:
        client = weaviate.connect_to_local(
            port=port,
            grpc_port=grpc_port,
            headers={
                # this pulls your OPENAI_API_KEY from your environment (do not put it here)
                "X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY")
            }) 
        return client
    except Exception as e:
        print(f"Error occured connecting to local weaviate client: {e}")
        return None


def drop_and_recreate_collection(client: weaviate.WeaviateClient, 
                                 collection_name: str,
                                 embedding_model: str = 'text-embedding-3-small',
                                 model_dimensions: int = 512):
    """
    Create the collection. If it already exists, drop it and recreate it. 
    """
    if client.collections.exists(collection_name):
        client.collections.delete(collection_name)
    # otherwise, create the collection with schema
    collection = client.collections.create(
        name=collection_name,
        description="A collection of movie information",
        properties=[
            wvc.config.Property(
                name="ID",
                description="The movie ID",
                data_type=wvc.config.DataType.TEXT
            ),
            wvc.config.Property(
                name="Title",
                description="The title of the movie",
                data_type=wvc.config.DataType.TEXT
            ),
            wvc.config.Property(
                name="Year",
                description="Release year of the movie",
                data_type=wvc.config.DataType.INT
            ),
            wvc.config.Property(
                name="Rating",
                description="Movie certificate rating, such as R, PG-13, etc",
                data_type=wvc.config.DataType.TEXT
            ),
            wvc.config.Property(
                name="Duration",
                description="Duration of the movie in minutes",
                data_type=wvc.config.DataType.INT
            ),
            wvc.config.Property(
                name="Genre",
                description="Genre of the movie",
                data_type=wvc.config.DataType.TEXT
            ),
            wvc.config.Property(
                name="ImdbGoodnessRating",
                description="Imdb rating of the movie",
                data_type=wvc.config.DataType.NUMBER
            ),
            wvc.config.Property(
                name="MetascoreGoodnessRating",
                description="Metascore rating of the movie",
                data_type=wvc.config.DataType.INT
            ),
            wvc.config.Property(
                name="Director",
                description="Director of the movie",
                data_type=wvc.config.DataType.TEXT
            ),
            wvc.config.Property(
                name="Cast",
                description="Cast of the movie",
                data_type=wvc.config.DataType.TEXT
            ),
            wvc.config.Property(
                name="Description",
                description="Brief description of the movie",
                data_type=wvc.config.DataType.TEXT
            )
        ],
        # configure the vectorizer, which will get your embeddings
        vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_openai(
            model=embedding_model,
            dimensions=model_dimensions
        ),
        # default to the openai LLM for generative work
        generative_config=wvc.config.Configure.Generative.openai()
    )
        
    # now return the collection
    return collection

def clean_int(value):
    try:
        return int(value.replace(',', ''))
    except (ValueError, AttributeError):
        return None

def clean_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def load_data(collection, data_file="./movies_medium.json"):
    # Placeholder for python dicts
    movies = []
    # Load JSON data from file
    with open(data_file, "r") as file:
        try:
            movie_data = json.load(file)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON file: {e}")
            return
        
        # Extract and structure movie information
        for movie in movie_data:
            try:
                movies.append({
                    'ID': movie.get('ID'),
                    'Title': movie.get('Title'),
                    'Year': clean_int(movie.get('Year')),
                    'Rating': movie.get('Certificate'),
                    'Duration': clean_int(movie.get('Duration (min)')),
                    'Genre': movie.get('Genre'),
                    'ImdbGoodnessRating': clean_float(movie.get('Rating')),
                    'MetascoreGoodnessRating': clean_int(movie.get('Metascore')),
                    'Director': movie.get('Director'),
                    'Cast': movie.get('Cast'),
                    'Description': movie.get('Description')
                })
            except Exception as e:
                print(f"Error processing movie with ID {movie.get('ID')}: {e}")
    
    # Insert into the data set
    collection.data.insert_many(movies)

def print_collection_contents(collection):
    response = collection.query.fetch_objects(limit=4999)
    print("###########################")
    print("THE ENTIRE DATASET:")
    # for o in response.objects:
    #     print(f"{o.properties}")
    print(f"Length of collection: {len(response.objects)}")
    print("###########################")

def create_and_load_db(client: weaviate.WeaviateClient):
    try:
        # client = create_client()
        movie_collection = drop_and_recreate_collection(client, "Movies")
        load_data(movie_collection)

        # Print the collection contents so we can see
        print_collection_contents(movie_collection)
        print("Database preloaded successfully.")
        return movie_collection
    except Exception as e:
        print(f"An error occurred handling the client or collection: {e}")
    
    finally:
        # Example: Close the database client if it was created
        if client:
            try:
                client.close()
                print("Closed client")
            except Exception as e:
                print(f"Error closing client: {e}")
            
    return None


# QUERY RELATED CODE:


def compare_prompt_and_vector(weav_client: weaviate.WeaviateClient, open_ai_client: OpenAI, user_prompt: str) -> list:
    """
    Compares the user's prompt with what is returned by the vector database, and decides if the result is on topic.
    If it is, a list will be returned of the on-topic vectors.
    """
    # Query Weaviate to get the relevant vectors
    collection = weav_client.collections.get("Movies")
    response = collection.query.near_text(
        query=user_prompt,
        certainty=0.7,
        return_metadata=wvc.query.MetadataQuery(certainty=True),
        limit=5
    )
    
    vectors = response.objects
    ok_vectors = []

    delimiter = "###"
    
    # Compare each vector's content with the user prompt using the llm
    for vector in vectors:
        comparison_prompt = f"""
        For the following user prompt delimited by triple hashtags: {delimiter}{user_prompt}{delimiter}
        And for the following movie information formatted as a JSON object delimited by triple hashtags: {delimiter}{vector}{delimiter}
        For context, here is what the different keys in the json correspond to:
        Title: name of the movie.
        Year: year the movie was released.
        Rating: age rating given to the movie. 
        Duration: length of the movie in minutes.
        Genre: genre(s) of the movie
        ImdbGoodnessRating: IMDB user rating for the movie.
        MetascoreGoodnessRatinge: score from critics.
        Director: director(s) of the movie.
        Cast: main actors in the movie.
        Description: brief summary of the movie's plot.

        Read the user prompt, and compare it with the movie information json object given. 
        Answer precisely "yes" if it is related to what the user prompt is asking for - you should check the fields of the JSON movie object to confirm this.
        Answer precisely "no" if the movie json object has fields that contradict the user prompt, or if the json does not seem like a valid 'answer' to the users query.

        An example of when to respond 'yes' would be something like the user asking "what is a movie about cartels"
        and the description in the movie json has the word "cartel" in it.

        Be careful to check the fields of the json to see if they match with the users prompt. For example: If the user prompt is "R rated comedy movies", 
        and the 'Rating' field in the json says "PG-13", you should respond "no", since "R-rated" means a Rating with value "R".
        """
        
        # Get the comparison result from the OpenAI API
        comparison_result = get_user_completion(open_ai_client, comparison_prompt)
        print(vector)
        print(comparison_result)
        print()

        if "yes" in comparison_result.lower():
            print(vector)
            ok_vectors.append(vector)
    
    return ok_vectors


# def query_database(client: weaviate.WeaviateClient):
#     # Access the collection
#     collection = client.collections.get("Movies")
    
#     query_2 = "R-rated comedy movies"
#     response_2 = collection.query.near_text(query=query_2, limit=10, certainty=0.6, return_metadata=wvc.query.MetadataQuery(distance=True, certainty=True))
#     print("###########################")
#     print(f"Query 2: {query_2}")
#     for i in range(10):
#         print(f"{i+1}: {response_2.objects[i].properties}")
#         print(f"{i+1}: {response_2.objects[i].metadata}\n")
#     print("###########################")
