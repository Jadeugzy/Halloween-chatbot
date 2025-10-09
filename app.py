from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)
app.secret_key = "game-secret-key-12345"

# Game data
PATHS = {
    "conjuring": [1, 2, 3, 4, 5],
    "insidious": [1, 3, 4, 5, 2],
    "the shining": [2, 1, 5, 3, 4],
    "the exorcist": [2, 4, 1, 5, 3],
    "the ring": [3, 2, 1, 4, 5],
    "poltergeist": [3, 5, 2, 1, 4],
    "sinister": [4, 3, 5, 2, 1],
    "scream": [4, 5, 3, 1, 2],
    "evil dead": [5, 4, 2, 3, 1],
    "the grudge": [5, 1, 4, 2, 3]
}

LOCATION_CLUES = {
    1: "(Clue A) place of origin",
    2: "(Clue B) umur",
    3: "(Clue C) organ", 
    4: "(Clue D) jam",
    5: "(Clue E) kulitny ad ap"
}

ANSWERS = {
    1: ["romania"],
    2: ["765 years", "765 tahun"],
    3: ["nails to the heart", "paku di jantung"],
    4: ["6:26 am", "6:26"],
    5: ["3 symbols", "3 simbol"]
}

ALPHABET_CLUES = {
    1: "M",
    2: "O", 
    3: "R",
    4: "Z",
    5: "A"
}

FINAL_WORD = "MORZA"

def start_new_game():
    session.clear()
    session['stage'] = 'ask_team'
    session.modified = True

@app.route('/')
def home():
    start_new_game()
    return render_template('index.html')

@app.route('/api/message', methods=['POST'])
def handle_message():
    data = request.json or {}
    user_input = data.get('text', '').strip().lower()

    # Initialize session if needed
    if 'stage' not in session:
        start_new_game()

    responses = []

    if session['stage'] == 'ask_team':
        if user_input in PATHS:
            session['team'] = user_input
            session['path'] = PATHS[user_input]
            session['current_location_index'] = 0
            session['current_location'] = session['path'][0]
            session['chances_left'] = 5
            session['total_points'] = 0
            session['alphabet_clues'] = []
            session['stage'] = 'in_game'
            session.modified = True

            responses.append({
                "text": f"Team {user_input.title()} accepted. Let the investigation begin.",
                "type": "system"
            })
            # Give first location clue only
            loc = session['current_location']
            responses.append({
                "text": LOCATION_CLUES[loc],
                "type": "clue"
            })
            responses.append({
                "text": f"Find this location and enter the answer. You have {session['chances_left']} chances.",
                "type": "system"
            })
        else:
            responses.append({
                "text": "Unknown team. Use: conjuring, insidious, the shining, the exorcist, the ring, poltergeist, sinister, scream, evil dead, the grudge",
                "type": "error"
            })

    elif session['stage'] == 'in_game':
        current_loc = session['current_location']

        # Check if answer is correct
        if user_input in [ans.lower() for ans in ANSWERS[current_loc]]:
            # Correct answer
            points_earned = session['chances_left']
            session['total_points'] += points_earned

            responses.append({
                "text": "✓ Correct! The clue is verified.",
                "type": "success"
            })
            responses.append({
                "text": f"Earned {points_earned} points for this location.",
                "type": "success"
            })
        else:
            # Wrong answer
            session['chances_left'] -= 1

            if session['chances_left'] > 0:
                responses.append({
                    "text": f"✗ Incorrect. {session['chances_left']} chances remaining.",
                    "type": "error"
                })
                # Don't move to next location yet, wait for next attempt
                session.modified = True
                return jsonify(responses)
            else:
                # Out of chances
                responses.append({
                    "text": "No chances left! Moving to next location...",
                    "type": "error"
                })

        # Give alphabet clue regardless of correct answer or running out of chances
        alphabet_clue = ALPHABET_CLUES[current_loc]
        responses.append({
            "text": f"Alphabet clue: {alphabet_clue}",
            "type": "alphabet"
        })
        session['alphabet_clues'].append(alphabet_clue)

        # Move to next location
        session['current_location_index'] += 1

        if session['current_location_index'] < 5:
            # More locations remaining
            session['current_location'] = session['path'][session['current_location_index']]
            session['chances_left'] = 5

            loc = session['current_location']
            responses.append({
                "text": LOCATION_CLUES[loc],
                "type": "clue"
            })
            responses.append({
                "text": f"Find this location and enter the answer. You have {session['chances_left']} chances.",
                "type": "system"
            })
        else:
            # All locations completed
            session['stage'] = 'final_guess'
            responses.append({
                "text": "All locations investigated! Now for the final challenge...",
                "type": "system"
            })
            responses.append({
                "text": "Using the alphabet clues you collected, guess the 5-letter final word. You have ONE attempt:",
                "type": "system"
            })

        session.modified = True

    elif session['stage'] == 'final_guess':
        user_guess = user_input.upper().strip()

        if len(user_guess) != 5:
            responses.append({
                "text": "Final word must be 5 letters. Game over.",
                "type": "error"
            })
        else:
            # Calculate final word points
            final_points = 0
            for i in range(5):
                if user_guess[i] == FINAL_WORD[i]:
                    final_points += 2

            session['total_points'] += final_points

            responses.append({
                "text": f"Your guess: {user_guess}",
                "type": "system"
            })
            responses.append({
                "text": f"Correct word: {FINAL_WORD}",
                "type": "system"
            })
            responses.append({
                "text": f"Final word points: {final_points}",
                "type": "success"
            })

        # Game completed
        responses.append({
            "text": f"TOTAL SCORE: {session['total_points']} points",
            "type": "success"
        })
        responses.append({
            "text": "Game completed! Refresh page to play again.",
            "type": "system"
        })

        session['stage'] = 'completed'
        session.modified = True

    elif session['stage'] == 'completed':
        responses.append({
            "text": "Game already completed. Refresh page to start new game.",
            "type": "system"
        })

    return jsonify(responses)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)