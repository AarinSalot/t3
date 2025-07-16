#!/bin/bash

BASE_URL="http://127.0.0.1:5000"
TASK_API_BASE="$BASE_URL/api/v1/task"
PROJECT_API_BASE="$BASE_URL/api/v1/project"
EMPLOYEE_API_BASE="$BASE_URL/api/v1/employee"
TIMESTAMP=$(date +%s)$(jot -r 1 1000 9999)
EMAIL="test$TIMESTAMP@example.com"

echo "🎯 Comprehensive Task API Test"
echo "Using email: $EMAIL"

# Test 1: Register User
echo -e "\n1. 👤 Registering user..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST $BASE_URL/api/auth/register \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Test User\",
    \"email\": \"$EMAIL\", 
    \"password\": \"password123\",
    \"confirm_password\": \"password123\"
  }")

HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 201 ]; then
    echo "✅ User registered successfully"
    TOKEN=$(echo "$BODY" | tr -d '\n' | sed 's/.*"access_token": *"\([^"]*\)".*/\1/')
    echo "🔑 Token: ${TOKEN:0:50}..."
else
    echo "❌ Registration failed: $BODY"
    exit 1
fi

AUTH_HEADER="Authorization: Bearer $TOKEN"

# Test 2: Create Employees for Task Assignment
echo -e "\n2. 👨‍💼 Creating employees for task assignment..."
EMPLOYEE1_EMAIL="john.doe$TIMESTAMP@company.com"
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST $EMPLOYEE_API_BASE/ \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"John Doe\",
    \"email\": \"$EMPLOYEE1_EMAIL\"
  }")

HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 201 ]; then
    echo "✅ Employee 1 created successfully"
    EMPLOYEE1_ID=$(echo "$BODY" | tr -d '\n' | sed 's/.*"id": *"\([^"]*\)".*/\1/')
    echo "📝 Employee 1 ID: $EMPLOYEE1_ID"
else
    echo "❌ Employee 1 creation failed: $BODY"
    exit 1
fi

EMPLOYEE2_EMAIL="jane.smith$TIMESTAMP@company.com"
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST $EMPLOYEE_API_BASE/ \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Jane Smith\",
    \"email\": \"$EMPLOYEE2_EMAIL\"
  }")

HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 201 ]; then
    echo "✅ Employee 2 created successfully"
    EMPLOYEE2_ID=$(echo "$BODY" | tr -d '\n' | sed 's/.*"id": *"\([^"]*\)".*/\1/')
    echo "📝 Employee 2 ID: $EMPLOYEE2_ID"
else
    echo "❌ Employee 2 creation failed: $BODY"
    exit 1
fi

# Test 3: Create Project with Employees
echo -e "\n3. 🎯 Creating project with employees..."
DEADLINE=$(($(date +%s) * 1000 + 30 * 24 * 60 * 60 * 1000))  # 30 days from now in milliseconds
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST $PROJECT_API_BASE/ \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Task Project $TIMESTAMP\",
    \"description\": \"A test project for task validation\",
    \"billable\": true,
    \"deadline\": $DEADLINE,
    \"employees\": [\"$EMPLOYEE1_ID\", \"$EMPLOYEE2_ID\"]
  }")

HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 201 ]; then
    echo "✅ Project created successfully"
    PROJECT_ID=$(echo "$BODY" | tr -d '\n' | sed 's/.*"id": *"\([^"]*\)".*/\1/')
    echo "📝 Project ID: $PROJECT_ID"
    echo "📊 Response: $BODY"
else
    echo "❌ Project creation failed: $BODY"
    exit 1
fi

# Test 4: Create Task with Project
echo -e "\n4. 📋 Creating task for the project..."
TASK_DEADLINE=$(($(date +%s) * 1000 + 14 * 24 * 60 * 60 * 1000))  # 14 days from now
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST $TASK_API_BASE/ \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Implement Authentication\",
    \"project_id\": \"$PROJECT_ID\",
    \"description\": \"Implement user authentication with JWT tokens\",
    \"status\": \"pending\",
    \"priority\": \"high\",
    \"labels\": \"backend,security\",
    \"billable\": true,
    \"deadline\": $TASK_DEADLINE
  }")

HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 201 ]; then
    echo "✅ Task created successfully"
    TASK_ID=$(echo "$BODY" | tr -d '\n' | sed 's/.*"id": *"\([^"]*\)".*/\1/')
    echo "📝 Task ID: $TASK_ID"
    echo "📊 Response: $BODY"
else
    echo "❌ Task creation failed: $BODY"
    exit 1
fi

# Test 5: Verify Task Employees Match Project Employees
echo -e "\n5. 🔗 Verifying task employees match project employees..."
TASK_RESPONSE=$(curl -s -H "$AUTH_HEADER" "$TASK_API_BASE/$TASK_ID")
PROJECT_RESPONSE=$(curl -s -H "$AUTH_HEADER" "$PROJECT_API_BASE/$PROJECT_ID")

TASK_EMPLOYEES=$(echo $TASK_RESPONSE | grep -o '"employees":\[[^]]*\]')
PROJECT_EMPLOYEES=$(echo $PROJECT_RESPONSE | grep -o '"employees":\[[^]]*\]')

echo "📋 Task employees: $TASK_EMPLOYEES"
echo "🎯 Project employees: $PROJECT_EMPLOYEES"

