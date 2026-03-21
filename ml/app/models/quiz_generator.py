"""
Dynamic Quiz Generator with Reasoning Traces
==============================================
Skill-aware adaptive questioning with difficulty scaling based on experience and claimed levels.
Every question includes "why" explanation tracing back to skill gap analysis.
"""

import json
import random
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
ONET_PATH = DATA_DIR / "onet_skills.json"

_taxonomy = None

def _load_taxonomy() -> dict:
    global _taxonomy
    if _taxonomy is None:
        for path in [ONET_PATH, Path("/app/data/onet_skills.json")]:
            if path.exists():
                with open(path) as f:
                    _taxonomy = json.load(f)
                return _taxonomy
        raise FileNotFoundError("onet_skills.json not found")
    return _taxonomy


# NEW: Question bank organized by skill -> difficulty -> questions
# This enables adaptive difficulty selection based on user profile
QUESTION_BANK_STRUCTURED = {
    "python": {
        1: [
            {
                "question": "What is a Python list?",
                "options": ["An ordered mutable collection", "A key-value store", "A single value", "An immutable sequence"],
                "answer": 0,
                "explanation": "A list is ordered and mutable in Python"
            },
            {
                "question": "What does `print(type([]) is list)` return?",
                "options": ["True", "False", "Error", "TypeError"],
                "answer": 0,
                "explanation": "The type() function returns the list class"
            }
        ],
        3: [
            {
                "question": "What does a Python decorator do?",
                "options": ["Wraps a function to modify its behavior", "Creates a new class", "Imports a module", "Handles exceptions"],
                "answer": 0,
                "explanation": "Decorators wrap functions to extend behavior"
            },
            {
                "question": "What is the time complexity of dictionary lookup?",
                "options": ["O(n)", "O(log n)", "O(1) amortized", "O(n log n)"],
                "answer": 2,
                "explanation": "Dictionaries use hashing for O(1) average lookups"
            }
        ],
        5: [
            {
                "question": "When would you use asyncio over threading?",
                "options": ["I/O bound concurrent tasks", "CPU bound parallel tasks", "Single threaded scripts", "Memory intensive operations"],
                "answer": 0,
                "explanation": "asyncio excels at I/O bound concurrency"
            },
            {
                "question": "What is a context manager (with statement)?",
                "options": ["Defined via __enter__ and __exit__", "A type of loop", "A module import", "An exception handler"],
                "answer": 0,
                "explanation": "Context managers ensure proper resource cleanup"
            }
        ]
    },
    "sql": {
        1: [
            {
                "question": "What does SELECT * FROM users return?",
                "options": ["All rows and columns from users table", "Only the first row", "Column names only", "Count of users"],
                "answer": 0,
                "explanation": "SELECT * retrieves all columns and rows"
            },
            {
                "question": "What SQL clause filters rows?",
                "options": ["SELECT", "WHERE", "ORDER BY", "GROUP BY"],
                "answer": 1,
                "explanation": "WHERE clause filters rows in a query"
            }
        ],
        3: [
            {
                "question": "Difference between INNER JOIN and LEFT JOIN?",
                "options": ["INNER returns matching rows only; LEFT returns all left rows", "They are identical", "LEFT JOIN is always faster", "INNER JOIN works on one table only"],
                "answer": 0,
                "explanation": "INNER JOIN returns only rows with matches in both tables"
            },
            {
                "question": "What does the HAVING clause do?",
                "options": ["Filters grouped results", "Filters rows before grouping", "Orders results", "Limits result count"],
                "answer": 0,
                "explanation": "HAVING filters groups created by GROUP BY"
            }
        ],
        5: [
            {
                "question": "How would you optimize a slow query on 10M rows?",
                "options": ["Add indexes on filtered and joined columns", "Increase server RAM only", "Use SELECT * everywhere", "Remove all WHERE clauses"],
                "answer": 0,
                "explanation": "Indexes dramatically speed up filtered queries"
            },
            {
                "question": "What does ACID ensure in database transactions?",
                "options": ["Atomicity, Consistency, Isolation, Durability", "Authentication, Control, Identity, Data", "Access, Count, Index, Deploy", "Aggregate, Connection, Integrity, Delta"],
                "answer": 0,
                "explanation": "ACID properties guarantee reliable transactions"
            }
        ]
    },
    "docker": {
        1: [
            {
                "question": "What is a Docker container?",
                "options": ["A lightweight isolated runtime environment", "A virtual machine", "A cloud server", "A type of database"],
                "answer": 0,
                "explanation": "Containers are lightweight isolated environments"
            },
            {
                "question": "What does `docker-compose up -d` do?",
                "options": ["Starts services in detached background mode", "Deletes all containers", "Downloads images", "Debugs containers"],
                "answer": 0,
                "explanation": "The -d flag runs containers in the background"
            }
        ],
        3: [
            {
                "question": "Difference between CMD and ENTRYPOINT in Dockerfile?",
                "options": ["ENTRYPOINT is fixed command; CMD provides defaults", "They are identical", "CMD runs at build time only", "ENTRYPOINT only works with volumes"],
                "answer": 0,
                "explanation": "ENTRYPOINT sets the executable; CMD sets default args"
            },
            {
                "question": "What is a Docker volume?",
                "options": ["Persistent storage outside containers", "A compressed archive", "A network interface", "A CPU limit"],
                "answer": 0,
                "explanation": "Volumes enable data persistence beyond container lifecycle"
            }
        ],
        5: [
            {
                "question": "How do you persist data between container restarts?",
                "options": ["Use named volumes or bind mounts", "Copy files manually each time", "Store data in environment variables", "Restart containers simultaneously"],
                "answer": 0,
                "explanation": "Named volumes persist independently of container lifecycle"
            },
            {
                "question": "What is a multi-stage Docker build used for?",
                "options": ["Reduce final image size by keeping build artifacts out", "Run tests after building", "Enable rolling deployments", "Create multiple containers"],
                "answer": 0,
                "explanation": "Multi-stage builds keep intermediate layers separate"
            }
        ]
    },
    "fastapi": {
        1: [
            {
                "question": "What is FastAPI primarily used for?",
                "options": ["Building REST APIs with Python", "Building mobile applications", "Database administration", "Frontend development"],
                "answer": 0,
                "explanation": "FastAPI is a modern Python web framework for APIs"
            },
            {
                "question": "How do you define a path parameter in FastAPI?",
                "options": ["Using {param_name} in the route path", "Using query strings", "Using headers", "Using cookies"],
                "answer": 0,
                "explanation": "Path parameters go in curly braces in the route"
            }
        ],
        3: [
            {
                "question": "What does Depends() do in FastAPI?",
                "options": ["Injects dependencies into route functions", "Creates a new API endpoint", "Validates the request body schema", "Handles HTTP exceptions"],
                "answer": 0,
                "explanation": "Depends() enables clean dependency injection"
            },
            {
                "question": "What type hint indicates request body in FastAPI?",
                "options": ["Pydantic BaseModel", "Dict", "String", "Integer"],
                "answer": 0,
                "explanation": "Pydantic models validate request data automatically"
            }
        ],
        5: [
            {
                "question": "How do you handle background tasks without blocking response?",
                "options": ["Use BackgroundTasks or Celery queue", "Use time.sleep() in the route", "Use synchronous blocking functions", "Use threading.Thread directly in routes"],
                "answer": 0,
                "explanation": "BackgroundTasks runs tasks after the response is sent"
            },
            {
                "question": "How do you implement pagination in FastAPI?",
                "options": ["Use query parameters for skip and limit", "Load all data and slice", "Use database offset only", "Manual array slicing"],
                "answer": 0,
                "explanation": "Query parameters enable flexible pagination"
            }
        ]
    },
    "machine_learning": {
        1: [
            {
                "question": "What is supervised learning?",
                "options": ["Learning from labeled input-output pairs", "Learning without any data", "Learning from rewards and penalties", "Learning from unlabeled data only"],
                "answer": 0,
                "explanation": "Supervised learning uses labeled training data"
            },
            {
                "question": "What is a feature in machine learning?",
                "options": ["An input variable used for prediction", "A model architecture", "A loss function", "An activation function"],
                "answer": 0,
                "explanation": "Features are the input variables for the model"
            }
        ],
        3: [
            {
                "question": "What is overfitting in machine learning?",
                "options": ["Model memorizes training data; fails on new data", "Model is too simple to learn patterns", "Model trains too slowly", "Model uses insufficient training data"],
                "answer": 0,
                "explanation": "Overfitting means poor generalization to unseen data"
            },
            {
                "question": "What is the purpose of a validation set?",
                "options": ["To tune hyperparameters and evaluate during training", "To train the model", "To deploy the model", "To collect more data"],
                "answer": 0,
                "explanation": "Validation set helps prevent overfitting during training"
            }
        ],
        5: [
            {
                "question": "When choose gradient boosting over neural networks?",
                "options": ["Tabular data with limited samples", "Large scale image classification", "Natural language processing tasks", "Video analysis at scale"],
                "answer": 0,
                "explanation": "Gradient boosting excels on structured tabular data"
            },
            {
                "question": "What is cross-validation used for?",
                "options": ["Estimate model performance on unseen data", "Speed up training", "Increase model accuracy", "Reduce memory usage"],
                "answer": 0,
                "explanation": "Cross-validation provides robust performance estimates"
            }
        ]
    },
    "react": {
        1: [
            {
                "question": "What is a React component?",
                "options": ["A reusable piece of UI", "A CSS stylesheet", "A database query", "A server endpoint"],
                "answer": 0,
                "explanation": "Components are reusable, independent UI pieces"
            },
            {
                "question": "What happens when state changes in React?",
                "options": ["Component re-renders", "Page reloads", "App crashes", "No change"],
                "answer": 0,
                "explanation": "State changes trigger component re-renders"
            }
        ],
        3: [
            {
                "question": "What is the purpose of useEffect hook?",
                "options": ["Handle side effects like API calls and subscriptions", "Create new components dynamically", "Style components inline", "Replace useState entirely"],
                "answer": 0,
                "explanation": "useEffect runs side effects after render"
            },
            {
                "question": "What is the virtual DOM?",
                "options": ["Lightweight copy of real DOM for efficient updates", "A hidden DOM element", "Server-side rendering technique", "CSS optimization"],
                "answer": 0,
                "explanation": "Virtual DOM is React's optimization mechanism"
            }
        ],
        5: [
            {
                "question": "When should you use useMemo vs useCallback?",
                "options": ["useMemo for values; useCallback for functions", "They are identical hooks", "useCallback for values; useMemo for functions", "Both only work in class components"],
                "answer": 0,
                "explanation": "useMemo memoizes values; useCallback memoizes functions"
            },
            {
                "question": "What is proper dependency array usage in useEffect?",
                "options": ["Include all external values used in the effect", "Always use empty array", "Never use dependency array", "Only include state variables"],
                "answer": 0,
                "explanation": "Dependencies control when effects re-run"
            }
        ]
    },
    "git": {
        1: [
            {
                "question": "What does git commit do?",
                "options": ["Saves staged changes to local repository", "Uploads code to GitHub", "Creates a new branch", "Merges two branches"],
                "answer": 0,
                "explanation": "git commit saves a snapshot of staged changes locally"
            },
            {
                "question": "What does git add do?",
                "options": ["Stages changes for commit", "Creates new file", "Deletes files", "Pushes to remote"],
                "answer": 0,
                "explanation": "git add stages changes for the next commit"
            }
        ],
        3: [
            {
                "question": "Difference between git merge and git rebase?",
                "options": ["Merge preserves history; rebase creates linear history", "They produce identical results", "Rebase is only for remote branches", "Merge deletes the source branch"],
                "answer": 0,
                "explanation": "Rebase rewrites commits for a cleaner linear history"
            },
            {
                "question": "What is a git stash used for?",
                "options": ["Temporarily save uncommitted changes", "Permanently delete changes", "Merge branches", "Create backups"],
                "answer": 0,
                "explanation": "git stash saves work-in-progress for later"
            }
        ],
        5: [
            {
                "question": "When would you use git cherry-pick?",
                "options": ["Apply specific commits from another branch", "Delete commits from history", "Merge entire branches together", "Reset to a previous commit"],
                "answer": 0,
                "explanation": "cherry-pick applies individual commits selectively"
            },
            {
                "question": "What is an interactive rebase used for?",
                "options": ["Reorder, edit, or squash commits before pushing", "Deploy code", "Backup repository", "List branches"],
                "answer": 0,
                "explanation": "Interactive rebase allows commit history refinement"
            }
        ]
    },
    "aws": {
        1: [
            {
                "question": "What is Amazon S3 used for?",
                "options": ["Object storage for files and data", "Running virtual servers", "Managing databases", "Domain name management"],
                "answer": 0,
                "explanation": "S3 is AWS scalable object storage service"
            },
            {
                "question": "What is AWS Lambda?",
                "options": ["Serverless compute service", "HTTP server", "Database engine", "Storage bucket"],
                "answer": 0,
                "explanation": "Lambda runs code without managing servers"
            }
        ],
        3: [
            {
                "question": "Difference between EC2 and Lambda?",
                "options": ["EC2 is always-on servers; Lambda is event-driven serverless", "They are the same service", "Lambda requires server management", "EC2 only runs Python code"],
                "answer": 0,
                "explanation": "Lambda runs code without managing servers"
            },
            {
                "question": "What is an AWS availability zone?",
                "options": ["Isolated location within a region", "A pricing tier", "A type of service", "A database type"],
                "answer": 0,
                "explanation": "AZs provide redundancy and high availability"
            }
        ],
        5: [
            {
                "question": "How would you design a highly available web app on AWS?",
                "options": ["Multi-AZ deployment with load balancer and auto-scaling", "Single EC2 instance with large storage", "One Lambda function per request", "RDS without read replicas"],
                "answer": 0,
                "explanation": "Multi-AZ with load balancing ensures high availability"
            },
            {
                "question": "What is AWS CloudFront used for?",
                "options": ["Content delivery via edge locations", "Running servers", "Database management", "Code repository"],
                "answer": 0,
                "explanation": "CloudFront is AWS's content delivery network"
            }
        ]
    },
    "communication": {
        1: [
            {
                "question": "What is active listening?",
                "options": ["Fully concentrating and responding to the speaker", "Talking more than listening", "Checking your phone while someone talks", "Interrupting to share your ideas"],
                "answer": 0,
                "explanation": "Active listening means full engagement with the speaker"
            },
            {
                "question": "Why is written communication important in tech?",
                "options": ["Creates records for clarity and reference", "It's not important", "Slower than talking", "Creates misunderstanding"],
                "answer": 0,
                "explanation": "Written docs provide clarity and accountability"
            }
        ],
        3: [
            {
                "question": "How do you handle disagreement in a team?",
                "options": ["Listen to all views and find common ground", "Ignore the disagreement and move on", "Always defer to the senior person", "Escalate immediately to management"],
                "answer": 0,
                "explanation": "Finding common ground resolves conflict constructively"
            },
            {
                "question": "How do you give constructive feedback?",
                "options": ["Be specific, timely, and solution-focused", "Focus on personal traits", "Do it publicly", "Wait until things are really bad"],
                "answer": 0,
                "explanation": "Good feedback is specific and actionable"
            }
        ],
        5: [
            {
                "question": "How do you communicate technical concepts to non-technical stakeholders?",
                "options": ["Use analogies and focus on business impact", "Use full technical jargon for accuracy", "Send a detailed technical document", "Avoid the conversation entirely"],
                "answer": 0,
                "explanation": "Analogies and business impact bridge technical gaps"
            },
            {
                "question": "How do you handle a meeting with many conflicting opinions?",
                "options": ["Seek shared goals and summarize areas of agreement", "Let the loudest person decide", "Cancel the meeting", "Skip the conflicting topics"],
                "answer": 0,
                "explanation": "Finding common ground moves teams forward"
            }
        ]
    },
    "agile": {
        1: [
            {
                "question": "What is a sprint in Agile?",
                "options": ["A fixed time period to complete planned work", "A type of software test", "A deployment pipeline", "A code review process"],
                "answer": 0,
                "explanation": "A sprint is a timeboxed period usually 1-4 weeks"
            },
            {
                "question": "What is a backlog item (user story)?",
                "options": ["A feature or task described from user perspective", "A bug report", "A risk", "A resource"],
                "answer": 0,
                "explanation": "User stories describe features from the user's viewpoint"
            }
        ],
        3: [
            {
                "question": "What happens in a sprint retrospective?",
                "options": ["Team reflects on what went well and what to improve", "Team plans the next sprint backlog", "Team demos work to stakeholders", "Team estimates story points"],
                "answer": 0,
                "explanation": "Retrospective focuses on process improvement"
            },
            {
                "question": "What is the purpose of story points?",
                "options": ["Estimate effort and complexity of tasks", "Track hours spent", "Measure velocity only", "Assign rewards"],
                "answer": 0,
                "explanation": "Story points help teams estimate task complexity"
            }
        ],
        5: [
            {
                "question": "How do you handle scope creep in an Agile project?",
                "options": ["Add to backlog and reprioritize with stakeholders", "Implement everything immediately", "Reject all new requirements", "Extend the sprint indefinitely"],
                "answer": 0,
                "explanation": "Backlog management keeps scope controlled in Agile"
            },
            {
                "question": "What is velocity in Agile teams?",
                "options": ["Amount of work completed per sprint", "Speed of deployment", "Number of bugs fixed", "Team size"],
                "answer": 0,
                "explanation": "Velocity helps predict sprint capacity"
            }
        ]
    },
    "pandas": {
        1: [
            {
                "question": "What is a Pandas DataFrame?",
                "options": ["A 2D labeled data structure like a spreadsheet", "A list of numbers", "A Python dictionary", "A database table"],
                "answer": 0,
                "explanation": "DataFrame is a 2D labeled data structure in pandas"
            }
        ],
        3: [
            {
                "question": "How do you handle missing values in a DataFrame?",
                "options": ["Use fillna() or dropna()", "Delete the entire column", "Convert to string 'None'", "Ignore them automatically"],
                "answer": 0,
                "explanation": "fillna() fills missing values; dropna() removes rows"
            }
        ],
        5: [
            {
                "question": "When would you use chunking with read_csv()?",
                "options": ["Processing files larger than available RAM", "Reading small CSV files faster", "Handling corrupted CSV files", "Reading multiple files at once"],
                "answer": 0,
                "explanation": "Chunking reads large files in manageable pieces"
            }
        ]
    },
    "nextjs": {
        1: [
            {
                "question": "What is Next.js?",
                "options": ["React framework for production applications", "A testing library", "A database", "A CSS framework"],
                "answer": 0,
                "explanation": "Next.js is a React framework with built-in optimization"
            }
        ],
        3: [
            {
                "question": "What is Server-Side Rendering (SSR)?",
                "options": ["Rendering on server before sending to client", "Rendering only on browser", "Rendering in database", "A type of caching"],
                "answer": 0,
                "explanation": "SSR improves initial page load and SEO"
            }
        ],
        5: [
            {
                "question": "What is Incremental Static Regeneration?",
                "options": ["Revalidate static pages on-demand after a time period", "Regenerate all files on every request", "Static files that never change", "Dynamic server rendering"],
                "answer": 0,
                "explanation": "ISR combines static benefits with dynamic freshness"
            }
        ]
    },
    "nodejs": {
        1: [
            {
                "question": "What is Node.js?",
                "options": ["JavaScript runtime for server-side development", "A database", "A frontend framework", "A testing tool"],
                "answer": 0,
                "explanation": "Node.js allows JavaScript to run outside browsers"
            }
        ],
        3: [
            {
                "question": "What is the event loop in Node.js?",
                "options": ["Mechanism handling async operations by queuing callbacks", "A type of for-loop", "A debugging tool", "Package manager feature"],
                "answer": 0,
                "explanation": "The event loop enables non-blocking I/O"
            }
        ],
        5: [
            {
                "question": "What is a cluster in Node.js?",
                "options": ["Spawn multiple processes for multi-core CPU utilization", "A database concept", "A networking protocol", "A security feature"],
                "answer": 0,
                "explanation": "Clusters enable Node.js to use multiple CPU cores"
            }
        ]
    },
    "redis": {
        1: [
            {
                "question": "What is Redis?",
                "options": ["In-memory data structure store", "SQL database", "Message queue only", "File storage"],
                "answer": 0,
                "explanation": "Redis is an in-memory key-value store"
            }
        ],
        3: [
            {
                "question": "What data structures does Redis support?",
                "options": ["Strings, Lists, Sets, Hashes, Sorted Sets", "Only strings", "Only tables", "Only databases"],
                "answer": 0,
                "explanation": "Redis supports rich data structures"
            }
        ],
        5: [
            {
                "question": "How do you implement caching with Redis?",
                "options": ["Check cache before DB, update on miss", "Always use database", "Store everything forever", "Never update cache"],
                "answer": 0,
                "explanation": "Cache-aside pattern optimizes data access"
            }
        ]
    }
}


