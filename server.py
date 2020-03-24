import data_manager
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


@app.route('/')
@app.route('/search')
def index():
    questions = data_manager.display_latest_five_questions()
    query = False
    if request.args:
        pattern = request.args.get('q')
        search_results = data_manager.search_question_pattern(pattern)
        query = True
        return render_template('index.html', search_results=search_results, query=query, pattern=pattern)
    return render_template('index.html', questions=questions, query=query)


@app.route('/list')
def route_list():
    all_questions = data_manager.get_all_questions_data()
    if request.args:
        order_by = request.args.get('order_by')
        order_direction = request.args.get('order_direction')
        questions = data_manager.sort_all_questions(order_by, order_direction)
        return render_template('list.html', all_questions=questions, order_by=order_by,
                               order_direction=order_direction)
    return render_template('list.html', all_questions=all_questions)


@app.route('/question/<question_id>')
def route_question(question_id):
    data_manager.visit_specific_question_page(question_id)
    question_dictionary = data_manager.get_specific_question_data(question_id)
    question_answers_list = data_manager.get_all_answers_for_specif_question(question_id)

    question_comments_list = data_manager.get_all_comments_for_specif_question(question_id)

    answer_comments_list = data_manager.get_answer_comments_by_question_id(question_id)

    tags_list = data_manager.get_tags_by_question_id(question_id)
    return render_template('question.html', question_dictionary=question_dictionary,
                           question_answers_list=question_answers_list,
                           question_comments_list=question_comments_list, answer_comments_list=answer_comments_list,
                           tags_list=tags_list)


@app.route('/add_question', methods=['GET', 'POST'])
def route_add_question():
    if request.method == 'POST':
        title_post = request.form['form_question_title']
        message_post = request.form['form_question_message']
        post_image = None

        file_image = request.files['form_question_image']
        if file_image:
            post_image = file_image.filename

        submission_time = data_manager.add_question(title_post, message_post, post_image)
        question_id = data_manager.get_question_id_by_submission_time(submission_time)
        return redirect(url_for('route_question', question_id=question_id))
    return render_template('add_question.html')


@app.route('/question/<question_id>/edit', methods=['GET', 'POST'])
def route_edit_question(question_id):
    specific_question = data_manager.get_specific_question_data(question_id)
    if request.method == 'POST':
        post_title = request.form['edit_title']
        post_message = request.form['edit_message']
        post_image = None

        file_image = request.files['edit_question_image']
        if request.files:
            post_image = file_image.filename

        data_manager.update_question(question_id, post_title, post_message, post_image)
        return redirect(url_for('route_question', question_id=question_id))
    return render_template('edit_question.html', question_id=question_id, specific_question=specific_question)


@app.route('/question/<question_id>/delete')
def route_delete_question(question_id):
    data_manager.delete_question(question_id)
    return redirect('/list')


@app.route('/question/<question_id>/new-answer', methods=['GET', 'POST'])
def route_add_answer(question_id):
    specific_question = data_manager.get_specific_question_data(question_id)
    if request.method == 'POST':
        post_message = request.form['form_answer']
        post_image = None

        file_image = request.files['form_answer_image']
        if request.files:
            post_image = file_image.filename

        data_manager.add_answer_to_spec_question(question_id, post_message, post_image)
        return redirect(url_for('route_question', question_id=question_id))
    return render_template('answer.html', question_id=question_id, specific_question=specific_question)


@app.route('/answer/<answer_id>/delete')
def route_delete_answer(answer_id):
    question_id = data_manager.get_question_id_by_answer_id(answer_id)
    data_manager.delete_answer(answer_id)
    return redirect(url_for('route_question', question_id=question_id))


@app.route('/question/<question_id>/vote_up')
def route_question_vote_up(question_id):
    data_manager.question_vote_up(question_id)
    return redirect('/list')


@app.route('/question/<question_id>/vote_down')
def route_question_vote_down(question_id):
    data_manager.question_vote_down(question_id)
    return redirect('/list')


@app.route('/answer/<answer_id>/vote_up')
def route_answer_vote_up(answer_id):
    question_id = data_manager.get_question_id_by_answer_id(answer_id)
    data_manager.answer_vote_up(answer_id)
    return redirect(url_for('route_question', question_id=question_id))