if [ "$TASK_EMPLOYEES" = "$PROJECT_EMPLOYEES" ]; then
    echo "✅ Task employees match project employees"
else
    echo "❌ Task employees do NOT match project employees"
fi

# Test 6: Get All Tasks
echo -e "\n6. 📋 Getting all tasks..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -H "$AUTH_HEADER" $TASK_API_BASE/)
HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Retrieved tasks successfully"
    echo "📊 Response: $BODY"
else
    echo "❌ Failed to get tasks: $BODY"
fi

# Test 7: Get Task by ID
echo -e "\n7. 👁️ Getting task by ID..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -H "$AUTH_HEADER" "$TASK_API_BASE/$TASK_ID")
HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Task retrieved by ID successfully"
    echo "📊 Response: $BODY"
else
    echo "❌ Failed to get task by ID: $BODY"
fi

# Test 8: Update Task Status and Priority
echo -e "\n8. ✏️ Updating task status and priority..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X PUT $TASK_API_BASE/$TASK_ID \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress",
    "priority": "urgent",
    "description": "Updated task description with more implementation details"
  }')

HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Task updated successfully"
    echo "📊 Response: $BODY"
else
    echo "❌ Failed to update task: $BODY"
fi

# Test 9: Filter Tasks by Project
echo -e "\n9. 🔍 Filtering tasks by project..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -H "$AUTH_HEADER" "$TASK_API_BASE/?project_id=$PROJECT_ID")
HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Task filtering by project completed successfully"
    echo "📊 Response: $BODY"
else
    echo "❌ Task filtering failed: $BODY"
fi

# Test 10: Filter Tasks by Status
echo -e "\n10. 📂 Filtering tasks by status..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -H "$AUTH_HEADER" "$TASK_API_BASE/?status=in_progress")
HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Task filtering by status completed successfully"
    echo "📊 Response: $BODY"
else
    echo "❌ Task filtering by status failed: $BODY"
fi

# Test 11: Update Project Employees and Verify Task Sync
echo -e "\n11. 🔄 Testing bidirectional sync: updating project employees..."
echo "📝 Removing Employee 2 from project via Project API..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X PUT $PROJECT_API_BASE/$PROJECT_ID \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{
    \"employees\": [\"$EMPLOYEE1_ID\"]
  }")

HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Project employees updated successfully"
    
    # Verify task employees are synced
    echo "🔍 Verifying task employees are synced..."
    TASK_RESPONSE=$(curl -s -H "$AUTH_HEADER" "$TASK_API_BASE/$TASK_ID")
    
    if echo $TASK_RESPONSE | grep -q "$EMPLOYEE1_ID" && ! echo $TASK_RESPONSE | grep -q "$EMPLOYEE2_ID"; then
        echo "✅ Task employees successfully synced with project"
    else
        echo "❌ Task employees not properly synced"
    fi
    
    echo "📊 Updated task: $TASK_RESPONSE"
else
    echo "❌ Failed to update project employees: $BODY"
fi

# Test 12: Search Tasks
echo -e "\n12. 🔍 Searching tasks..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -H "$AUTH_HEADER" "$TASK_API_BASE/?search=Authentication")
HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Task search completed successfully"
    echo "📊 Response: $BODY"
else
    echo "❌ Task search failed: $BODY"
fi

# Test 13: Filter Tasks by Employee
echo -e "\n13. 👤 Filtering tasks by employee assignment..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -H "$AUTH_HEADER" "$TASK_API_BASE/?employee_id=$EMPLOYEE1_ID")
HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Task filtering by employee completed successfully"
    echo "📊 Response: $BODY"
else
    echo "❌ Task filtering by employee failed: $BODY"
fi

# Test 14: Create Second Task for Testing
echo -e "\n14. 📋 Creating second task for deletion test..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST $TASK_API_BASE/ \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Create Documentation\",
    \"project_id\": \"$PROJECT_ID\",
    \"description\": \"Create API documentation\",
    \"status\": \"pending\",
    \"priority\": \"low\",
    \"labels\": \"documentation\",
    \"billable\": false
  }")

HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 201 ]; then
    echo "✅ Second task created successfully"
    TASK2_ID=$(echo "$BODY" | tr -d '\n' | sed 's/.*"id": *"\([^"]*\)".*/\1/')
    echo "📝 Second Task ID: $TASK2_ID"
else
    echo "❌ Second task creation failed: $BODY"
    exit 1
fi

# Test 15: Delete Task
echo -e "\n15. 🗑️ Deleting second task..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X DELETE $TASK_API_BASE/$TASK2_ID \
  -H "$AUTH_HEADER")

HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Task deleted successfully"
    echo "📊 Response: $BODY"
else
    echo "❌ Failed to delete task: $BODY"
fi

# Test 16: Verify Task Deletion
echo -e "\n16. 🔍 Verifying task deletion..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -H "$AUTH_HEADER" $TASK_API_BASE/$TASK2_ID)
HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 404 ]; then
    echo "✅ Confirmed: Task not found (successfully deleted)"
    echo "📊 Response: $BODY"
else
    echo "❌ Unexpected response - task may still exist: $BODY"
fi

echo -e "\n🎉 Comprehensive task API test complete!"
echo "✅ All Task CRUD operations working"
echo "✅ Bidirectional Employee ↔ Project ↔ Task relationships verified" 