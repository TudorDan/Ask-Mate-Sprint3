from flask import session

import database_common
import re
import datetime
import bcrypt


@database_common.connection_handler
def display_latest_five_questions(cursor):
    cursor.execute("""
                    SELECT title FROM question
                    ORDER BY submission_time DESC 
                    LIMIT 5;
                    """)
    questions = cursor.fetchall()
    return questions


@database_common.connection_handler
def get_all_questions_data(cursor):
    cursor.execute("""
                    SELECT * FROM question
                    ORDER BY submission_time;
                    """)
    all_questions = cursor.fetchall()
    return all_questions


@database_common.connection_handler
def sort_all_questions(cursor, order_by, order_direction):
    cursor.execute("""
                    SELECT * FROM question
                    ORDER BY {order_by} {order_direction};
                    """.format(**{'order_by': order_by, 'order_direction': order_direction.upper()}))
    questions = cursor.fetchall()
    return questions


@database_common.connection_handler
def search_question_pattern(cursor, pattern):
    cursor.execute("""
                    SELECT title FROM question
                    WHERE LOWER(title) LIKE LOWER(%(pattern)s)
                    UNION 
                    SELECT message FROM answer
                    WHERE LOWER(message) LIKE LOWER(%(pattern)s);
                    """,
                   {'pattern': '%' + pattern + '%'})
    search_results = cursor.fetchall()
    highlighted_list = []
    for dictionary in search_results:
        temp = re.sub(re.escape(pattern), f'<mark>{pattern}</mark>', dictionary['title'], flags=re.IGNORECASE)
        highlighted_list.append(temp)
    return highlighted_list


@database_common.connection_handler
def visit_specific_question_page(cursor, question_id):
    cursor.execute("""
                    UPDATE question
                    SET view_number = view_number + 1
                    WHERE id = %(question_id)s;
                    """,
                   {'question_id': question_id})


@database_common.connection_handler
def get_specific_question_data(cursor, question_id):
    cursor.execute("""
                    SELECT * FROM question
                    WHERE id = %(question_id)s;
                    """,
                   {'question_id': question_id})
    dictionary_data = cursor.fetchone()
    return dictionary_data


@database_common.connection_handler
def get_all_answers_for_specif_question(cursor, question_id):
    cursor.execute("""
                    SELECT * FROM answer
                    WHERE question_id = %(question_id)s
                    ORDER BY submission_time;
                    """,
                   {'question_id': question_id})
    answers_list = cursor.fetchall()
    return answers_list


@database_common.connection_handler
def add_question(cursor, title, message, image):
    time = datetime.datetime.now().strftime('%Y-%b-%d %H:%M:%S')
    cursor.execute("""
                    INSERT INTO question (submission_time, view_number, vote_number, title, message, image)
                    VALUES (%(time)s, %(view_number)s, %(vote_number)s, %(title)s, %(message)s, %(image)s);
                    """,
                   {'time': time,
                    'view_number': 0,
                    'vote_number': 0,
                    'title': title,
                    'message': message,
                    'image': image})
    return time


@database_common.connection_handler
def get_question_id_by_submission_time(cursor, submission_time):
    cursor.execute("""
                    SELECT * FROM question
                    WHERE submission_time = %(submission_time)s;
                    """,
                   {'submission_time': submission_time})
    question_dictionary = cursor.fetchone()
    return question_dictionary['id']


@database_common.connection_handler
def update_question(cursor, question_id, title, message, image):
    time = datetime.datetime.now().strftime('%Y-%b-%d %H:%M:%S')
    cursor.execute("""
                    UPDATE question
                    SET submission_time = %(submission_time)s, title = %(title)s, message = %(message)s, 
                    image = %(image)s
                    WHERE id = %(question_id)s;
                    """,
                   {'submission_time': time,
                    'title': title,
                    'message': message,
                    'image': image,
                    'question_id': question_id})


