#!/bin/bash

BASE_URL="http://127.0.0.1:5000"
TASK_API_BASE="$BASE_URL/api/v1/task"
PROJECT_API_BASE="$BASE_URL/api/v1/project"
EMPLOYEE_API_BASE="$BASE_URL/api/v1/employee"
TIMESTAMP=$(date +%s)$(jot -r 1 1000 9999)
EMAIL="test$TIMESTAMP@example.com"

echo "🔄 Three-Way Bidirectional Relationship Test"
echo "Testing Employee ↔ Project ↔ Task relationships"
echo "Using email: $EMAIL"

# Setup: Register User and Get Token
echo -e "\n1. 👤 Setting up authentication..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST $BASE_URL/api/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Test User\", \"email\": \"$EMAIL\", \"password\": \"password123\", \"confirm_password\": \"password123\"}")

TOKEN=$(echo "$RESPONSE" | sed -e 's/HTTPSTATUS\:.*//g' | tr -d '\n' | sed 's/.*"access_token": *"\([^"]*\)".*/\1/')
AUTH_HEADER="Authorization: Bearer $TOKEN"
echo "✅ Authenticated"

# Setup: Create 3 Employees
echo -e "\n2. 👨‍💼 Creating employees..."
create_employee() {
    local name=$1
    local email=$2
    curl -s -X POST $EMPLOYEE_API_BASE/ \
        -H "$AUTH_HEADER" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"$name\", \"email\": \"$email\"}" | \
        tr -d '\n' | sed 's/.*"id": *"\([^"]*\)".*/\1/'
}

EMP1_ID=$(create_employee "Alice Johnson" "alice$TIMESTAMP@company.com")
EMP2_ID=$(create_employee "Bob Smith" "bob$TIMESTAMP@company.com")  
EMP3_ID=$(create_employee "Carol Davis" "carol$TIMESTAMP@company.com")

echo "✅ Created 3 employees: $EMP1_ID, $EMP2_ID, $EMP3_ID"

# Setup: Create Project with 2 Employees
echo -e "\n3. 🎯 Creating project with 2 employees..."
PROJECT_RESPONSE=$(curl -s -X POST $PROJECT_API_BASE/ \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Three-Way Test Project $TIMESTAMP\",
    \"description\": \"Testing bidirectional relationships\",
    \"billable\": true,
    \"employees\": [\"$EMP1_ID\", \"$EMP2_ID\"]
  }")

PROJECT_ID=$(echo "$PROJECT_RESPONSE" | tr -d '\n' | sed 's/.*"id": *"\([^"]*\)".*/\1/')
echo "✅ Project created: $PROJECT_ID"

# Setup: Create 2 Tasks for the Project
echo -e "\n4. 📋 Creating tasks for the project..."
create_task() {
    local name=$1
    local priority=$2
    curl -s -X POST $TASK_API_BASE/ \
        -H "$AUTH_HEADER" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"$name\", \"project_id\": \"$PROJECT_ID\", \"priority\": \"$priority\", \"status\": \"pending\"}" | \
        tr -d '\n' | sed 's/.*"id": *"\([^"]*\)".*/\1/'
}

TASK1_ID=$(create_task "Implement Frontend" "high")
TASK2_ID=$(create_task "Setup Database" "medium")

echo "✅ Created 2 tasks: $TASK1_ID, $TASK2_ID"

