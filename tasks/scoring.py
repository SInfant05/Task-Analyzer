# tasks/scoring.py
"""
Smart Task Priority Scoring Engine

This module contains the core algorithm for calculating task priorities.
It considers multiple factors: urgency, importance, effort, and dependencies.

ALGORITHM DESIGN DECISIONS:
---------------------------
1. Each factor produces a score from 0-100
2. Final score is a weighted combination based on strategy
3. Higher score = Higher priority = Do this first

SCORING PHILOSOPHY:
------------------
- Urgency: Time-sensitive tasks shouldn't slip through the cracks
- Importance: User knows what matters most to their goals
- Effort: Quick wins build momentum and clear the backlog
- Dependencies: Unblocking other work has multiplicative value
"""

from datetime import date, datetime
from typing import Dict, Any, List, Optional, Tuple


# ============================================================
# CONFIGURATION: Weight distributions for different strategies
# ============================================================

STRATEGY_WEIGHTS = {
    'balanced': {  # ADD THIS ENTRY
        'urgency': 0.35,
        'importance': 0.30,
        'effort': 0.20,
        'dependency': 0.15,
        'description': 'Balanced consideration of all factors'
    },
    'smart_balance': {
        'urgency': 0.35,
        'importance': 0.30,
        'effort': 0.20,
        'dependency': 0.15,
        'description': 'Balanced consideration of all factors'
    },
    'deadline_driven': {
        'urgency': 0.55,
        'importance': 0.25,
        'effort': 0.10,
        'dependency': 0.10,
        'description': 'Prioritize tasks with approaching deadlines'
    },
    'high_impact': {
        'urgency': 0.20,
        'importance': 0.50,
        'effort': 0.15,
        'dependency': 0.15,
        'description': 'Focus on high-importance tasks first'
    },
    'fastest_wins': {
        'urgency': 0.20,
        'importance': 0.20,
        'effort': 0.45,
        'dependency': 0.15,
        'description': 'Prioritize quick tasks to build momentum'
    },
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def parse_date(date_input: Any) -> Optional[date]:
    """
    Safely parse a date from various input formats.
    
    Handles:
    - date objects (pass through)
    - datetime objects (extract date)
    - strings in multiple formats (YYYY-MM-DD, MM/DD/YYYY, etc.)
    - None values
    
    Args:
        date_input: The date value to parse
        
    Returns:
        A date object, or None if parsing fails
        
    Examples:
        >>> parse_date('2025-12-25')
        datetime.date(2025, 12, 25)
        >>> parse_date(None)
        None
    """
    if date_input is None:
        return None
    
    # Already a date object
    if isinstance(date_input, date) and not isinstance(date_input, datetime):
        return date_input
    
    # Datetime object - extract date
    if isinstance(date_input, datetime):
        return date_input.date()
    
    # String - try multiple formats
    if isinstance(date_input, str):
        date_formats = [
            '%Y-%m-%d',    # 2025-12-25
            '%m/%d/%Y',    # 12/25/2025
            '%d-%m-%Y',    # 25-12-2025
            '%Y/%m/%d',    # 2025/12/25
            '%d/%m/%Y',    # 25/12/2025
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_input.strip(), fmt).date()
            except ValueError:
                continue
    
    return None


def validate_task_data(task: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate and normalize task data, applying defaults for missing fields.
    
    Args:
        task: Raw task dictionary from user input
        
    Returns:
        Tuple of (normalized_task, warnings_list)
        
    Edge Cases Handled:
    - Missing title → "Untitled Task"
    - Missing due_date → None (handled in urgency calculation)
    - Missing importance → Default to 5
    - Missing estimated_hours → Default to 2
    - Importance out of range → Clamped to 1-10
    - Negative hours → Converted to positive
    """
    warnings = []
    normalized = {}
    
    # Title
    normalized['title'] = task.get('title', '').strip()
    if not normalized['title']:
        normalized['title'] = 'Untitled Task'
        warnings.append('Missing title - defaulted to "Untitled Task"')
    
    # Due date
    raw_date = task.get('due_date')
    normalized['due_date'] = parse_date(raw_date)
    if raw_date and normalized['due_date'] is None:
        warnings.append(f'Invalid date format: {raw_date}')
    
    # Importance (1-10)
    try:
        importance = int(task.get('importance', 5))
        if importance < 1:
            importance = 1
            warnings.append('Importance below 1 - clamped to 1')
        elif importance > 10:
            importance = 10
            warnings.append('Importance above 10 - clamped to 10')
        normalized['importance'] = importance
    except (ValueError, TypeError):
        normalized['importance'] = 5
        warnings.append('Invalid importance value - defaulted to 5')
    
    # Estimated hours
    try:
        hours = int(task.get('estimated_hours', 2))
        if hours <= 0:
            hours = abs(hours) if hours != 0 else 2
            warnings.append('Invalid hours - converted to positive')
        normalized['estimated_hours'] = hours
    except (ValueError, TypeError):
        normalized['estimated_hours'] = 2
        warnings.append('Invalid estimated_hours - defaulted to 2')
    
    # Dependencies
    deps = task.get('dependencies', [])
    if isinstance(deps, list):
        normalized['dependencies'] = deps
    else:
        normalized['dependencies'] = []
        warnings.append('Invalid dependencies format - defaulted to empty list')
    
    # Preserve original ID if present
    if 'id' in task:
        normalized['id'] = task['id']
    
    return normalized, warnings


# ============================================================
# SCORING FUNCTIONS (Each returns 0-100)
# ============================================================

def calculate_urgency_score(due_date: Optional[date]) -> Tuple[float, str]:
    """
    Calculate urgency score based on days until deadline.
    
    Scoring Logic:
    - Overdue: 100 points (maximum urgency!)
    - Due today: 95 points
    - Due tomorrow: 85 points
    - Due in 2-3 days: 70-80 points
    - Due in 4-7 days: 40-65 points
    - Due in 1-2 weeks: 20-35 points
    - Due later: 5-15 points
    - No due date: 30 points (medium urgency)
    
    Args:
        due_date: The task's deadline
        
    Returns:
        Tuple of (score, explanation)
    """
    if due_date is None:
        return 30.0, "No deadline set - medium urgency assumed"
    
    today = date.today()
    days_until = (due_date - today).days
    
    if days_until < 0:
        # OVERDUE!
        days_overdue = abs(days_until)
        score = min(100.0, 100.0 + (days_overdue * 0.5))
        return score, f"WARNING: OVERDUE by {days_overdue} day(s)!"
    
    if days_until == 0:
        return 95.0, "Due TODAY - urgent!"
    
    if days_until == 1:
        return 85.0, "Due tomorrow - very urgent"
    
    if days_until <= 3:
        score = 80.0 - ((days_until - 1) * 5)
        return score, f"Due in {days_until} days - urgent"
    
    if days_until <= 7:
        score = 65.0 - ((days_until - 3) * 6)
        return score, f"Due in {days_until} days - approaching"
    
    if days_until <= 14:
        score = 35.0 - ((days_until - 7) * 2)
        return score, f"Due in {days_until} days"
    
    if days_until <= 30:
        score = 20.0 - ((days_until - 14) * 0.5)
        return max(10.0, score), f"Due in {days_until} days - not urgent"
    
    return 5.0, f"Due in {days_until} days - low urgency"


def calculate_importance_score(importance: int) -> Tuple[float, str]:
    """
    Convert importance rating (1-10) to a weighted score.
    
    We use a slight exponential curve so that high-importance
    tasks (8-10) stand out more significantly.
    
    Args:
        importance: User rating 1-10
        
    Returns:
        Tuple of (score, explanation)
    """
    # Base conversion: 1-10 → 10-100
    base_score = importance * 10
    
    # Exponential boost for high importance (8-10)
    if importance >= 8:
        bonus = (importance - 7) ** 2 * 3  # 3, 12, 27 bonus
        base_score = min(100, base_score + bonus)
    
    # Descriptions
    if importance >= 9:
        desc = "Critical priority"
    elif importance >= 7:
        desc = "High priority"
    elif importance >= 5:
        desc = "Medium priority"
    elif importance >= 3:
        desc = "Low priority"
    else:
        desc = "Minimal priority"
    
    return float(base_score), desc


def calculate_effort_score(estimated_hours: int) -> Tuple[float, str]:
    """
    Calculate effort score - favoring quick wins.
    
    Philosophy: Small tasks build momentum and clear mental overhead.
    But we don't want to ONLY do easy work, so the bonus is moderate.
    
    Scoring:
    - Under 1 hour: 100 points (super quick win!)
    - 1-2 hours: 85 points
    - 2-4 hours: 65 points
    - 4-8 hours: 45 points
    - 8+ hours: 25 points (decreasing)
    
    Args:
        estimated_hours: Expected time to complete
        
    Returns:
        Tuple of (score, explanation)
    """
    if estimated_hours < 1:
        return 100.0, "Super quick task!"
    
    if estimated_hours <= 2:
        score = 85.0 - ((estimated_hours - 1) * 10)
        return score, f"Quick win ({estimated_hours}h)"
    
    if estimated_hours <= 4:
        score = 75.0 - ((estimated_hours - 2) * 10)
        return score, f"Moderate effort ({estimated_hours}h)"
    
    if estimated_hours <= 8:
        score = 55.0 - ((estimated_hours - 4) * 5)
        return score, f"Significant effort ({estimated_hours}h)"
    
    # Long tasks
    score = max(10.0, 28.0 - ((estimated_hours - 8) * 2))
    return score, f"Major effort ({estimated_hours}h)"


def calculate_dependency_score(
    task_id: Any,
    dependencies: List[Any],
    all_tasks: List[Dict],
    completed_ids: Optional[List[Any]] = None
) -> Tuple[float, str]:
    """
    Calculate dependency-based score.
    
    Two aspects:
    1. Is THIS task blocked by unfinished dependencies? (penalty)
    2. Does THIS task block other tasks? (bonus for being a blocker)
    
    Args:
        task_id: ID of current task
        dependencies: List of task IDs this task depends on
        all_tasks: All tasks in the analysis (to check what this blocks)
        completed_ids: IDs of completed tasks
        
    Returns:
        Tuple of (score, explanation)
    """
    if completed_ids is None:
        completed_ids = []
    
    score = 70.0  # Base score
    explanations = []
    
    # Check if this task is blocked
    if dependencies:
        unmet = [d for d in dependencies if d not in completed_ids]
        if unmet:
            # Blocked - reduce score significantly
            block_penalty = min(50, len(unmet) * 20)
            score -= block_penalty
            explanations.append(f"Blocked by {len(unmet)} task(s)")
        else:
            # All dependencies met!
            score += 10
            explanations.append("All dependencies complete")
    
    # Check if this task blocks others (makes it more valuable to complete)
    if task_id is not None:
        blocked_count = 0
        for task in all_tasks:
            task_deps = task.get('dependencies', [])
            if task_id in task_deps:
                blocked_count += 1
        
        if blocked_count > 0:
            blocker_bonus = min(30, blocked_count * 15)
            score += blocker_bonus
            explanations.append(f"Blocks {blocked_count} other task(s)")
    
    score = max(0, min(100, score))
    explanation = "; ".join(explanations) if explanations else "No dependencies"
    
    return score, explanation


# ============================================================
# CIRCULAR DEPENDENCY DETECTION
# ============================================================

def detect_circular_dependencies(tasks: List[Dict]) -> List[Dict]:
    """
    Detect circular dependencies in task list.
    
    Uses DFS (Depth-First Search) to find cycles.
    
    Args:
        tasks: List of task dictionaries with 'id' and 'dependencies'
        
    Returns:
        List of circular dependency warnings
    """
    # Build adjacency map
    task_map = {t.get('id'): t for t in tasks if t.get('id') is not None}
    
    warnings = []
    visited = set()
    rec_stack = set()
    
    def has_cycle(task_id, path):
        if task_id in rec_stack:
            cycle_path = path[path.index(task_id):] + [task_id]
            return cycle_path
        
        if task_id in visited:
            return None
        
        visited.add(task_id)
        rec_stack.add(task_id)
        
        task = task_map.get(task_id)
        if task:
            for dep_id in task.get('dependencies', []):
                result = has_cycle(dep_id, path + [task_id])
                if result:
                    return result
        
        rec_stack.remove(task_id)
        return None
    
    for task_id in task_map:
        if task_id not in visited:
            cycle = has_cycle(task_id, [])
            if cycle:
                warnings.append({
                    'type': 'circular_dependency',
                    'message': f'Circular dependency detected: {" → ".join(map(str, cycle))}',
                    'tasks': cycle
                })
    
    return warnings


# ============================================================
# MAIN SCORING FUNCTION
# ============================================================

def calculate_task_score(
    task: Dict[str, Any],
    all_tasks: List[Dict] = None,
    strategy: str = 'smart_balance',
    completed_ids: List[Any] = None
) -> Dict[str, Any]:
    """
    Calculate the complete priority score for a single task.
    
    This is the main entry point for scoring a task.
    
    Args:
        task: Task dictionary with title, due_date, importance, etc.
        all_tasks: All tasks (for dependency checking)
        strategy: Scoring strategy to use
        completed_ids: IDs of already completed tasks
        
    Returns:
        Dictionary containing:
        - All original task data
        - score: Final priority score
        - score_breakdown: Individual component scores
        - priority_level: HIGH/MEDIUM/LOW
        - explanations: Why each score was given
        - warnings: Any data issues found
    """
    if all_tasks is None:
        all_tasks = []
    if completed_ids is None:
        completed_ids = []
    
    # Validate and normalize input
    normalized, data_warnings = validate_task_data(task)
    
    # Get strategy weights
    weights = STRATEGY_WEIGHTS.get(strategy, STRATEGY_WEIGHTS['smart_balance'])
    
    # Calculate component scores
    urgency_score, urgency_exp = calculate_urgency_score(normalized['due_date'])
    importance_score, importance_exp = calculate_importance_score(normalized['importance'])
    effort_score, effort_exp = calculate_effort_score(normalized['estimated_hours'])
    dependency_score, dependency_exp = calculate_dependency_score(
        normalized.get('id'),
        normalized['dependencies'],
        all_tasks,
        completed_ids
    )
    
    # Calculate weighted final score
    final_score = (
        urgency_score * weights['urgency'] +
        importance_score * weights['importance'] +
        effort_score * weights['effort'] +
        dependency_score * weights['dependency']
    )
    
    # Determine priority level
    if final_score >= 75:
        priority_level = 'CRITICAL'
    elif final_score >= 60:
        priority_level = 'HIGH'
    elif final_score >= 40:
        priority_level = 'MEDIUM'
    elif final_score >= 25:
        priority_level = 'LOW'
    else:
        priority_level = 'MINIMAL'
    
    # Build result
    result = {
        **normalized,
        'due_date': normalized['due_date'].isoformat() if normalized['due_date'] else None,
        'score': round(final_score, 2),
        'priority_level': priority_level,
        'score_breakdown': {
            'urgency': round(urgency_score, 2),
            'importance': round(importance_score, 2),
            'effort': round(effort_score, 2),
            'dependency': round(dependency_score, 2),
        },
        'explanations': {
            'urgency': urgency_exp,
            'importance': importance_exp,
            'effort': effort_exp,
            'dependency': dependency_exp,
        },
        'strategy_used': strategy,
    }
    
    if data_warnings:
        result['warnings'] = data_warnings
    
    return result


# ============================================================
# BATCH ANALYSIS FUNCTIONS
# ============================================================

def analyze_tasks(
    tasks: List[Dict[str, Any]],
    strategy: str = 'balanced',
    completed_ids: List[Any] = None
) -> Dict[str, Any]:
    """
    Analyze and sort a list of tasks by priority.
    
    Args:
        tasks: List of task dictionaries
        strategy: Scoring strategy
        completed_ids: IDs of completed tasks
        
    Returns:
        Dictionary with:
        - tasks: Sorted list of scored tasks
        - summary: Statistics about the analysis
        - warnings: Any issues found
    """
    if not tasks:
        return {
            'tasks': [],
            'summary': {
                'total': 0,
                'message': 'No tasks to analyze'
            },
            'warnings': []
        }
    
    # Detect circular dependencies
    dep_warnings = detect_circular_dependencies(tasks)
    
    # Score all tasks
    scored_tasks = []
    for task in tasks:
        scored = calculate_task_score(
            task,
            all_tasks=tasks,
            strategy=strategy,
            completed_ids=completed_ids
        )
        scored_tasks.append(scored)
    
    # Sort by score (highest first)
    scored_tasks.sort(key=lambda x: x['score'], reverse=True)
    
    # Add rank
    for i, task in enumerate(scored_tasks, 1):
        task['rank'] = i
    
    # Generate summary
    total = len(scored_tasks)
    critical = sum(1 for t in scored_tasks if t['priority_level'] == 'CRITICAL')
    high = sum(1 for t in scored_tasks if t['priority_level'] == 'HIGH')
    overdue = sum(1 for t in scored_tasks if 'OVERDUE' in t['explanations'].get('urgency', ''))
    
    summary = {
        'total': total,
        'critical_count': critical,
        'high_count': high,
        'overdue_count': overdue,
        'strategy': strategy,
        'strategy_description': STRATEGY_WEIGHTS[strategy]['description'],
    }
    by_priority = {}
    for t in scored_tasks:
        level = t['priority_level']
        by_priority[level] = by_priority.get(level, 0) + 1

    summary = {
    'total': total,
    'by_priority': by_priority,
    'critical_count': by_priority.get('CRITICAL', 0),
    'high_count': by_priority.get('HIGH', 0),
    'overdue_count': overdue,
    'warnings': dep_warnings,
    'strategy': strategy,
    'strategy_description': STRATEGY_WEIGHTS.get(strategy, STRATEGY_WEIGHTS['balanced'])['description'],
    }

    return {
        'tasks': scored_tasks,
        'summary': summary,
        'warnings': dep_warnings,
    }


def get_top_suggestions(
    tasks: List[Dict[str, Any]],
    count: int = 3,
    strategy: str = 'smart_balance'
) -> Dict[str, Any]:
    """
    Get top task suggestions with detailed explanations.
    
    This powers the /api/tasks/suggest/ endpoint.
    
    Args:
        tasks: List of task dictionaries
        count: Number of suggestions (default 3)
        strategy: Scoring strategy
        
    Returns:
        Dictionary with top tasks and actionable advice
    """
    analysis = analyze_tasks(tasks, strategy=strategy)
    
    if not analysis['tasks']:
        return {
            'suggestions': [],
            'message': 'No tasks to suggest. Add some tasks first!',
            'summary': analysis['summary']
        }
    
    top_tasks = analysis['tasks'][:count]
    
    # Generate personalized explanations
    suggestions = []
    for i, task in enumerate(top_tasks, 1):
        # Build reason string
        reasons = []
        exp = task['explanations']
        
        if 'OVERDUE' in exp['urgency']:
            reasons.append(exp['urgency'])
        elif 'today' in exp['urgency'].lower():
            reasons.append("Due today!")
        elif 'tomorrow' in exp['urgency'].lower():
            reasons.append("Due tomorrow")
        
        if task['importance'] >= 8:
            reasons.append(f"High importance ({task['importance']}/10)")
        
        if task['estimated_hours'] <= 2:
            reasons.append(f"Quick win - only {task['estimated_hours']}h")
        
        if 'Blocks' in exp['dependency']:
            reasons.append(exp['dependency'])
        
        suggestion = {
            **task,
            'suggestion_rank': i,
            'why': reasons if reasons else ['Balanced priority based on all factors'],
            'action': generate_action_advice(task)
        }
        suggestions.append(suggestion)
    
    # Generate overall message
    summary = analysis['summary']
    if summary['overdue_count'] > 0:
        message = f"WARNING: You have {summary['overdue_count']} overdue task(s). Focus on these first!"
    elif summary['critical_count'] > 0:
        message = f"CRITICAL: {summary['critical_count']} critical task(s) need attention today."
    elif summary['high_count'] > 0:
        message = f"NOTICE: {summary['high_count']} high-priority task(s) to tackle."
    else:
        message = "No urgent tasks. Great time for deep work on important projects."
    
    return {
        'suggestions': suggestions,
        'message': message,
        'summary': summary,
        'all_tasks_analyzed': len(analysis['tasks']),
    }


def generate_action_advice(task: Dict) -> str:
    """Generate actionable advice based on task properties."""
    score = task['score']
    hours = task['estimated_hours']
    
    if 'OVERDUE' in task['explanations']['urgency']:
        return "URGENT: Complete this immediately; it's past the deadline."
    
    if score >= 75:
        if hours <= 2:
            return "High priority and quick — do this first thing."
        return "Block time today to make significant progress."
    
    if score >= 60:
        return "Schedule dedicated time for this task this week."
    
    if score >= 40:
        return "Keep on your radar — tackle after higher priorities."
    
    return "Lower priority — address when higher items are done."