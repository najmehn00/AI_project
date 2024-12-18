from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import threading
from sqlalchemy.sql import func

app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///api_requests.db'  # You can change to PostgreSQL or MySQL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Model
class APIRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prompt = db.Column(db.Text, nullable=False)
    model = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    response = db.Column(db.Text, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=func.now())
    completed_at = db.Column(db.DateTime, nullable=True)

# Create database tables
with app.app_context():
    db.create_all()

def process_api_request(request_id, model, prompt):
    """
    Process the API request in a background thread
    """
    with app.app_context():
        try:
            headers = {"Content-Type": "application/json"}
            payload = {"model": model, "prompt": prompt}
            
            # Make API request with timeout
            response = requests.post(
                'http://87.107.110.5:11434/api/generate ',
                json=payload,
                headers=headers,
                timeout=30  # 30 seconds timeout
            )
            response.raise_for_status()
            
            # Update database with success
            api_request = db.session.get(APIRequest, request_id)  # Updated here
            if api_request:
                api_request.status = 'completed'
                api_request.response = str(response.json())
                api_request.completed_at = datetime.utcnow()
                db.session.commit()
            
        except requests.exceptions.Timeout:
            # Handle timeout error
            api_request = db.session.get(APIRequest, request_id)  # Updated here
            if api_request:
                api_request.status = 'failed'
                api_request.error_message = 'Request timed out'
                api_request.completed_at = datetime.utcnow()
                db.session.commit()
            
        except Exception as e:
            # Handle other errors
            api_request = db.session.get(APIRequest, request_id)  # Updated here
            if api_request:
                api_request.status = 'failed'
                api_request.error_message = str(e)
                api_request.completed_at = datetime.utcnow()
                db.session.commit()


@app.route('/generate', methods=['POST'])
def generate_text():
    try:
        data = request.get_json()
        model = data.get("model", "llama3")
        prompt = data.get("prompt", "")
        
        # Create database entry
        api_request = APIRequest(
            prompt=prompt,
            model=model,
            status='pending'
        )
        db.session.add(api_request)
        db.session.commit()
        
        # Start background processing
        thread = threading.Thread(
            target=process_api_request,
            args=(api_request.id, model, prompt)
        )
        thread.start()
        
        # Return immediate response with request ID
        return jsonify({
            "request_id": api_request.id,
            "status": "pending",
            "message": "Request is being processed"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status/<int:request_id>', methods=['GET'])
def get_status(request_id):
    """
    Check the status of a specific request
    """
    try:
        api_request = APIRequest.query.get(request_id)
        if not api_request:
            return jsonify({"error": "Request not found"}), 404
            
        response = {
            "request_id": api_request.id,
            "status": api_request.status,
            "created_at": api_request.created_at.isoformat(),
            "completed_at": api_request.completed_at.isoformat() if api_request.completed_at else None
        }
        
        if api_request.status == 'completed':
            response["response"] = api_request.response
        elif api_request.status == 'failed':
            response["error_message"] = api_request.error_message
            
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/requests', methods=['GET'])
def get_all_requests():
    """
    Get all requests with optional filtering
    """
    try:
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        query = APIRequest.query
        if status:
            query = query.filter_by(status=status)
            
        requests = query.order_by(APIRequest.created_at.desc())\
                       .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            "requests": [{
                "id": req.id,
                "prompt": req.prompt,
                "model": req.model,
                "status": req.status,
                "created_at": req.created_at.isoformat(),
                "completed_at": req.completed_at.isoformat() if req.completed_at else None
            } for req in requests.items],
            "total": requests.total,
            "pages": requests.pages,
            "current_page": requests.page
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)