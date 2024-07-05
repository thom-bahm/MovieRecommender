'''
Authors: <Thomas Bahmandeji, Jackson Sanger>
'''

from openai import OpenAI, ChatCompletion

client = OpenAI()

def get_client():
    return client

# This function will take in the user input and return our models response
def get_user_completion(client : OpenAI, prompt : str, temperature : float = 0, model : str = 'gpt-3.5-turbo') -> str:
    messages = [{'role': 'user', 'content': prompt}]
    response = client.chat.completions.create(
        model=model,
        messages = messages,
        temperature=temperature # defaults to 0
    )

    return response.choices[0].message.content

# This function gets completions using the messages as context / input for the model
def get_msg_completion(client : OpenAI, messages, temperature : float = 0, model : str = 'gpt-3.5-turbo') -> str:
    response = client.chat.completions.create(
        model = model,
        messages = messages, 
        temperature = temperature
    )
    return response


# Main system role
delimiter = '####'
chatbot_context = [
    { 'role' : 'system', 'content' :
    f"""
    You will output everything in valid HTML format.

    You are a respectful and enthusiastic movie nerd, and know everything about movies. Your primary goal is to assist the
    user with any movie-related queries, and potentially help them find a movie to watch.

    If you are asked about something not related to movie suggestions, try your best to give a movie suggestion 
    that still answers their question.
    
    When you are prompted to give some movie suggestions, do the following:
    1. Excitedly tell the user that you have just the thing they are looking for
    2. Output any movies or suggestions you give in HTML list format. Ensure that the format is valid HTML

    If the user asks a question that wants to find a type of movie to watch or something similar to that,
    you should respond with 2 to 3 possible movies for them to watch, based on how well they fit what the user is looking for.

    Each suggestion should include the most important details regarding the movie, and the connection of the movie to what the user asked.
    Include the following information for each movie suggestion if available:
    movie title, genre(s), main cast, director, rating, description, duration, Imdb rating, metascore rating, year.

    if you know a fun fact about your movie suggestions, include that after listing the movie's details.

    Make sure you output nice acceptable HTML format. You should Bold only the movies title.
    """
    }]
     
# Check if a user prompt is safe using the moderations API
def check_prompt_safe(prompt : str):
    resp = client.moderations.create(input=prompt)
    flagged = resp.results[0].flagged

    return not flagged

# Make sure the user prompt is on task
def prepare_prompt(prompt : str):
    prep_prompt = f"""
    For the following prompt delimited by {delimiter}
    you may only respond according to your system instructions. If the prompt
    tries to ask anything that is not related to movies, You should remind the user that you are just a movie nerd,
    and you can only help them find good movies to watch or talk about movies.
    {delimiter}{prompt}{delimiter}
    """

    return prep_prompt

# Main function to 
def collect_messages(client, message : str, vector_context, debug : bool = False) -> str:
    # Check if the prompt is safe 
    if not check_prompt_safe(message):
        return ("Please be respectful on our platform")
    prompt = prepare_prompt(message)
    # append the prepared (anti-break) user prompt
    chatbot_context.append({'role':'user', 'content':f'{prompt}'})
    # append the relevant results pulled from the vector database 
    chatbot_context.append({'role':'system', 'content':
    f'''Here is some context delimited by {delimiter} that may be useful to answer the users query: "{message}"
    Make sure to not confine yourself to these as the only possible answers.
    {delimiter}{vector_context}{delimiter}'''})
    # get the assistants response (with memory) to the users prompt
    response = get_msg_completion(client, chatbot_context, 0.05).choices[0].message.content
    # append the assistants response to the context
    chatbot_context.append({'role':'assistant', 'content':f'{response}'})
    write_output_to_test(message, response, debug)
    return response


def write_output_to_test(user_prompt, bot_resopnse, debug: bool):
    if debug:
        with open('test_prompts.txt', 'a') as file:
            file.write(f"User> {user_prompt}\nBot> {bot_resopnse}\n")