# Map of experience to difficulty
EXPERIENCE_MAP = {
    "Fresher": 0,
    "0": 0,
    "1": 1,
    "2": 1,
    "3": 2,
    "4": 2,
    "5": 3,
    "6": 3,
    "7": 4,
    "8": 4,
    "9": 4,
    "10": 5,
    "Not detected": 1,
}


def get_difficulty_level(current_level: int, experience: str) -> int:
    """
    Determine appropriate question difficulty based on:
    1. User's claimed skill level in this skill
    2. Overall years of experience
    
    Returns difficulty 1-5
    """
    exp_score = EXPERIENCE_MAP.get(str(experience), 1)
    combined = current_level + exp_score
    
    if combined <= 2:
        return 1
    elif combined <= 5:
        return 3
    else:
        return 5


def generate_dynamic_quiz(
    verified_skills: dict,
    role: str,
    experience: str = "Not detected",
    max_questions: int = 10
) -> list:
    """
    NEW: Generate adaptive quiz dynamically based on skill gaps and experience
    
    Args:
        verified_skills: {skill: {level: int}} or {skill: int}
        role: Target role (e.g., "backend_engineer")
        experience: Years of experience (default "Not detected")
        max_questions: Hard cap at 10 questions
    
    Returns:
        Questions list with reasoning trace ("why" field)
    """
    max_questions = min(max_questions, 10)

    taxonomy = _load_taxonomy()
    onet_data = taxonomy
    
    # Get role definition
    role_data = onet_data.get("roles", {}).get(role, {})
    required_skills = role_data.get("required_skills", role_data.get("skills", {}))
    importance_weights = role_data.get("importance_weights", {})
    
    # Build gap profile
    skill_gaps = []
    for skill, required_level_data in required_skills.items():
        # Parse required level
        if isinstance(required_level_data, dict):
            required_level = int(required_level_data.get("level", 0))
        else:
            required_level = int(required_level_data)
        
        # Parse current level
        current_level_data = verified_skills.get(skill, {})
        if isinstance(current_level_data, dict):
            current_level = int(current_level_data.get("level", 0))
        else:
            current_level = int(current_level_data) if current_level_data else 0
        
        gap = required_level - current_level
        importance = float(importance_weights.get(skill, 0.5))
        
        # Only quiz skills with gaps, available questions, and role relevance.
        if gap > 0 and skill in QUESTION_BANK_STRUCTURED and importance >= 0.40:
            priority = round((gap / 5) * 0.6 + importance * 0.4, 4)
            skill_gaps.append({
                "skill": skill,
                "gap": gap,
                "importance": importance,
                "current_level": current_level,
                "required_level": required_level,
                "priority": priority
            })
    
    # Sort by priority — critical gaps first
    skill_gaps.sort(key=lambda x: x["priority"], reverse=True)
    
    questions = []
    used_per_skill = {}
    
    for gap_info in skill_gaps:
        if len(questions) >= max_questions:
            break
        
        skill = gap_info["skill"]
        importance = gap_info["importance"]
        current_level = gap_info["current_level"]
        
        # Critical skills (importance >= 0.85) get 2 questions, others get 1
        num_q = 2 if importance >= 0.85 else 1
        
        # Determine difficulty
        difficulty = get_difficulty_level(current_level, experience)
        
        # Get questions at requested difficulty, fallback to available
        available = QUESTION_BANK_STRUCTURED.get(skill, {}).get(difficulty, [])
        if not available:
            # Fallback: try other difficulties
            for fallback_diff in [3, 1, 5]:
                available = QUESTION_BANK_STRUCTURED.get(skill, {}).get(fallback_diff, [])
                if available:
                    difficulty = fallback_diff
                    break
        
        if not available:
            continue
        
        used = used_per_skill.get(skill, 0)
        for q in available[used: used + num_q]:
            if len(questions) >= max_questions:
                break
            
            questions.append({
                "skill": skill,
                "difficulty": difficulty,
                "question": q["question"],
                "options": q["options"],
                "answer": q["answer"],
                "explanation": q["explanation"],
                "why": (
                    f"Testing {skill.replace('_', ' ')} — you scored "
                    f"{gap_info['current_level']}/5 but "
                    f"{role.replace('_', ' ').title()} requires "
                    f"{gap_info['required_level']}/5. Priority: "
                    f"{gap_info['importance']*100:.0f}% importance for this role."
                )
            })
        
        used_per_skill[skill] = used + num_q
    
    return questions[:max_questions]