@database_common.connection_handler
def delete_question(cursor, question_id):
    # delete all question comments
    cursor.execute("""
                    DELETE FROM comment
                    WHERE question_id = %(question_id)s;
                    """,
                   {'question_id': question_id})
    # delete all answer comments
    cursor.execute("""
                    DELETE FROM comment
                    WHERE EXISTS(
                            SELECT comment.* FROM comment, answer
                            WHERE comment.answer_id = answer.id AND answer.question_id = %(question_id)s
                            );
                    """,
                   {'question_id': question_id})
    # delete all question answers
    cursor.execute("""
                    DELETE FROM answer
                    WHERE question_id = %(question_id)s;
                    """,
                   {'question_id': question_id})
    # finally, delete the actual question
    cursor.execute("""
                    DELETE FROM question
                    WHERE id = %(question_id)s;
                    """,
                   {'question_id': question_id})


@database_common.connection_handler
def add_answer_to_spec_question(cursor, question_id, message, image):
    time = datetime.datetime.now().strftime('%Y-%b-%d %H:%M:%S')
    cursor.execute("""
                    INSERT INTO answer (submission_time, vote_number, question_id, message, image)
                    VALUES (%(submission_time)s, %(vote_number)s, %(question_id)s, %(message)s, %(image)s);
                    """,
                   {'submission_time': time,
                    'vote_number': 0,
                    'question_id': question_id,
                    'message': message,
                    'image': image})


@database_common.connection_handler
def delete_answer(cursor, answer_id):
    cursor.execute("""
                    DELETE FROM comment
                    WHERE answer_id = %(answer_id)s;
                    """,
                   {'answer_id': answer_id})
    cursor.execute("""
                    DELETE FROM answer
                    WHERE id = %(answer_id)s;
                    """,
                   {'answer_id': answer_id})


@database_common.connection_handler
def get_question_id_by_answer_id(cursor, answer_id):
    cursor.execute("""
                    SELECT * FROM answer
                    WHERE id = %(answer_id)s;
                    """,
                   {'answer_id': answer_id})
    answer_dict = cursor.fetchone()
    return answer_dict['question_id']


@database_common.connection_handler
def question_vote_up(cursor, question_id):
    cursor.execute("""
                    UPDATE question
                    SET vote_number = vote_number + 1
                    WHERE id = %(question_id)s;
                    """,
                   {'question_id': question_id})
    # do not allow user to vote herself/himself
    cursor.execute("""
                    SELECT user_id FROM question
                    WHERE id = %(question_id)s;
                    """,
                   {'question_id': question_id})
    question_dict = cursor.fetchone()
    if question_dict['user_id'] != session['user_id']:
        cursor.execute("""
                        UPDATE users
                        SET reputation = reputation + 5
                        WHERE id = %(question_dict)s;
                        """,
                       {'question_dict': question_dict['user_id']})


@database_common.connection_handler
def question_vote_down(cursor, question_id):
    cursor.execute("""
                    UPDATE question
                    SET vote_number = vote_number - 1
                    WHERE id = %(question_id)s;
                    """,
                   {'question_id': question_id})
    # do not allow user to down vote herself/himself
    cursor.execute("""
                    SELECT user_id FROM question
                    WHERE id = %(question_id)s;
                    """,
                   {'question_id': question_id})
    question_dict = cursor.fetchone()
    if question_dict['user_id'] != session['user_id']:
        cursor.execute("""
                        UPDATE users
                        SET reputation = reputation - 2
                        WHERE id = %(question_dict)s;
                        """,
                       {'question_dict': question_dict['user_id']})


@database_common.connection_handler
def answer_vote_up(cursor, answer_id):
    cursor.execute("""
                    UPDATE answer
                    SET vote_number = vote_number + 1
                    WHERE id = %(answer_id)s;
                    """,
                   {'answer_id': answer_id})
    # do not allow user to vote herself/himself
    cursor.execute("""
                    SELECT user_id FROM answer
                    WHERE id = %(answer_id)s;
                    """,
                   {'answer_id': answer_id})
    question_dict = cursor.fetchone()
    if question_dict['user_id'] != session['user_id']:
        cursor.execute("""
                        UPDATE users
                        SET reputation = reputation + 10
                        WHERE id = %(question_dict)s;
                        """,
                       {'question_dict': question_dict['user_id']})


