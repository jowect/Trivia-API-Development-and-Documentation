import os
import random
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask import (
    Flask,
    request,
    abort,
    jsonify
)
from models import (
    setup_db,
    Question,
    Category,
)

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
    cors = CORS(app,
                resources={r"/api/*": {"origins": "*"}},
                send_wildcard=True)  # from flask

    '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
    @app.after_request
    def after_request(response):
        response.headers.add(
            'Access-Control-Allow-Headers',
            'Content-Type, Authorization')
        response.headers.add(
            'Access-Control-Allow-Methods',
            'GET, POST, DELETE')

        return response

    '''
  @TODO:
  Create an endpoint to handle GET requests
  for all available categories.
  '''
    @app.route('/categories', methods=['GET'])
    def get_categories():
        categories = Category.query.all()
        formatted_categories = {}
        for category in categories:
            formatted_categories[category.id] = category.type

        return jsonify({
            'success': True,
            'categories': formatted_categories,
            'total_categories': len(categories)
        })
        

    '''
  @TODO:
  Create an endpoint to handle GET requests for questions,
  including pagination (every 10 questions).
  This endpoint should return a list of questions,
  number of total questions, current category, categories.

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions.
  '''
    # function to paginate 10 questions per page
    def paginate_questions(request, questions_list):
        page = request.args.get('page', 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE
        questions = [question.format() for question in questions_list]
        paginated_questions = questions[start:end]
        return paginated_questions

    # function to get all categories
    def get_category_dict():
        categories = {}
        for category in Category.query.all():
            categories[category.id] = category.type
        return categories

    # endpoint
    @app.route('/questions', methods=['GET'])
    def get_questions():
        questions_list = Question.query.all()
        paginated_questions = paginate_questions(request, questions_list)
        if len(paginated_questions) == 0:
            abort(404)
        return jsonify({
            'success': True,
            'questions': paginated_questions,
            'total_questions': len(questions_list),
            'categories': get_category_dict()
        })

    '''
  @TODO:
  Create an endpoint to DELETE question using a question ID.

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page.
  '''
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        error = False
        question = Question.query.get(question_id)
        question.delete()
        if error:
            abort(500)
        else:
            return jsonify({
                'success': True,
                'deleted_question': question_id
                })

    '''
  @TODO:
  Create an endpoint to POST a new question,
  which will require the question and answer text,
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab,
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.
  '''
    @app.route('/questions/add', methods=['POST'])
    def add_question():
        data = {
            'question': request.get_json()['question'],
            'answer': request.get_json()['answer'],
            'category': request.get_json()['category'],
            'difficulty': request.get_json()['difficulty']
        }

        question = Question(**data)
        question.insert()

        result = {'success': True}

        return jsonify(result)
        
    '''
  @TODO:
  Create a POST endpoint to get questions based on a search term.
  It should return any questions for whom the search term
  is a substring of the question.

  TEST: Search by any phrase. The questions list will update to include
  only question that include that string within their question.
  Try using the word "title" to start.

  '''
    @app.route('/questions/search', methods=['POST'])
    def search_question():
        body = request.get_json()
        search_term = body.get('searchTerm', None)

        try:
            if search_term:
                selection = Question.query.order_by(Question.id).filter(
                    Question.question.ilike('%{}%'.format(search_term)))
                current_questions = paginate_questions(request, selection)

                return jsonify({
                    'success': True,
                    'questions': current_questions,
                    'total_questions': len(selection.all()),
                    'current_category': None
                })
        except BaseException:
            abort(404)
    '''
  @TODO:
  Create a GET endpoint to get questions based on category.

  TEST: In the "List" tab / main screen, clicking on one of the
  categories in the left column will cause only questions of that
  category to be shown.
  '''
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_on_category(category_id):
        questions_list = Question.query.filter(
            Question.category == category_id).all()
        paginated_questions = paginate_questions(request, questions_list)
        if len(paginated_questions) == 0:
            abort(404)
        return jsonify({
            'success': True,
            'questions': paginated_questions,
            'total_questions': len(questions_list),
            'current_category': None
        })

    '''
  @TODO:
  Create a POST endpoint to get questions to play the quiz.
  This endpoint should take category and previous question parameters
  and return a random questions within the given category,
  if provided, and that is not one of the previous questions.

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not.
  '''
    @app.route('/quizzes', methods=['POST'])
    def get_question_for_quiz():
        body = request.get_json()
        previous_questions = body.get('previous_questions', [])
        quiz_category = body.get('quiz_category', None)
        try:
            category_id = int(quiz_category['id'])
            if quiz_category['id'] == 0:
                filter_questions = Question.query.all()
            else:
                filter_questions = Question.query.filter(
                    Question.category == category_id).all()

            if not filter_questions:
                return abort(422)

            data = []
            for i in filter_questions:
                if i.id not in previous_questions:
                    data.append(i.format())
            if len(data) > 0:
                result = random.choice(data)
                return jsonify({'success': True, 'question': result})
            else:
                return jsonify({'question': False})
        except BaseException:
            abort(422)

    '''
  @TODO:
  Create error handlers for all expected errors
  including 404 and 422.
  '''
    @app.errorhandler(400)
    def bad_request_error(error):
        return jsonify({
            'success': False,
            'error': 400,
            'message': "Bad Request"
        }), 400

    @app.errorhandler(401)
    def unauthorized_error(error):
        return jsonify({
            'success': False,
            'error': 401,
            'message': "Unauthorized"
        }), 401

    @app.errorhandler(403)
    def forbidden_error(error):
        return jsonify({
            'success': False,
            'error': 403,
            'message': "Forbidden"
        }), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': "Ressource Not Found"
        }), 404

    @app.errorhandler(405)
    def invalid_method_error(error):
        return jsonify({
            'success': False,
            'error': 405,
            'message': "Invalid Method"
        }), 405

    @app.errorhandler(409)
    def duplicate_resource_error(error):
        return jsonify({
            'success': False,
            'error': 409,
            'message': "Duplicate Resource"
        }), 409

    @app.errorhandler(422)
    def not_processable_error(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': "Not Processable"
        }), 422

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            'success': False,
            'error': 500,
            'message': "Server Error"
        }), 500

    return app

    if __name__ == '__main__':
        app.run()
