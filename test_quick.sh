#!/bin/bash

BASE_URL="http://127.0.0.1:5000"
EMPLOYEE_API_BASE="$BASE_URL/api/v1/employee"
TIMESTAMP=$(date +%s)$(jot -r 1 1000 9999)
EMAIL="test$TIMESTAMP@example.com"

echo "🚀 Quick Employee API Test"
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

# Test 2: Create Employee
echo -e "\n2. 👨‍💼 Creating employee..."
EMPLOYEE_EMAIL="john.doe$TIMESTAMP@company.com"
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST $EMPLOYEE_API_BASE/ \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"John Doe\",
    \"email\": \"$EMPLOYEE_EMAIL\",
    \"projects\": [\"project-alpha\", \"project-beta\"]
  }")

HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 201 ]; then
    echo "✅ Employee created successfully"
    EMPLOYEE_ID=$(echo "$BODY" | tr -d '\n' | sed 's/.*"id": *"\([^"]*\)".*/\1/')
    echo "📝 Response body: $BODY"
    echo "📝 Employee ID: $EMPLOYEE_ID"
else
    echo "❌ Employee creation failed: $BODY"
fi

# Test 3: Get All Employees
echo -e "\n3. 📋 Getting all employees..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -H "$AUTH_HEADER" $EMPLOYEE_API_BASE/)
HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Retrieved employees successfully"
    echo "📊 Response: $BODY"
else
    echo "❌ Failed to get employees: $BODY"
fi

# Test 4: Update Employee with Project Management
echo -e "\n4. ✏️ Updating employee and managing projects..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X PUT $EMPLOYEE_API_BASE/$EMPLOYEE_ID \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Smith (Updated)",
    "projects": ["project-alpha", "project-beta", "project-gamma"]
  }')

HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Employee updated with projects successfully"
    echo "📊 Response: $BODY"
else
    echo "❌ Failed to update employee: $BODY"
fi

# Test 5: Get Single Employee by ID
echo -e "\n5. 👤 Getting employee by ID..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -H "$AUTH_HEADER" "$EMPLOYEE_API_BASE/$EMPLOYEE_ID")
HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Employee retrieved by ID successfully"
    echo "📊 Response: $BODY"
else
    echo "❌ Failed to get employee by ID: $BODY"
fi

# Test 6: Deactivate Employee (test timestamp)
echo -e "\n6. 🚫 Deactivating employee..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST $EMPLOYEE_API_BASE/deactivate/$EMPLOYEE_ID \
  -H "$AUTH_HEADER")

HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Employee deactivated successfully"
    echo "📊 Response: $BODY"
    
    # Check if deactivated field has a timestamp
    DEACTIVATED_TIME=$(echo $BODY | tr -d '\n' | sed 's/.*"deactivated": *\([0-9]*\).*/\1/')
    if [ ! -z "$DEACTIVATED_TIME" ] && [ "$DEACTIVATED_TIME" != "null" ] && [ "$DEACTIVATED_TIME" != "$BODY" ]; then
        echo "✅ Deactivated timestamp confirmed: $DEACTIVATED_TIME"
    else
        echo "❌ Deactivated timestamp missing or null"
    fi
else
    echo "❌ Failed to deactivate employee: $BODY"
fi

# Test 7: Reactivate Employee via PUT endpoint
echo -e "\n7. 🔄 Reactivating employee via PUT endpoint..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X PUT $EMPLOYEE_API_BASE/$EMPLOYEE_ID \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{"deactivated": null}')

HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Employee reactivated successfully via PUT"
    echo "📊 Response: $BODY"
    
    # Check if deactivated field is now null
    DEACTIVATED_FIELD=$(echo $BODY | tr -d '\n' | grep -o '"deactivated": *null' || echo "")
    if [ ! -z "$DEACTIVATED_FIELD" ]; then
        echo "✅ Confirmed: Employee reactivated (deactivated: null)"
    else
        echo "❌ ERROR: Employee should be reactivated but deactivated field is not null"
    fi
else
    echo "❌ Failed to reactivate employee: $BODY"
fi

# Test 8: Search
echo -e "\n8. 🔍 Searching employees..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -H "$AUTH_HEADER" "$EMPLOYEE_API_BASE/?search=john")
HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Search completed successfully"
    echo "📊 Response: $BODY"
else
    echo "❌ Search failed: $BODY"
fi

# Test 9: Verify Final Employee State
echo -e "\n9. 🔍 Verifying final employee state..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -H "$AUTH_HEADER" "$EMPLOYEE_API_BASE/$EMPLOYEE_ID")
HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Employee retrieved successfully"
    echo "📊 Response: $BODY"
    
    # Verify the employee is now reactivated (deactivated field is null)
    DEACTIVATED_FIELD=$(echo $BODY | tr -d '\n' | grep -o '"deactivated": *null' || echo "")
    if [ ! -z "$DEACTIVATED_FIELD" ]; then
        echo "✅ Final confirmation: Employee is active (deactivated: null)"
    else
        echo "❌ ERROR: Employee should be active but deactivated field is not null"
    fi
else
    echo "❌ ERROR: Cannot retrieve employee: $BODY"
fi

echo -e "\n🎉 Quick test complete!" 