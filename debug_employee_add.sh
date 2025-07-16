#!/bin/bash

# Debug script for employee add endpoint
API_BASE="http://localhost:5000/api/v1"
EMPLOYEE_API_BASE="$API_BASE/employee"
PROJECT_API_BASE="$API_BASE/project"

# Generate unique timestamp
TIMESTAMP=$(date +%s%3N)
EMAIL="debug$TIMESTAMP@test.com"

echo "🔍 Debug: Testing individual employee add endpoint"

# 1. Register and get auth token
echo "1. Getting auth token..."
AUTH_RESPONSE=$(curl -s -X POST "$API_BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"password123\"}")

echo "📊 Auth Response: $AUTH_RESPONSE"

# Try multiple patterns to extract the token
TOKEN=$(echo $AUTH_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
if [ -z "$TOKEN" ]; then
    TOKEN=$(echo $AUTH_RESPONSE | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
fi
if [ -z "$TOKEN" ]; then
    TOKEN=$(echo $AUTH_RESPONSE | jq -r '.access_token // .token // empty' 2>/dev/null)
fi

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to extract token from response"
    echo "📊 Response: $AUTH_RESPONSE"
    exit 1
fi

AUTH_HEADER="Authorization: Bearer $TOKEN"
echo "✅ Token: ${TOKEN:0:20}..."

# 2. Create an employee
echo "2. Creating employee..."
EMP_RESPONSE=$(curl -s -X POST $EMPLOYEE_API_BASE/ \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Test Employee\", \"email\": \"emp$TIMESTAMP@test.com\"}")

echo "📊 Employee Response: $EMP_RESPONSE"
EMPLOYEE_ID=$(echo $EMP_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$EMPLOYEE_ID" ]; then
    echo "❌ Failed to extract employee ID"
    exit 1
fi

echo "✅ Employee ID: $EMPLOYEE_ID"

# 3. Create a project
echo "3. Creating project..."
PROJ_RESPONSE=$(curl -s -X POST $PROJECT_API_BASE/ \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Debug Project $TIMESTAMP\", \"description\": \"Test project\"}")

echo "📊 Project Response: $PROJ_RESPONSE"
PROJECT_ID=$(echo $PROJ_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Failed to extract project ID"
    exit 1
fi

echo "✅ Project ID: $PROJECT_ID"

# 4. Create another employee to add
echo "4. Creating another employee..."
EMP2_RESPONSE=$(curl -s -X POST $EMPLOYEE_API_BASE/ \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Test Employee 2\", \"email\": \"emp2$TIMESTAMP@test.com\"}")

EMPLOYEE2_ID=$(echo $EMP2_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$EMPLOYEE2_ID" ]; then
    echo "❌ Failed to extract employee 2 ID"
    exit 1
fi

echo "✅ Employee 2 ID: $EMPLOYEE2_ID"

# 5. Test the problematic endpoint
echo "5. 🔍 Testing: POST /project/{id}/employees"
echo "URL: $PROJECT_API_BASE/$PROJECT_ID/employees"
echo "Data: {\"employee_id\": \"$EMPLOYEE2_ID\"}"

ADD_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST "$PROJECT_API_BASE/$PROJECT_ID/employees" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{\"employee_id\": \"$EMPLOYEE2_ID\"}")

HTTP_STATUS=$(echo $ADD_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $ADD_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

echo "📊 Response Status: $HTTP_STATUS"
echo "📊 Response Body: $BODY"

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ SUCCESS: Employee added to project"
else
    echo "❌ FAILED: $BODY"
fi

# 6. Test the remove endpoint too
echo "6. 🔍 Testing: DELETE /project/{id}/employees/{emp_id}"
echo "URL: $PROJECT_API_BASE/$PROJECT_ID/employees/$EMPLOYEE2_ID"

REMOVE_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X DELETE "$PROJECT_API_BASE/$PROJECT_ID/employees/$EMPLOYEE2_ID" \
  -H "$AUTH_HEADER")

HTTP_STATUS=$(echo $REMOVE_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $REMOVE_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

echo "📊 Response Status: $HTTP_STATUS"
echo "📊 Response Body: $BODY"

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ SUCCESS: Employee removed from project"
else
    echo "❌ FAILED: $BODY"
fi

echo "🏁 Debug complete" 