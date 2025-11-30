# tasks/tests.py

from django.test import TestCase, Client
from datetime import date, timedelta
import json

from .scoring import (
    calculate_urgency_score,
    calculate_importance_score,
    calculate_effort_score,
    calculate_task_score,
    analyze_tasks,
)


class ScoringTests(TestCase):
    """Test the scoring algorithm."""
    
    def test_urgency_overdue(self):
        # Overdue tasks should have high urgency.
        past = date.today() - timedelta(days=5)
        score, _ = calculate_urgency_score(past)
        self.assertGreaterEqual(score, 100)
    
    def test_urgency_today(self):
        # Tasks due today should have urgency score 95.
        today = date.today()
        score, _ = calculate_urgency_score(today)
        self.assertEqual(score, 95.0)
    
    def test_importance_scaling(self):
        # Importance should scale with rating.
        score_1, _ = calculate_importance_score(1)
        score_10, _ = calculate_importance_score(10)
        self.assertLess(score_1, score_10)
    
    def test_effort_quick_wins(self):
        # Shorter tasks should get higher effort scores.
        score_1h, _ = calculate_effort_score(1)
        score_8h, _ = calculate_effort_score(8)
        self.assertGreater(score_1h, score_8h)
    
    def test_complete_scoring(self):
        # Complete scoring should return all fields.
        task = {
            'title': 'Test Task',
            'due_date': date.today().isoformat(),
            'importance': 5,
            'estimated_hours': 2
        }
        result = calculate_task_score(task)
        self.assertIn('score', result)
        self.assertIn('priority_level', result)
    
    def test_tasks_sorted_by_score(self):
        # Analyze should return tasks sorted by score.
        tasks = [
            {'title': 'Low', 'due_date': (date.today() + timedelta(days=30)).isoformat(), 'importance': 2},
            {'title': 'High', 'due_date': date.today().isoformat(), 'importance': 9},
        ]
        result = analyze_tasks(tasks)
        self.assertEqual(result['tasks'][0]['title'], 'High')


class APIEndpointTests(TestCase):
    """Test API endpoints."""
    
    def setUp(self):
        self.client = Client()
    
    def test_analyze_endpoint(self):
        # POST /analyze/ should work with valid data.
        tasks = [
            {'title': 'Test', 'due_date': date.today().isoformat(), 'importance': 5}
        ]
        response = self.client.post(
            '/api/tasks/analyze/',
            data=json.dumps({'tasks': tasks}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
    
    def test_analyze_empty_list(self):
        # POST /analyze/ with empty list should return 400.
        response = self.client.post(
            '/api/tasks/analyze/',
            data=json.dumps({'tasks': []}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_suggest_endpoint(self):
        # POST /suggest/ should work with valid data.
        tasks = [
            {'title': 'Test', 'due_date': date.today().isoformat(), 'importance': 5}
        ]
        response = self.client.post(
            '/api/tasks/suggest/',
            data=json.dumps({'tasks': tasks}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
