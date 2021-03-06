import csv
import datetime
import os
import re

from flask import Flask, render_template, request, session
import flask
import content
import display.lists
import display.quiz
import display.tzahle


app = Flask(__name__)
# Secret key used for development, set it if one hasn't been set already
if app.secret_key is None:
    app.secret_key = os.environ.get('SECRET_KEY',
                                    '64b29b9e8f970f9fc7fbc10bc20585841162bd3fe1088b1a47b227e19620471c8b2e1a422bc3d7730864db8c3952b8ae')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dir/')
@app.route('/dir')
@app.route('/dir/<path:tag_path>')
def units_dir(tag_path=''):
    if tag_path == '' and 'q' in request.args:
        tag_path = request.args['q'].replace('-', '/')
    return render_template('lists.html',
                           c=content,
                           d=display.lists,
                           q=tag_path,
                           r='r' in request.args)


def sanitize_guess(guess: bytes) -> str:
    return re.sub(r'\s+', ' ', guess.decode('utf-8').translate(content.no_punc_trans).strip())


def build_answer_response(tag: content.Symbol, **kwargs) -> dict:
    tag_path = content.build_full_path(tag)
    return {'resp_type': 'answer', 'name': tag.name, 'path': tag_path, 'rel_path': flask.url_for('units_dir', tag_path=tag_path), **kwargs}


@app.route('/tzahle', methods=['GET', 'POST'])
def tzahle():
    if request.method == 'GET':
        session.setdefault('tzahle_guesses', [])
        return render_template('tzahle.html', c=content, d=display.tzahle)
    else:  # POST, player's guess checking
        tag = display.tzahle.get_tag_by_day_num(session.get('day_num', None))
        guess = sanitize_guess(request.data)
        answer_dict = build_answer_response(tag)
        guesses = session.get('tzahle_guesses') or []
        session['tzahle_guesses'] = guesses.append(guess)
        if guess in tag.alt_names:
            return answer_dict
        guess_words = guess.split(" ")
        # Collect all words in guess that are in any alt name of the tag
        words_in_answers = set([str(i) for i in range(len(guess_words)) for name in tag.alt_names if guess_words[i] in name])
        return {'resp_type': 'hint', 'word_indices': list(words_in_answers)}


@app.route('/tzahle/offset', methods=['POST'])
def tzahle_offset():
    try:
        offset = int(request.data)
    except ValueError:
        return 'invalid offset', 400
    player_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=offset)
    tag, day_num = display.tzahle.get_tag_by_date(player_time.date())
    session['day_num'] = day_num
    return content.build_full_image_path(tag)


@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    """A GET request returns the HTML page of the quiz.
    A POST request has the user's guess inside, or a "give up" message.
    Giving up is defined as sending the following string: giveup
    If the guess inside a request was right, the user's score (inside their session cookies) is incremented,
    and a JSON containing the tag's full name (key: name), path (key: path), relative URL to see the
    tag (key: rel_path), and new score (key: score) is returned for it to be shown to the player. The same JSON is
    returned when giving up, the only difference is that the score counter isn't incremented. If the guess is
    incorrect, the string "incorrect" is returned."""
    if request.method == 'GET':
        sess_guesses(clear=True)
        tag = display.quiz.random_tag()
        sess_tag_path(content.build_full_path(tag))
        return render_template('quiz.html',
                               c=content,
                               d=display.quiz,
                               tag=tag)
    else:  # POST
        tag_path = sess_tag_path()
        if tag_path is None:
            return 'bad path', 400
        tag = content.find_unit_tag(tag_path)
        if tag is None:
            return 'bad path', 400
        answer_dict = build_answer_response(tag, score=sess_score())

        guess = sanitize_guess(request.data)

        if guess == 'giveup':
            return answer_dict

        sess_guesses(add=guess)

        if guess in tag.alt_names:
            answer_dict['score'] += 1
            sess_score(answer_dict['score'])
            return answer_dict
        else:
            return 'incorrect'


@app.route('/quiz/objection', methods=['POST'])
def quiz_objection():
    """Sent when a quiz player thinks their guess(es) should be accepted as a valid answer.
    Uses the session to find out what the player's guesses were for what tag. No request body needed.
    The response body has a short explanation of the error if one occurred."""
    if 'tag_path' not in session or 'guesses' not in session:
        return 'no session', 400
    tag_path = sess_tag_path()
    guesses = sess_guesses()
    unit_tag = content.find_unit_tag(tag_path)
    if unit_tag is None:
        return 'bad path', 400
    if len(guesses) == 0:
        return 'no guesses', 400
    with open(os.path.join(app.root_path, 'objections.csv'), "a", encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow((tag_path, unit_tag.name, ';'.join(guesses)))
    return 'accepted', 200


def sess_guesses(add=None, clear=None):
    if clear:
        session['guesses'] = []
    elif not add:
        return session.get('guesses', [])
    else:
        guesses = session.get('guesses') or []
        guesses += [add]
        session['guesses'] = guesses


def sess_tag_path(new=None):
    if new is None:
        return session.get('tag_path', None)
    else:
        session['tag_path'] = new


def sess_score(new=None):
    if new is None:
        return session.get('score', 0)
    else:
        session['score'] = new


if __name__ == '__main__':
    app.run()