@database_common.connection_handler
def answer_vote_down(cursor, answer_id):
    cursor.execute("""
                    UPDATE answer
                    SET vote_number = vote_number - 1
                    WHERE id = %(answer_id)s;
                    """,
                   {'answer_id': answer_id})
    # do not allow user to down vote herself/himself
    cursor.execute("""
                    SELECT user_id FROM answer
                    WHERE id = %(answer_id)s;
                    """,
                   {'answer_id': answer_id})
    question_dict = cursor.fetchone()
    if question_dict['user_id'] != session['user_id']:
        cursor.execute("""
                        UPDATE users
                        SET reputation = reputation - 2
                        WHERE id = %(question_dict)s;
                        """,
                       {'question_dict': question_dict['user_id']})


@database_common.connection_handler
def get_one_answer_data(cursor, answer_id):
    cursor.execute("""
                    SELECT * FROM answer
                    WHERE id = %(answer_id)s;
                    """,
                   {'answer_id': answer_id})
    answer_dictionary = cursor.fetchone()
    return answer_dictionary


@database_common.connection_handler
def update_answer(cursor, answer_id, message, image):
    time = datetime.datetime.now().strftime('%Y-%b-%d %H:%M:%S')
    cursor.execute("""
                    UPDATE answer
                    SET submission_time = %(submission_time)s, message = %(message)s, image = %(image)s
                    WHERE id = %(answer_id)s;
                    """,
                   {'submission_time': time,
                    'message': message,
                    'image': image,
                    'answer_id': answer_id})


@database_common.connection_handler
def add_comment(cursor, question_id, message):
    time = datetime.datetime.now().strftime('%Y-%b-%d %H:%M:%S')
    cursor.execute("""
                    INSERT INTO comment (question_id, message, submission_time)
                    VALUES (%(question_id)s, %(message)s, %(submission_time)s);
                    """,
                   {'question_id': question_id,
                    'message': message,
                    'submission_time': time})


@database_common.connection_handler
def get_all_comments_for_specif_question(cursor, question_id):
    cursor.execute("""
                    SELECT * FROM comment
                    WHERE question_id = %(question_id)s
                    ORDER BY submission_time;
                    """,
                   {'question_id': question_id})
    comments_list = cursor.fetchall()
    return comments_list


@database_common.connection_handler
def add_comm_for_answer(cursor, answer_id, message):
    time = datetime.datetime.now().strftime('%Y-%b-%d %H:%M:%S')
    cursor.execute("""
                    INSERT INTO comment (answer_id, message, submission_time)
                    VALUES (%(answer_id)s, %(message)s, %(submission_time)s);
                    """,
                   {'answer_id': answer_id,
                    'message': message,
                    'submission_time': time})


@database_common.connection_handler
def get_answer_comments_by_question_id(cursor, question_id):
    cursor.execute("""
                    SELECT comment.* FROM comment, answer
                    WHERE comment.answer_id = answer.id AND answer.question_id = %(question_id)s;
                    """,
                   {'question_id': question_id})
    answer_comments_list = cursor.fetchall()
    return answer_comments_list


@database_common.connection_handler
def get_specific_comment(cursor, comment_id):
    cursor.execute("""
                    SELECT * FROM comment
                    WHERE id = %(comment_id)s;
                    """,
                   {'comment_id': comment_id})
    comment_dict = cursor.fetchone()
    return comment_dict


