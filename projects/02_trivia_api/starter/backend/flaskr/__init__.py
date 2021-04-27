import os
from flask import (
  Flask, 
  request, 
  abort, 
  jsonify
)
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import (
  setup_db, 
  Question, 
  Category
)

RECORDS_PER_PAGE = 10

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  CORS(app, resources={r"/": {"origins": '*'}})
  
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
    return response

  @app.route('/')
  def index():
    return 'Hello Trivia'


  '''
  Get all available categories.
  '''
  @app.route('/categories', methods=['GET'])
  def get_categories():
    try:
      categories = Category.query.all()

      if categories is None:
        return not_found_error('No categories found.')

      formatted_categories = [category.format() for category in categories]
     

      return jsonify({
        'success': True,
        'categories': formatted_categories,
        'total_categories': len(formatted_categories)
      })
    except ValueError as e:
      print(e)
      unprocessable_error(error_message = 'Unable to process your request')



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
  def get_paginated_records(request, records):
    page = request.args.get('page', 1, type=int)
    start = (page -1) * RECORDS_PER_PAGE
    end = start + RECORDS_PER_PAGE
    formatted_records = [record.format() for record in records]
    return formatted_records[start:end]


  @app.route('/questions', methods = ['GET'])
  def get_questions():
    try:
      categories = Category.query.all()
      categories_dict = {}
      for category in categories:
        categories_dict[category.id] = category.type

      questions = Question.query.all()
      total_questions = len(questions)

      paginated_questions = get_paginated_records(request, questions)

      if questions is None:
        return not_found_error('No questions found.')

      return jsonify({
        'success': True,
        'questions': paginated_questions,
        'total_questions': total_questions,
        'categories': categories_dict,
        'current_category': None
      })
    except ValueError as e:
      print(e)
      unprocessable_error('Unable to process your request.')


  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<int:question_id>', methods = ['DELETE'])
  def delete_question(question_id):
    try:
      question = Question.query.filter(Question.id == question_id).one_or_none()
      if question is None:
        return not_found_error('Unable to delete question: Missing or invalid question ID.')
      
      question.delete()
      return jsonify({
        'success': True,
        'deleted': question_id
      })
    except ValueError as e:
      print(e)
      unprocessable_error('Unable to process your request.')


  '''
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  @app.route('/questions', methods = ['POST'])
  def add_question():
    try:
      requestJSON = request.get_json()

      if 'question' not in requestJSON.keys() or requestJSON['question'] is None:
        return not_found_error('Missing or invalid question text.')
      
      if 'answer' not in requestJSON.keys() or requestJSON['answer'] is None:
        return not_found_error('Missing or invalid answer text.')

      if 'difficulty' not in requestJSON.keys() or requestJSON['difficulty'] is None:
        return not_found_error('Missing or invalid difficulty value.')

      if 'category' not in requestJSON.keys() or requestJSON['category'] is None:
        return not_found_error('Missing or invalid category ID')

      question = Question(
        question = requestJSON['question'],
        answer = requestJSON['answer'],
        difficulty = requestJSON['difficulty'],
        category = requestJSON['category']
      )

      question.insert()

      return jsonify({
        'success': True,
        'created': question.format()
      })

    except ValueError as e:
      print(e)
      unprocessable_error('Unable to process your request.')


  '''
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
  @app.route('/questions/search', methods = ['POST'])
  def search_questions():
    requestJSON = request.get_json()
    search_term = requestJSON['searchTerm']

    questions = Question.query.filter(Question.question.ilike('%' + search_term + '%')).all()
    paginated_questions = get_paginated_records(request, questions)

    return jsonify({
      'success': True,
      'questions': paginated_questions,
      'total_questions': len(questions),
      'current_category': None
    })

  '''
  @TODO: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route('/categories/<int:category_id>/questions')
  def get_category_questions(category_id):
    try:
      category = Category.query.filter(Category.id == category_id).one_or_none()

      if category is None:
        return not_found_error('Missing or invalid category ID.')

      questions = Question.query.filter(Question.category == category.id).all()

      if questions is None:
        return not_found_error('No quesitons found for the selected category.')

      paginated_questions = get_paginated_records(request, questions)
      print(len(paginated_questions))

      return jsonify({
        'success': True,
        'questions': paginated_questions
      })
    except ValueError as e:
      print(e)
      unprocessable_error('Unable to process your request.')


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
  @app.route('/quizzes', methods = ['POST'])
  def play_quiz():
    try:
      requestJSON = request.get_json()
      print(requestJSON)
      previous_questions = requestJSON['previous_questions']
      quiz_category = requestJSON['quiz_category']
      category_id = quiz_category['id']
      
      if category_id == 0:
        questions = Question.query.filter(Question.id.notin_(previous_questions)).all()
      else:
        questions = Question.query.filter(
          Question.id.notin_(previous_questions),
          Question.category == category_id
        ).all()

      if len(questions) < 1:
        #return not_found_error(error_message = 'No questions found for the selected category')
        return jsonify({
          'success': True
        })

      question = random.choice(questions)

      if not question:
        return jsonify({
          'success': True,
          'question': ''
        })
      
      return jsonify({
        'success': True,
        'question': question.format(),
        'total_questions': len(questions)
      })

    except ValueError as e:
      print(e)
      unprocessable_error('Unable to process your request.')

  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  def error_handler_helper(error_message):
    return jsonify({
      'success': False,
      'message': str(error_message)
    })

  @app.errorhandler(400)
  def bad_request_error(error_message = 'Bad request'):
    return error_handler_helper(error_message, 400)

  @app.errorhandler(404)
  def not_found_error(error_message = 'Item not found.'):
    return error_handler_helper(error_message), 404

  @app.errorhandler(422)
  def unprocessable_error(error_message = 'Request is unprocessable'):
    return error_handler_helper(error_message), 422


  
  return app

    