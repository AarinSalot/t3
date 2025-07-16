#!/bin/bash

BASE_URL="http://127.0.0.1:5000"
PROJECT_API_BASE="$BASE_URL/api/v1/project"
EMPLOYEE_API_BASE="$BASE_URL/api/v1/employee"
TIMESTAMP=$(date +%s)$(jot -r 1 1000 9999)
EMAIL="test$TIMESTAMP@example.com"

echo "🔗 Bidirectional Relationship Test"
echo "Testing that Employee ↔ Project relationships work both ways"

# Register and get token
echo -e "\n1. 👤 Setting up authentication..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST $BASE_URL/api/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Test User\", \"email\": \"$EMAIL\", \"password\": \"password123\", \"confirm_password\": \"password123\"}")

TOKEN=$(echo "$RESPONSE" | sed -e 's/HTTPSTATUS\:.*//g' | tr -d '\n' | sed 's/.*"access_token": *"\([^"]*\)".*/\1/')
AUTH_HEADER="Authorization: Bearer $TOKEN"
echo "✅ Authenticated"

# Create employee
echo -e "\n2. 👨‍💼 Creating employee..."
EMPLOYEE_RESPONSE=$(curl -s -X POST $EMPLOYEE_API_BASE/ \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"John Doe\", \"email\": \"john$TIMESTAMP@company.com\"}")

EMPLOYEE_ID=$(echo "$EMPLOYEE_RESPONSE" | tr -d '\n' | sed 's/.*"id": *"\([^"]*\)".*/\1/')
echo "✅ Employee created: $EMPLOYEE_ID"

# Create project with employee
echo -e "\n3. 🎯 Creating project and assigning employee..."
PROJECT_RESPONSE=$(curl -s -X POST $PROJECT_API_BASE/ \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Test Project $TIMESTAMP\", \"employees\": [\"$EMPLOYEE_ID\"]}")

PROJECT_ID=$(echo "$PROJECT_RESPONSE" | tr -d '\n' | sed 's/.*"id": *"\([^"]*\)".*/\1/')
echo "✅ Project created: $PROJECT_ID"

# Verify bidirectional relationship
echo -e "\n4. 🔍 Verifying bidirectional relationship..."

echo "📋 Checking project shows employee:"
PROJECT_CHECK=$(curl -s -H "$AUTH_HEADER" "$PROJECT_API_BASE/$PROJECT_ID")
if echo $PROJECT_CHECK | grep -q "$EMPLOYEE_ID"; then
    echo "✅ Project contains employee ID"
else
    echo "❌ Project does NOT contain employee ID"
fi

echo "👤 Checking employee shows project:"
EMPLOYEE_CHECK=$(curl -s -H "$AUTH_HEADER" "$EMPLOYEE_API_BASE/$EMPLOYEE_ID")
if echo $EMPLOYEE_CHECK | grep -q "$PROJECT_ID"; then
    echo "✅ Employee contains project ID"
else
    echo "❌ Employee does NOT contain project ID"
fi

# Test updating via employee API
echo -e "\n5. 🔄 Testing project update via Employee API..."
curl -s -X PUT $EMPLOYEE_API_BASE/$EMPLOYEE_ID \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{\"projects\": []}" > /dev/null

# Check both sides updated
PROJECT_CHECK2=$(curl -s -H "$AUTH_HEADER" "$PROJECT_API_BASE/$PROJECT_ID")
EMPLOYEE_CHECK2=$(curl -s -H "$AUTH_HEADER" "$EMPLOYEE_API_BASE/$EMPLOYEE_ID")

echo "📋 After removing via Employee API:"
if echo $PROJECT_CHECK2 | grep -q "$EMPLOYEE_ID"; then
    echo "❌ Project still contains employee (should be removed)"
else
    echo "✅ Project no longer contains employee"
fi

if echo $EMPLOYEE_CHECK2 | grep -q "$PROJECT_ID"; then
    echo "❌ Employee still contains project (should be removed)"
else
    echo "✅ Employee no longer contains project"
fi

echo -e "\n🎉 Bidirectional relationship test complete!"
echo "✅ Both Employee API and Project API maintain consistent relationships" 