@database_common.connection_handler
def get_question_id_by_comment_id(cursor, comment_id):
    cursor.execute("""
                        SELECT question_id FROM comment
                        WHERE id = %(comment_id)s;
                        """,
                   {'comment_id': comment_id})
    question_id_dict = cursor.fetchone()

    if question_id_dict['question_id'] is None:
        cursor.execute("""
                        SELECT answer.question_id
                        FROM answer, comment
                        WHERE answer.id = comment.answer_id AND comment.id = %(comment_id)s;
                        """,
                       {'comment_id': comment_id})
        question_id_dict = cursor.fetchone()

    question_id = question_id_dict['question_id']
    return question_id


@database_common.connection_handler
def update_comment(cursor, comment_id, message):
    time = datetime.datetime.now().strftime('%Y-%b-%d %H:%M:%S')
    cursor.execute("""
                    UPDATE comment
                    SET edited_count = 0
                    WHERE id =  %(comment_id)s AND edited_count IS NULL;
                    """,
                   {'comment_id': comment_id})
    cursor.execute("""
                    UPDATE comment
                    SET message = %(message)s, submission_time = %(submission_time)s, edited_count = edited_count + 1
                    WHERE id = %(comment_id)s;
                    """,
                   {'message': message,
                    'submission_time': time,
                    'comment_id': comment_id})


@database_common.connection_handler
def delete_comment(cursor, comment_id):
    cursor.execute("""
                    DELETE FROM comment
                    WHERE id = %(comment_id)s;
                    """,
                   {'comment_id': comment_id})


@database_common.connection_handler
def get_tags_by_question_id(cursor, question_id):
    cursor.execute("""
                    SELECT tag.* FROM tag, question_tag
                    WHERE tag.id = question_tag.tag_id AND question_tag.question_id = %(question_id)s;
                    """,
                   {'question_id': question_id})
    tags_list = cursor.fetchall()
    return tags_list


@database_common.connection_handler
def add_tag(cursor, message, question_id):
    # insert the tag in the "tag" table
    cursor.execute("""
                    INSERT INTO tag (name)
                    VALUES (%(message)s);
                    """,
                   {'message': message})
    # get the new id for the new record in the "tag" table
    cursor.execute("""
                    SELECT id FROM tag
                    WHERE name = %(message)s;
                    """,
                   {'message': message})
    tag_id_dict = cursor.fetchone()
    tag_id = tag_id_dict['id']
    # connect the new tag with the question
    cursor.execute("""
                    INSERT INTO question_tag (question_id, tag_id)
                    VALUES (%(question_id)s, %(tag_id)s);
                    """,
                   {'question_id': question_id,
                    'tag_id': tag_id})


@database_common.connection_handler
def delete_tag(cursor, tag_id):
    cursor.execute("""
                    DELETE FROM question_tag
                    WHERE tag_id = %(tag_id)s;
                    """,
                   {'tag_id': tag_id})
    cursor.execute("""
                    DELETE FROM tag
                    WHERE id = %(tag_id)s;
                    """,
                   {'tag_id': tag_id})


def hash_password(plain_text_password):
    # By using bcrypt, the salt is saved into the hash itself
    hashed_bytes = bcrypt.hashpw(plain_text_password.encode('utf-8'), bcrypt.gensalt())
    return hashed_bytes.decode('utf-8')


@database_common.connection_handler
def add_new_user(cursor, username, hashed_password):
    dt = datetime.datetime.now().strftime('%Y-%b-%d %H:%M:%S')
    cursor.execute("""
                    INSERT INTO users (user_name, password, submission_time)
                    VALUES (%(username)s, %(hashed_password)s, %(dt)s);
                    """,
                   {'username': username,
                    'hashed_password': hashed_password,
                    'dt': dt})


@database_common.connection_handler
def check_user(cursor, username):
    cursor.execute("""
                    SELECT user_name FROM users
                    WHERE user_name = %(username)s;
                    """,
                   {'username': username})
    user_dict = cursor.fetchone()
    if user_dict is None:
        return True
    return False


@database_common.connection_handler
def obtain_all_users_data(cursor):
    cursor.execute("""
                    SELECT * FROM users
                    ORDER BY submission_time;
                    """)
    users_dict_list = cursor.fetchall()
    return users_dict_list


