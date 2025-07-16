#!/bin/bash

BASE_URL="http://127.0.0.1:5000"
PROJECT_API_BASE="$BASE_URL/api/v1/project"
EMPLOYEE_API_BASE="$BASE_URL/api/v1/employee"
TIMESTAMP=$(date +%s)$(jot -r 1 1000 9999)
EMAIL="test$TIMESTAMP@example.com"

echo "🚀 Comprehensive Project API Test"
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

# Test 2: Create Employees for Project Assignment
echo -e "\n2. 👨‍💼 Creating employees for project assignment..."
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
    \"name\": \"Project Alpha $TIMESTAMP\",
    \"description\": \"A test project for API validation\",
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

# Test 4: Get All Projects
echo -e "\n4. 📋 Getting all projects..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -H "$AUTH_HEADER" $PROJECT_API_BASE/)
HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Retrieved projects successfully"
    echo "📊 Response: $BODY"
else
    echo "❌ Failed to get projects: $BODY"
fi

# Test 5: Get Project by ID
echo -e "\n5. 👁️ Getting project by ID..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -H "$AUTH_HEADER" "$PROJECT_API_BASE/$PROJECT_ID")
HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Project retrieved by ID successfully"
    echo "📊 Response: $BODY"
else
    echo "❌ Failed to get project by ID: $BODY"
fi

# Test 6: Verify Bidirectional Relationship - Check Employee Projects
echo -e "\n6. 🔗 Verifying bidirectional relationship - checking employee projects..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -H "$AUTH_HEADER" "$EMPLOYEE_API_BASE/$EMPLOYEE1_ID")
HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Employee retrieved successfully"
    PROJECT_IN_EMPLOYEE=$(echo $BODY | grep -o "\"$PROJECT_ID\"" || echo "")
    if [ ! -z "$PROJECT_IN_EMPLOYEE" ]; then
        echo "✅ Confirmed: Project appears in employee's projects list"
    else
        echo "❌ ERROR: Project not found in employee's projects list"
    fi
    echo "📊 Employee Response: $BODY"
else
    echo "❌ Failed to get employee: $BODY"
fi

# Test 7: Update Project - Add Description and Change Status
echo -e "\n7. ✏️ Updating project..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X PUT $PROJECT_API_BASE/$PROJECT_ID \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated project description with more details",
    "archived": false,
    "billable": false
  }')

HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Project updated successfully"
    echo "📊 Response: $BODY"
else
    echo "❌ Failed to update project: $BODY"
fi

# Test 8: Add Employee to Project via Project API
echo -e "\n8. ➕ Adding employee to project via project endpoint..."
# First create another employee
EMPLOYEE3_EMAIL="mike.wilson$TIMESTAMP@company.com"
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST $EMPLOYEE_API_BASE/ \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Mike Wilson\",
    \"email\": \"$EMPLOYEE3_EMAIL\"
  }")

EMPLOYEE3_ID=$(echo "$RESPONSE" | sed -e 's/HTTPSTATUS\:.*//g' | tr -d '\n' | sed 's/.*"id": *"\([^"]*\)".*/\1/')

RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST $PROJECT_API_BASE/$PROJECT_ID/employees \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{\"employee_id\": \"$EMPLOYEE3_ID\"}")

HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Employee added to project successfully"
    echo "📊 Response: $BODY"
else
    echo "❌ Failed to add employee to project: $BODY"
fi

# Test 9: Search Projects
echo -e "\n9. 🔍 Searching projects..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -H "$AUTH_HEADER" "$PROJECT_API_BASE/?search=Alpha")
HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Project search completed successfully"
    echo "📊 Response: $BODY"
else
    echo "❌ Project search failed: $BODY"
fi

# Test 10: Filter Active Projects
echo -e "\n10. 📂 Getting active (non-archived) projects..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -H "$AUTH_HEADER" "$PROJECT_API_BASE/?active_only=true")
HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Active projects retrieved successfully"
    echo "📊 Response: $BODY"
else
    echo "❌ Failed to get active projects: $BODY"
fi

# Test 11: Update Project Employee List via PUT
echo -e "\n11. 🔄 Updating project employee list via PUT..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X PUT $PROJECT_API_BASE/$PROJECT_ID \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{
    \"employees\": [\"$EMPLOYEE1_ID\"]
  }")

HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Project employee list updated successfully"
    echo "📊 Response: $BODY"
else
    echo "❌ Failed to update project employee list: $BODY"
fi

# Test 12: Remove Employee from Project
echo -e "\n12. ➖ Removing employee from project..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X DELETE $PROJECT_API_BASE/$PROJECT_ID/employees/$EMPLOYEE1_ID \
  -H "$AUTH_HEADER")

HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Employee removed from project successfully"
    echo "📊 Response: $BODY"
else
    echo "❌ Failed to remove employee from project: $BODY"
fi

# Test 13: Create Second Project for Testing
echo -e "\n13. 🎯 Creating second project for deletion test..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST $PROJECT_API_BASE/ \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Project Beta $TIMESTAMP\",
    \"description\": \"Another test project for deletion\",
    \"archived\": false,
    \"billable\": true
  }")

HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 201 ]; then
    echo "✅ Second project created successfully"
    PROJECT2_ID=$(echo "$BODY" | tr -d '\n' | sed 's/.*"id": *"\([^"]*\)".*/\1/')
    echo "📝 Second Project ID: $PROJECT2_ID"
else
    echo "❌ Second project creation failed: $BODY"
    exit 1
fi

# Test 14: Delete Project
echo -e "\n14. 🗑️ Deleting second project..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X DELETE $PROJECT_API_BASE/$PROJECT2_ID \
  -H "$AUTH_HEADER")

HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Project deleted successfully"
    echo "📊 Response: $BODY"
else
    echo "❌ Failed to delete project: $BODY"
fi

# Test 15: Verify Project Deletion
echo -e "\n15. 🔍 Verifying project deletion..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -H "$AUTH_HEADER" $PROJECT_API_BASE/$PROJECT2_ID)
HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 404 ]; then
    echo "✅ Confirmed: Project not found (successfully deleted)"
    echo "📊 Response: $BODY"
else
    echo "❌ Unexpected response - project may still exist: $BODY"
fi

echo -e "\n🎉 Comprehensive project API test complete!" 