@app.route('/answer/<answer_id>/vote_down')
def route_answer_vote_down(answer_id):
    question_id = data_manager.get_question_id_by_answer_id(answer_id)
    data_manager.answer_vote_down(answer_id)
    return redirect(url_for('route_question', question_id=question_id))


@app.route('/answer/<answer_id>/edit', methods=['GET', 'POST'])
def route_edit_answer(answer_id):
    answer_data = data_manager.get_one_answer_data(answer_id)
    question_id = data_manager.get_question_id_by_answer_id(answer_id)
    if request.method == 'POST':
        post_message = request.form['edit_message']
        post_image = None

        file_image = request.files['edit_answer_image']
        if request.files:
            post_image = file_image.filename

        data_manager.update_answer(answer_id, post_message, post_image)
        return redirect(url_for('route_question', question_id=question_id))
    return render_template('edit_answer.html', answer_id=answer_id, answer_data=answer_data)


@app.route('/question/<question_id>/new-comment', methods=['GET', 'POST'])
def route_add_comment(question_id):
    if request.method == 'POST':
        post_message = request.form['add_message']
        data_manager.add_comment(question_id, post_message)
        return redirect(url_for('route_question', question_id=question_id))
    return render_template('add_comment.html', question_id=question_id)


@app.route('/answer/<answer_id>/new-comment', methods=['GET', 'POST'])
def route_add_comm_to_answer(answer_id):
    question_id = data_manager.get_question_id_by_answer_id(answer_id)
    if request.method == 'POST':
        post_message = request.form['add_answer_message']
        data_manager.add_comm_for_answer(answer_id, post_message)
        return redirect(url_for('route_question', question_id=question_id))
    return render_template('add_comm_to_answer.html', answer_id=answer_id)


@app.route('/comment/<comment_id>/edit', methods=['GET', 'POST'])
def route_edit_comment(comment_id):
    comment_dict = data_manager.get_specific_comment(comment_id)
    if request.method == 'POST':
        post_message = request.form['edit_comment']
        data_manager.update_comment(comment_id, post_message)

        question_id = data_manager.get_question_id_by_comment_id(comment_id)
        return redirect(url_for('route_question', question_id=question_id))
    return render_template('edit_comment.html', comment_dict=comment_dict)


@app.route('/comments/<comment_id>/delete')
def route_delete_comment(comment_id):
    question_id = data_manager.get_question_id_by_comment_id(comment_id)
    data_manager.delete_comment(comment_id)
    return redirect(url_for('route_question', question_id=question_id))


@app.route('/question/<question_id>/new-tag', methods=['GET', 'POST'])
def route_add_tag(question_id):
    if request.method == 'POST':
        tag_message = request.form['add_tag']
        data_manager.add_tag(tag_message, question_id)
        return redirect(url_for('route_question', question_id=question_id))
    return render_template('add_tag.html', question_id=question_id)


@app.route('/question/<question_id>/tag/<tag_id>/delete')
def route_delete_tag(question_id, tag_id):
    data_manager.delete_tag(tag_id)
    return redirect(url_for('route_question', question_id=question_id))


@app.route('/registration', methods=['GET', 'POST'])
def route_add_user():
    user_ok = True
    if request.method == 'POST':
        username = request.form['form_username']
        password = request.form['form_password']

        user_ok = data_manager.check_user(username)

        if user_ok:
            hashed_password = data_manager.hash_password(password)
            data_manager.add_new_user(username, hashed_password)
            return redirect(url_for('index'))
        else:
            user_ok = False
    return render_template('add_new_user.html', user_ok=user_ok)


@app.route('/user-login', methods=['GET', 'POST'])
def route_login():
    user_ok = True
    if request.method == 'POST':
        username = request.form['form_username']
        password = request.form['form_password']

        user_ok = data_manager.verify_user(username, password)

        if user_ok:
            return redirect(url_for('route_list'))
        else:
            user_ok = False
    return render_template('login.html', user_ok=user_ok)


@app.route('/list-users')
def route_users_list():
    users_dict_list = data_manager.obtain_all_users_data()
    return render_template('list_users.html', users_dict_list=users_dict_list)


if __name__ == '__main__':
    app.run(debug=True)