def verify_password(plain_text_password, hashed_password):
    hashed_bytes_password = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_text_password.encode('utf-8'), hashed_bytes_password)


@database_common.connection_handler
def verify_user(cursor, username, password):
    cursor.execute("""
                    SELECT password FROM users
                    WHERE user_name = %(username)s;
                    """,
                   {'username': username})
    user_dict = cursor.fetchone()
    if user_dict is None:
        return False
    else:
        result = verify_password(password, user_dict['password'])
    return result


@database_common.connection_handler
def get_user_id_by_username(cursor, username):
    cursor.execute("""
                    SELECT id FROM users
                    WHERE user_name = %(username)s;
                    """,
                   {'username': username})
    user_dict = cursor.fetchone()
    return user_dict['id']


@database_common.connection_handler
def get_questions_by_user_id(cursor, user_id):
    cursor.execute("""
                    SELECT id, title, message, image FROM question
                    WHERE user_id = %(user_id)s;
                    """,
                   {'user_id': user_id})
    questions_dict_list = cursor.fetchall()
    return questions_dict_list


@database_common.connection_handler
def get_answers_by_user_id(cursor, user_id):
    cursor.execute("""
                    SELECT answer.message, answer.image, answer.question_id, answer.accepted, answer.id, question.title
                    FROM answer 
                    JOIN question ON answer.question_id = question.id
                    WHERE answer.user_id = %(user_id)s;
                    """,
                   {'user_id': user_id})
    answers_dict_list = cursor.fetchall()
    return answers_dict_list


@database_common.connection_handler
def get_comments_by_user_id(cursor, user_id):
    cursor.execute("""
                    SELECT answer.message AS ans_mes, question.id, question.title, comment.message
                    FROM answer 
                    JOIN question ON answer.question_id = question.id
                    JOIN comment ON answer.id = comment.answer_id
                    WHERE comment.user_id = %(user_id)s
                    UNION
                    SELECT null, question.id, question.title, comment.message
                    FROM question 
                    JOIN comment ON question.id = comment.question_id
                    WHERE comment.user_id = %(user_id)s;
                    """,
                   {'user_id': user_id})
    comments_dict_list = cursor.fetchall()
    return comments_dict_list


@database_common.connection_handler
def mark_answer_as_accepted(cursor, answer_id):
    cursor.execute("""
                    UPDATE answer 
                    SET accepted = TRUE 
                    WHERE id = %(answer_id)s;
                    """,
                   {'answer_id': answer_id})
    # do not allow user to mark herself/himself
    cursor.execute("""
                    SELECT user_id FROM answer
                    WHERE id = %(answer_id)s;
                    """,
                   {'answer_id': answer_id})
    question_dict = cursor.fetchone()
    if question_dict['user_id'] != session['user_id']:
        cursor.execute("""
                        UPDATE users
                        SET reputation = reputation + 15
                        WHERE id = %(question_dict)s;
                        """,
                       {'question_dict': question_dict['user_id']})


@database_common.connection_handler
def unmark_accepted_answer(cursor, answer_id):
    cursor.execute("""
                    UPDATE answer 
                    SET accepted = FALSE 
                    WHERE id = %(answer_id)s;
                    """,
                   {'answer_id': answer_id})


@database_common.connection_handler
def get_all_user_data_by_username(cursor, username):
    cursor.execute("""
                        SELECT * FROM users
                        WHERE user_name = %(username)s;
                        """,
                   {'username': username})
    user_dict = cursor.fetchone()
    return user_dict


@database_common.connection_handler
def get_all_existing_tags(cursor):
    cursor.execute("""
                    SELECT name, COUNT(question_id) AS question_number
                    FROM tag 
                    JOIN question_tag ON tag.id = question_tag.tag_id
                    GROUP BY name;
                    """)
    tags_list_of_dicts = cursor.fetchall()
    return tags_list_of_dicts
