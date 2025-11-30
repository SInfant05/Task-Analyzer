# tasks/views.py
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from .scoring import analyze_tasks, get_top_suggestions, STRATEGY_WEIGHTS


@csrf_exempt
@require_http_methods(["POST"])
def analyze_tasks_view(request):
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        return JsonResponse({'status': 'ok'})
    
    try:
        # Parse request body
        body = json.loads(request.body.decode('utf-8'))
        
        # Extract tasks - handle both array and object formats
        if isinstance(body, list):
            tasks = body
            strategy = 'smart_balance'
        else:
            tasks = body.get('tasks', [])
            strategy = body.get('strategy', 'smart_balance')
        
        # Validate input
        if not tasks:
            return JsonResponse({
                'success': False,
                'error': 'No tasks provided. Please send a list of tasks.',
                'hint': 'Send {"tasks": [...]} or just [...]'
            }, status=400)
        
        if not isinstance(tasks, list):
            return JsonResponse({
                'success': False,
                'error': 'Tasks must be a list/array.',
            }, status=400)
        
        # Validate strategy
        if strategy not in STRATEGY_WEIGHTS:
            return JsonResponse({
                'success': False,
                'error': f'Invalid strategy: {strategy}',
                'valid_strategies': list(STRATEGY_WEIGHTS.keys())
            }, status=400)
        
        # Perform analysis
        result = analyze_tasks(tasks, strategy=strategy)
        
        return JsonResponse({
            'success': True,
            'data': result
        })
    
    except json.JSONDecodeError as e:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format',
            'details': str(e)
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Server error occurred',
            'details': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST", "OPTIONS"])
def suggest_tasks_view(request):
    """
    Get top 3 task suggestions with explanations.
    
    Endpoint: GET /api/tasks/suggest/
    
    For GET: Tasks should be passed as query parameter (limited use)
    For POST: Same format as /analyze/ endpoint
    
    This endpoint is designed to answer: "What should I work on TODAY?"
    
    Response:
    {
        "success": true,
        "data": {
            "suggestions": [...top 3 tasks...],
            "message": "Focus message",
            "summary": {...}
        }
    }
    """
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        return JsonResponse({'status': 'ok'})
    
    try:
        # Handle both GET and POST
        if request.method == 'POST':
            body = json.loads(request.body.decode('utf-8'))
            if isinstance(body, list):
                tasks = body
                strategy = 'smart_balance'
            else:
                tasks = body.get('tasks', [])
                strategy = body.get('strategy', 'smart_balance')
        else:
            # GET request - tasks from query param (for demo purposes)
            tasks_param = request.GET.get('tasks', '[]')
            try:
                tasks = json.loads(tasks_param)
            except:
                tasks = []
            strategy = request.GET.get('strategy', 'smart_balance')
        
        # Validate
        if not tasks:
            return JsonResponse({
                'success': False,
                'error': 'No tasks provided.',
                'hint': 'POST your tasks to this endpoint'
            }, status=400)
        
        # Get suggestions
        count = int(request.GET.get('count', 3))
        result = get_top_suggestions(tasks, count=min(count, 10), strategy=strategy)
        
        return JsonResponse({
            'success': True,
            'data': result
        })
    
    except json.JSONDecodeError as e:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format',
            'details': str(e)
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Server error occurred',
            'details': str(e)
        }, status=500)


# View to serve the frontend
class IndexView(TemplateView):
    template_name = 'index.html'