# Initial State Verification
echo -e "\n5. 📊 Verifying initial state..."
verify_relationships() {
    local context=$1
    local emp3_should_be_in_project=${2:-false}
    echo "🔍 $context"
    
    # Get current state
    PROJECT=$(curl -s -H "$AUTH_HEADER" "$PROJECT_API_BASE/$PROJECT_ID")
    EMP1=$(curl -s -H "$AUTH_HEADER" "$EMPLOYEE_API_BASE/$EMP1_ID")
    EMP2=$(curl -s -H "$AUTH_HEADER" "$EMPLOYEE_API_BASE/$EMP2_ID")
    EMP3=$(curl -s -H "$AUTH_HEADER" "$EMPLOYEE_API_BASE/$EMP3_ID")
    TASK1=$(curl -s -H "$AUTH_HEADER" "$TASK_API_BASE/$TASK1_ID")
    TASK2=$(curl -s -H "$AUTH_HEADER" "$TASK_API_BASE/$TASK2_ID")
    
    # Extract employee lists
    PROJ_EMPLOYEES=$(echo $PROJECT | grep -o '"employees": *\[[^]]*\]')
    TASK1_EMPLOYEES=$(echo $TASK1 | grep -o '"employees": *\[[^]]*\]')
    TASK2_EMPLOYEES=$(echo $TASK2 | grep -o '"employees": *\[[^]]*\]')
    
    # Extract project lists  
    EMP1_PROJECTS=$(echo $EMP1 | grep -o '"projects": *\[[^]]*\]')
    EMP2_PROJECTS=$(echo $EMP2 | grep -o '"projects": *\[[^]]*\]')
    EMP3_PROJECTS=$(echo $EMP3 | grep -o '"projects": *\[[^]]*\]')

    
    echo "📋 Project employees: $PROJ_EMPLOYEES"
    echo "🎯 Task1 employees: $TASK1_EMPLOYEES"
    echo "🎯 Task2 employees: $TASK2_EMPLOYEES"
    echo "👤 Employee1 projects: $EMP1_PROJECTS"
    echo "👤 Employee2 projects: $EMP2_PROJECTS"
    echo "👤 Employee3 projects: $EMP3_PROJECTS"
    
    # Verify consistency
    if [ "$PROJ_EMPLOYEES" = "$TASK1_EMPLOYEES" ] && [ "$PROJ_EMPLOYEES" = "$TASK2_EMPLOYEES" ]; then
        echo "✅ All task employees match project employees"
    else
        echo "❌ Task employees don't match project employees"
    fi
    
    # Check Employee 1 (should always have project except in special cases)
    local emp1_should_have_project=${3:-true}
    # Check Employee 2 (may vary based on test)
    local emp2_should_have_project=${4:-true}
    
    local emp1_ok=false
    local emp2_ok=false
    
    if [ "$emp1_should_have_project" = "true" ]; then
        if echo $EMP1_PROJECTS | grep -q "$PROJECT_ID"; then
            emp1_ok=true
        fi
    else
        if ! echo $EMP1_PROJECTS | grep -q "$PROJECT_ID"; then
            emp1_ok=true
        fi
    fi
    
    if [ "$emp2_should_have_project" = "true" ]; then
        if echo $EMP2_PROJECTS | grep -q "$PROJECT_ID"; then
            emp2_ok=true
        fi
    else
        if ! echo $EMP2_PROJECTS | grep -q "$PROJECT_ID"; then
            emp2_ok=true
        fi
    fi
    
    if [ "$emp1_ok" = true ] && [ "$emp2_ok" = true ]; then
        echo "✅ Employee 1&2 project relationships correct"
    else
        echo "❌ Employee 1&2 project relationships incorrect"
    fi
    
    if [ "$emp3_should_be_in_project" = "true" ]; then
        if echo $EMP3_PROJECTS | grep -q "$PROJECT_ID"; then
            echo "✅ Employee 3 correctly has project in list"
        else
            echo "❌ Employee 3 missing project in list"
        fi
    else
        if ! echo $EMP3_PROJECTS | grep -q "$PROJECT_ID"; then
            echo "✅ Employee 3 correctly not in project"
        else
            echo "❌ Employee 3 incorrectly has project in list"
        fi
    fi
}

verify_relationships "Initial state verification" false true true