# Keep backward compatibility with existing quiz flow
def generate_quiz(
    skill_ids: list[str],
    questions_per_skill: int = 2,
    max_questions: int = 10,
    experience_years: int | None = None,
    claimed_levels: dict[str, int] | None = None,
) -> dict:
    """
    Legacy quiz generation for backward compatibility.
    This is called by backend when using the old quiz flow.
    """
    taxonomy = _load_taxonomy()
    questions = []
    q_id = 0
    claimed_levels = claimed_levels or {}
    
    if experience_years is None:
        min_diff, max_diff = 1, 4
        target_diff = 2
    elif experience_years <= 1:
        min_diff, max_diff = 1, 2
        target_diff = 2
    elif experience_years <= 4:
        min_diff, max_diff = 2, 3
        target_diff = 3
    else:
        min_diff, max_diff = 3, 5
        target_diff = 4
    
    for skill_id in skill_ids:
        skill_questions = QUESTION_BANK_STRUCTURED.get(skill_id, {})
        if not skill_questions:
            continue
        
        # Adapt difficulty by both overall experience and claimed skill level
        skill_target = claimed_levels.get(skill_id)
        if isinstance(skill_target, int):
            target = max(1, min(5, round((target_diff + skill_target) / 2)))
        else:
            target = target_diff
        
        # Collect all questions in difficulty band
        candidate_pool = []
        for diff, questions_at_diff in skill_questions.items():
            if min_diff <= diff <= max_diff:
                candidate_pool.extend(questions_at_diff)
        
        if not candidate_pool:
            # Fallback to any available questions
            for diff, q_list in skill_questions.items():
                candidate_pool.extend(q_list)
        
        if not candidate_pool:
            continue
        
        random.shuffle(candidate_pool)
        candidate_pool.sort(key=lambda q: abs(q.get("difficulty", 3) - target))
        selected = candidate_pool[:min(questions_per_skill, len(candidate_pool))]
        
        for q in selected:
            skill_name = taxonomy.get("skills", {}).get(skill_id, {}).get("name", skill_id)
            questions.append({
                "id": f"q_{q_id}",
                "skill_id": skill_id,
                "skill_name": skill_name,
                "question": q["question"],
                "options": q["options"],
                "correct_index": q["answer"],
                "difficulty": q.get("difficulty", 2),
                "why": f"Testing {skill_id} — level {skill_target}/5 claimed"
            })
            q_id += 1
    
    if len(questions) > max_questions:
        random.shuffle(questions)
        questions = questions[:max_questions]
    
    quiz_id = f"quiz_{''.join(random.choices('abcdef0123456789', k=8))}"
    
    return {
        "quiz_id": quiz_id,
        "questions": questions,
        "total_questions": len(questions),
    }


