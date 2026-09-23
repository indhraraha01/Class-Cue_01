#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================
user_problem_statement: "Add authentication (Signup/Login/Logout) + a Try Demo option to the existing Class Cue app, with strict per-user data isolation. Protect existing pages; demo uses built-in sample data (isolated, client-side); new registered users start with empty students/subjects; do not change unrelated existing functionality."

backend:
  - task: "Auth signup/login/me (JWT + bcrypt, UUIDs)"
    implemented: true
    working: "NA"
    file: "backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Added POST /api/auth/signup, POST /api/auth/login, GET /api/auth/me. bcrypt password hashing, PyJWT HS256 bearer tokens (7d), JWT_SECRET from env. Users stored in 'users' collection with UUID id, unique index on email. Verified basic flow via curl (signup/login/me/duplicate/invalid)."
  - task: "Per-user state isolation on /api/state"
    implemented: true
    working: "NA"
    file: "backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
        - working: "NA"
          agent: "main"
          comment: "GET/PUT /api/state now require auth (Depends get_current_user) and are scoped by user_id in new 'user_states' collection. Unauthenticated -> 401. New user gets empty AppState. Old shared app_state 'class-cue' doc left untouched (orphaned)."

frontend:
  - task: "Login/Signup/Logout + Try Demo gate"
    implemented: true
    working: "NA"
    file: "frontend/src/App.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Added Root auth gate + AuthScreen (login/signup toggle + Try Demo). Token in localStorage cc_token; demo flag in sessionStorage cc_demo. Logout button in topbar. App wrapped; unauthenticated users see AuthScreen. NOT YET UI-TESTED (awaiting user permission)."
  - task: "Demo isolation + empty new-user state"
    implemented: true
    working: "NA"
    file: "frontend/src/App.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Demo uses in-code seed, never calls /api/state (client-side only). Auth users load/persist via /api/state with Bearer header; removed the old seed-merge so new users stay empty. Added Dashboard empty-state guard so empty accounts don't crash."

metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 0
  run_ui: false

test_plan:
  current_focus:
    - "Auth signup/login/me (JWT + bcrypt, UUIDs)"
    - "Per-user state isolation on /api/state"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
    - agent: "main"
      message: "Please test the BACKEND auth + data isolation only. Focus: (1) signup creates user + returns token; new user's GET /api/state returns all-empty arrays. (2) login with correct/incorrect creds. (3) /api/auth/me with/without token. (4) /api/state GET/PUT require auth (401 without Bearer). (5) DATA ISOLATION: create User A, add data via PUT /api/state; create User B, confirm B's GET /api/state is empty and does not see A's data; confirm A still has its own data. (6) duplicate email signup -> 400. Pre-seeded test user: teacher@classcue.com / Test1234 (see /app/memory/test_credentials.md). Do NOT test frontend."