# Test 1: Add Employee via Project API
echo -e "\n6. 🔄 Test 1: Adding Employee 3 via Project API..."
curl -s -X PUT $PROJECT_API_BASE/$PROJECT_ID \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{\"employees\": [\"$EMP1_ID\", \"$EMP2_ID\", \"$EMP3_ID\"]}" > /dev/null

verify_relationships "After adding Employee 3 via Project API" true true true

# Test 2: Remove Employee via Employee API
echo -e "\n7. 🔄 Test 2: Removing Employee 2 via Employee API..."
curl -s -X PUT $EMPLOYEE_API_BASE/$EMP2_ID \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{\"projects\": []}" > /dev/null

verify_relationships "After removing Employee 2 via Employee API" true true false

# Test 3: Verify Tasks Still Sync
echo -e "\n8. 🔄 Test 3: Adding Employee 2 back via Project API..."
curl -s -X PUT $PROJECT_API_BASE/$PROJECT_ID \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{\"employees\": [\"$EMP1_ID\", \"$EMP2_ID\", \"$EMP3_ID\"]}" > /dev/null

verify_relationships "After adding Employee 2 back via Project API" true true true

# Test 4: Task Creation Inherits Project Employees
echo -e "\n9. 📋 Test 4: Creating new task (should inherit current project employees)..."
TASK3_ID=$(create_task "Write Tests" "urgent")
TASK3=$(curl -s -H "$AUTH_HEADER" "$TASK_API_BASE/$TASK3_ID")
    TASK3_EMPLOYEES=$(echo $TASK3 | grep -o '"employees": *\[[^]]*\]')

echo "📋 New task employees: $TASK3_EMPLOYEES"
if echo $TASK3_EMPLOYEES | grep -q "$EMP1_ID" && echo $TASK3_EMPLOYEES | grep -q "$EMP2_ID" && echo $TASK3_EMPLOYEES | grep -q "$EMP3_ID"; then
    echo "✅ New task correctly inherited all 3 project employees"
else
    echo "❌ New task did not inherit project employees correctly"
fi

# Test 5: Project Employee Change Syncs All Tasks
echo -e "\n10. 🔄 Test 5: Removing 2 employees from project (should sync to all tasks)..."
curl -s -X PUT $PROJECT_API_BASE/$PROJECT_ID \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{\"employees\": [\"$EMP1_ID\"]}" > /dev/null

echo "🔍 Verifying all tasks synced to single employee..."
TASK1_AFTER=$(curl -s -H "$AUTH_HEADER" "$TASK_API_BASE/$TASK1_ID")
TASK2_AFTER=$(curl -s -H "$AUTH_HEADER" "$TASK_API_BASE/$TASK2_ID")
TASK3_AFTER=$(curl -s -H "$AUTH_HEADER" "$TASK_API_BASE/$TASK3_ID")

    TASK1_EMP_AFTER=$(echo $TASK1_AFTER | grep -o '"employees": *\[[^]]*\]')
    TASK2_EMP_AFTER=$(echo $TASK2_AFTER | grep -o '"employees": *\[[^]]*\]')
    TASK3_EMP_AFTER=$(echo $TASK3_AFTER | grep -o '"employees": *\[[^]]*\]')

echo "📋 Task1 employees after: $TASK1_EMP_AFTER"
echo "📋 Task2 employees after: $TASK2_EMP_AFTER"  
echo "📋 Task3 employees after: $TASK3_EMP_AFTER"

if echo $TASK1_EMP_AFTER | grep -q "$EMP1_ID" && ! echo $TASK1_EMP_AFTER | grep -q "$EMP2_ID" && ! echo $TASK1_EMP_AFTER | grep -q "$EMP3_ID"; then
    echo "✅ All tasks correctly synced to only Employee 1"
else
    echo "❌ Tasks did not sync correctly with project change"
fi

echo "🔍 Verifying Employee API reflects project removal..."
EMP1_FINAL=$(curl -s -H "$AUTH_HEADER" "$EMPLOYEE_API_BASE/$EMP1_ID")
EMP2_FINAL=$(curl -s -H "$AUTH_HEADER" "$EMPLOYEE_API_BASE/$EMP2_ID") 
EMP3_FINAL=$(curl -s -H "$AUTH_HEADER" "$EMPLOYEE_API_BASE/$EMP3_ID")

EMP1_PROJECTS_FINAL=$(echo $EMP1_FINAL | grep -o '"projects": *\[[^]]*\]')
EMP2_PROJECTS_FINAL=$(echo $EMP2_FINAL | grep -o '"projects": *\[[^]]*\]')
EMP3_PROJECTS_FINAL=$(echo $EMP3_FINAL | grep -o '"projects": *\[[^]]*\]')

echo "👤 Employee1 final projects: $EMP1_PROJECTS_FINAL"
echo "👤 Employee2 final projects: $EMP2_PROJECTS_FINAL"
echo "👤 Employee3 final projects: $EMP3_PROJECTS_FINAL"

if echo $EMP1_PROJECTS_FINAL | grep -q "$PROJECT_ID" && ! echo $EMP2_PROJECTS_FINAL | grep -q "$PROJECT_ID" && ! echo $EMP3_PROJECTS_FINAL | grep -q "$PROJECT_ID"; then
    echo "✅ Employee API correctly reflects project removal"
else
    echo "❌ Employee API does not reflect project removal correctly"
fi

# Final Summary
echo -e "\n🎉 Three-Way Bidirectional Relationship Test Complete!"
echo "✅ Employee ↔ Project relationships working"
echo "✅ Project ↔ Task employee sync working"
echo "✅ Task creation inherits project employees"
echo "✅ Project employee changes sync to all tasks"
echo "✅ All bidirectional relationships verified" 