def grade_quiz(questions: list[dict], answers: dict[str, int]) -> dict:
    """
    Grade quiz responses and return verified skill levels.
    
    Args:
        questions: The generated quiz questions
        answers: Map of question_id -> selected_option_index
    
    Returns:
        Skill scores with verified levels
    """
    skill_results: dict[str, dict] = {}
    
    for q in questions:
        sid = q["skill_id"] if "skill_id" in q else q.get("skill")
        if sid not in skill_results:
            skill_results[sid] = {"correct": 0, "total": 0, "difficulty_sum": 0}
        
        skill_results[sid]["total"] += 1
        user_answer = answers.get(q.get("id", ""))
        correct_index = q.get("correct_index", q.get("answer", 0))
        
        if user_answer == correct_index:
            skill_results[sid]["correct"] += 1
            skill_results[sid]["difficulty_sum"] += q.get("difficulty", 2)
    
    total_correct = sum(r["correct"] for r in skill_results.values())
    total_questions = sum(r["total"] for r in skill_results.values())
    
    skill_scores = {}
    for sid, result in skill_results.items():
        if result["total"] == 0:
            verified_level = 1
        else:
            accuracy = result["correct"] / result["total"]
            avg_difficulty = (
                result["difficulty_sum"] / result["correct"]
                if result["correct"] > 0
                else 1
            )
            verified_level = min(5, max(1, round(accuracy * avg_difficulty)))
        
        skill_scores[sid] = {
            "correct": result["correct"],
            "total": result["total"],
            "verified_level": verified_level,
        }
    
    return {
        "total_score": total_correct,
        "max_score": total_questions,
        "skill_scores": skill_scores,
    }
