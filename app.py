from flask import Flask, request, jsonify, render_template
import google.generativeai as genai  # Import the Gemini client

# Initialize Flask app
app = Flask(__name__)

# Initialize the Gemini client
GEMINI_API_KEY = "AIzaSyCN3DuqwGnUusZ6OHwRatlu15v1pUgTDoE"  # Replace with your Gemini API key
genai.configure(api_key=GEMINI_API_KEY)
MODEL = "gemini-1.5-pro"  # Use the Gemini 1.5 Pro model

# Define the tree structure
tree = [
    {
        "nodeId": "node1",
        "rootNode": True,
        "prompt": "Hello! Are you John?",
        "edges": [
            {"condition": "user is John", "targetNodeId": "node2"},
            {"condition": "user is not John", "targetNodeId": "node3"}
        ]
    },
    {
        "nodeId": "node2",
        "prompt": "Great to meet you, John. I’m Monika, the AI agent here to conduct your Frontend Developer interview. Are you ready to begin the interview right now?",
        "edges": [
            {"condition": "user is ready to start the interview", "targetNodeId": "node4"},
            {"condition": "user is not ready to start the interview", "targetNodeId": "node5"}
        ]
    },
    {
        "nodeId": "node3",
        "prompt": "I apologize for the confusion. It seems I’ve reached the wrong candidate. Thank you for your time, and I’m sorry for any inconvenience. Have a great day!",
        "edges": []
    },
    {
        "nodeId": "node4",
        "prompt": "Excellent! Let’s get started. First question: What is a closure in JavaScript?",
        "edges": []
    },
    {
        "nodeId": "node5",
        "prompt": "I understand, no problem at all. I’m sorry for catching you at a busy time. Would you like me to end the call now, and we can reschedule for a more convenient time?",
        "edges": []
    }
]

# Helper function to generate chatbot responses
def generate_response(messages):
    model = genai.GenerativeModel(MODEL)
    try:
        # Convert messages to the format expected by Gemini
        formatted_messages = []
        for message in messages:
            formatted_messages.append({"role": message["role"], "parts": [{"text": message["content"]}]})
        
        # Generate response using Gemini
        response = model.generate_content(formatted_messages)
        
        # Debug the response
        print(f"API Response: {response}")
        print(f"Response Text: {response.text}")
        print(f"Response Candidates: {response.candidates}")
        print(f"Finish Reason: {response.candidates[0].finish_reason if response.candidates else 'No candidates'}")
        
        # Check if the response contains valid text
        if response.text:
            return response.text.strip()
        else:
            # Handle cases where the response does not contain text
            print("No valid text in response. Finish reason:", response.candidates[0].finish_reason)
            return messages[-1]["content"]  # Return the last assistant message as a fallback
    except Exception as e:
        print(f"Error generating response: {e}")
        return "Sorry, something went wrong. Please try again."

# Helper function to evaluate conditions
def evaluate_condition(condition, user_input):
    # Simplify condition evaluation logic
    if condition == "user is John":
        return "john" in user_input.lower()  # Check if "john" is in the user's input
    elif condition == "user is not John":
        return "john" not in user_input.lower()  # Check if "john" is not in the user's input
    elif condition == "user is ready to start the interview":
        return "ready" in user_input.lower()  # Check if "ready" is in the user's input
    elif condition == "user is not ready to start the interview":
        return "ready" not in user_input.lower()  # Check if "ready" is not in the user's input
    else:
        return False  # Default to False if condition is not recognized

# Helper function to find a node by ID
def find_node_by_id(node_id):
    for node in tree:
        if node["nodeId"] == node_id:
            return node
    return None

# Global variable to track the current node and conversation history
current_node = None
conversation_history = []

# Route for the home page
@app.route("/")
def home():
    return render_template("index.html")

# Route to handle chatbot interaction
@app.route("/chat", methods=["POST"])
def chat():
    global current_node, conversation_history

    # Initialize conversation if no current node
    if current_node is None:
        current_node = find_node_by_id("node1")
        conversation_history = [
            {"role": "assistant", "content": current_node["prompt"]}
        ]
        print(f"Initializing conversation. Current node: {current_node['nodeId']}")
        return jsonify({"response": current_node["prompt"], "current_node": current_node["nodeId"]})

    # Get user input
    user_input = request.json.get("user_input")
    print(f"User input: {user_input}")

    # Add user input to conversation history
    conversation_history.append({"role": "user", "content": user_input})

    # Evaluate conditions and move to the next node
    if "edges" in current_node and current_node["edges"]:
        for edge in current_node["edges"]:
            print(f"Evaluating condition: {edge['condition']}")
            if evaluate_condition(edge["condition"], user_input):
                current_node = find_node_by_id(edge["targetNodeId"])
                print(f"Condition met. Moving to node: {current_node['nodeId']}")
                break
        else:
            response = "I'm sorry, I didn't understand your response. Let's try again."
            print("No condition met. Asking user to try again.")
            conversation_history.append({"role": "assistant", "content": response})
            return jsonify({"response": response, "current_node": current_node["nodeId"]})
    else:
        response = "Thank you for your time. The interview is now complete."
        print("Interview completed. Resetting conversation.")
        conversation_history.append({"role": "assistant", "content": response})
        current_node = None  # Reset the conversation
        return jsonify({"response": response, "current_node": None})

    # Generate response for the new node
    conversation_history.append({"role": "assistant", "content": current_node["prompt"]})
    response = generate_response(conversation_history)
    print(f"Generated response: {response}")
    return jsonify({"response": response, "current_node": current_node["nodeId"]})

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)