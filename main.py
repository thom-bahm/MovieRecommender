'''
Authors: <Thomas Bahmandeji, Jackson Sanger>
'''
from flask import Flask, render_template, request, jsonify, g
from chat_api import collect_messages, get_client, check_prompt_safe
from vdb import * 

app = Flask(__name__)

# Connect to the local client if it is running locally. if not, create the client
# store the weav_client in the flask context so we can see if it is not there
def get_weaviate_client():
    if 'weav_client' not in g:
        g.weav_client = connect_to_local() or create_client()
    return g.weav_client

# handle closure of the weaviate client when flask app is stopped
@app.teardown_appcontext
def close_weaviate_client(exception):
    weav_client = g.pop('weav_client', None)
    if weav_client is not None:
        weav_client.close()


# Using flask to host a single page app
@app.route('/', methods=['GET', 'POST'])
def index():
    gpt_client = get_client()
    weav_client = get_weaviate_client()
    # Create the DB if it does not exist
    if not weav_client.collections.exists("Movies"):
        create_and_load_db(weav_client)
    
    # The user submits the form (Sends a message/question)
    if request.method == 'POST':
        user_message = request.form['message']
        # User the users prompt to query the vector database, and
        # have the LLM review if the information retrieved is actually on topic.
        ok_vectors = compare_prompt_and_vector(weav_client, gpt_client, user_message)
        response = collect_messages(gpt_client, user_message, ok_vectors, debug=False)
        return jsonify({'user_message': user_message, 'api_response': response})
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)


# For console testing without flask
# def main():
#     gpt_client = get_client()
#     weav_client = connect_to_local()
#     print("ASDASD", weav_client.collections.exists("Movies"))
#     if not weav_client.collections.exists("Movies"):
#         create_and_load_db(weav_client)
    
#     # query_database(weav_client)
#     compare_prompt_and_vector(weav_client, gpt_client, "R rated comedy movies")
#     weav_client.close()

#     # resp = collect_messages(gpt_client)
#     # while resp != '':
#     #     resp = collect_messages(gpt_client)

# if __name__ == '__main__':
#     main()

