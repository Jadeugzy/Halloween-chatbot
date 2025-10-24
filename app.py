from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)
app.secret_key = "game-secret-key-12345"

PATHS = {
    "conjuring": [1, 2, 3, 5, 4],
    "insidious": [1, 4, 5, 3, 2],
    "the shining": [2, 3, 5, 4, 1],
    "the exorcist": [2, 1, 4, 5, 3],
    "the ring": [3, 5, 4, 1, 2],
    "poltergeist": [3, 2, 1, 4, 5],
    "sinister": [4, 1, 2, 3, 5],
    "scream": [4, 5, 3, 2, 1],
    "evil dead": [5, 4, 1, 2, 3],
    "the grudge": [5, 3, 2, 1, 4]
}

LOCATION_CLUES = {
    1: "(Zone A) I am from the nearest north entrance. Where the modern technology I find dead, to the first left turn to be. Find the red. Enter. Don’t stop. Keep walking. Another left and there I will find you.",
    2: "(Zone B) To find what you seek, go first to where the northern gate is near. There, a silent guardian sits forever still, a figure forged in metal upon a towering chair, keeping its unseeing watch. Not far from his unblinking gaze stands an abandoned sentinel, whose lights have long gone dark, its interior once stocked with travel-sized comforts for weary travelers. Now it stands as a relic, its purpose faded, marking the edge of a secluded and shadowy space. Venture behind this relic of commerce, and you will find a miniature wilderness. Here, the world grows dense and shadowy, a secluded patch where trees and tangled bushes conspire to guard their secrets from the casual eye. Let your gaze climb the trunks and branches above, or scour the hidden nooks and fallen debris below, for your objective awaits.",
    3: "(Zone C) seek for the crowd where uneven spirits guarding the heaven's gates, standing by the holy place. It's where the silence hides the truth. How to answer : case 1 - 1st word (space) 2nd word ", 
    4: "(Zone D) On the night of the full moon, they gather still in a silent toon. The herd doesn’t flee, stick together forever and ever. No footprints - only shadows. Where the wilderness kiss a cabin. A family stays together and the time is under it. How to answer : 'hour:minutes' am",
    5: "(Zone E) I begin at the Grand Welcome, where SISC greets its guests. To find my start, ignore the crowd and pivot sharply left into the territory coded 'E'. You must first find the nearest place of relief within this grand receiving area, for that spot marks your true beginning. From there, I lead you away from the plaza's light, climbing the stone steps into the quiet shadow. I continue uphill through the darkness, until the only sight left is the weathered glass of a humble, solitary shack. How to answer: clue 1, clue 2, clue 3"
}

ANSWERS = {
    1: ["romania"],
    2: ["765", "765 years"],
    3: ["heart - rusty nail","heart-rusty nail","heart - rust nail","heart-rust nail"],
    4: ["6:26 am", "6:26", "6.26", "6.26 am","06:26 am", "06:26", "06.26", "06.26 am"],
    5: ["inverted pentagram, inverted, 666"]
}

ALPHABET_CLUES = {
    1: "one dips, two rise (wplo shift 11)",
    2: "a perfect ring of death (ylfh shift 3)", 
    3: "it stood proud, half of it torn one leg breaks free running from the body mark of a Rebellion (hzfywt shift 5)",
    4: "lightning Zaps, thunder roars (rniiqj shift 9)",
    5: "First born of the 26th (cjru shift 7)"
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

        if user_input in [ans.lower() for ans in ANSWERS[current_loc]]:
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
            session['chances_left'] -= 1

            if session['chances_left'] > 0:
                responses.append({
                    "text": f"✗ Incorrect. {session['chances_left']} chances remaining.",
                    "type": "error"
                })
                session.modified = True
                return jsonify(responses)
            else:
                responses.append({
                    "text": "No chances left! Moving to next location...",
                    "type": "error"
                })

        alphabet_clue = ALPHABET_CLUES[current_loc]
        responses.append({
            "text": f"Alphabet clue: {alphabet_clue}",
            "type": "alphabet"
        })
        session['alphabet_clues'].append(alphabet_clue)

        session['current_location_index'] += 1

        if session['current_location_index'] < 5:
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
            final_points = 0
            for i in range(5):
                if user_guess[i] == FINAL_WORD[i]:
                    final_points += 2

            session['total_points'] += final_points

            responses.append({
                "text": f"Correct word: {FINAL_WORD}",
                "type": "system"
            })
            responses.append({
                "text": f"Final word points: {final_points}",
                "type": "success"
            })

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
