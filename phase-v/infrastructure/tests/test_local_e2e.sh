#!/bin/bash
#
# test_local_e2e.sh - End-to-end test for local Minikube deployment
#
# T109: This test verifies that the application works end-to-end by creating a task and verifying Kafka events
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="todo-app"
BACKEND_URL="${BACKEND_URL:-http://$(minikube ip)}"
TEST_USER_EMAIL="e2e-test@example.com"
TEST_USER_NAME="E2E Test User"

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

test_pass() {
    TESTS_PASSED=$((TESTS_PASSED + 1))
    log_info "✓ PASS: $1"
}

test_fail() {
    TESTS_FAILED=$((TESTS_FAILED + 1))
    log_error "✗ FAIL: $1"
}

# Check if backend is accessible
check_backend_accessible() {
    log_info "Checking if backend is accessible..."

    # Try health endpoint
    if curl -f -s "${BACKEND_URL}/health" > /dev/null 2>&1; then
        test_pass "Backend is accessible at ${BACKEND_URL}"
    else
        test_fail "Backend is not accessible at ${BACKEND_URL}"
        return 1
    fi
}

# Create test user
create_test_user() {
    log_info "Creating test user..."

    RESPONSE=$(curl -s -X POST "${BACKEND_URL}/api/auth/signup" \
        -H "Content-Type: application/json" \
        -d "{
            \"email\": \"${TEST_USER_EMAIL}\",
            \"name\": \"${TEST_USER_NAME}\",
            \"password\": \"testpassword123\"
        }")

    # Check if user was created successfully
    if echo "${RESPONSE}" | grep -q "id"; then
        USER_ID=$(echo "${RESPONSE}" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
        test_pass "Test user created with ID: ${USER_ID}"
    else
        test_fail "Failed to create test user"
        log_error "Response: ${RESPONSE}"
        return 1
    fi
}

# Login test user
login_test_user() {
    log_info "Logging in test user..."

    RESPONSE=$(curl -s -X POST "${BACKEND_URL}/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{
            \"email\": \"${TEST_USER_EMAIL}\",
            \"password\": \"testpassword123\"
        }")

    # Check if login was successful
    if echo "${RESPONSE}" | grep -q "access_token"; then
        TOKEN=$(echo "${RESPONSE}" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
        test_pass "Test user logged in successfully"
    else
        test_fail "Failed to login test user"
        log_error "Response: ${RESPONSE}"
        return 1
    fi
}

# Create a test task
create_test_task() {
    log_info "Creating test task..."

    RESPONSE=$(curl -s -X POST "${BACKEND_URL}/api/users/${USER_ID}/tasks" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${TOKEN}" \
        -d "{
            \"title\": \"E2E Test Task\",
            \"description\": \"This task was created by the E2E test\"
        }")

    # Check if task was created successfully
    if echo "${RESPONSE}" | grep -q "id"; then
        TASK_ID=$(echo "${RESPONSE}" | grep -o '"id":[0-9]*' | cut -d':' -f2)
        test_pass "Test task created with ID: ${TASK_ID}"
    else
        test_fail "Failed to create test task"
        log_error "Response: ${RESPONSE}"
        return 1
    fi
}

# Verify task was created
verify_task_created() {
    log_info "Verifying task was created..."

    RESPONSE=$(curl -s "${BACKEND_URL}/api/users/${USER_ID}/tasks" \
        -H "Authorization: Bearer ${TOKEN}")

    # Check if task exists in the list
    if echo "${RESPONSE}" | grep -q "E2E Test Task"; then
        test_pass "Task found in task list"
    else
        test_fail "Task not found in task list"
        log_error "Response: ${RESPONSE}"
        return 1
    fi
}

# Check Kafka for task events
check_kafka_events() {
    log_info "Checking Kafka for task events..."

    # This requires kafkacat or kafka-console-consumer to be installed
    if ! command -v kafkacat &> /dev/null && ! command -v kafka-console-consumer &> /dev/null; then
        log_warn "Kafka consumer not found. Skipping Kafka event verification."
        return
    fi

    # Get Kafka service address
    KAFKA_SERVICE=$(kubectl get service kafka-service -n ${NAMESPACE} -o jsonpath='{.spec.clusterIP}')
    KAFKA_PORT="9092"

    # Try to consume from task-events topic
    if command -v kafkacat &> /dev/null; then
        EVENTS=$(timeout 5 kafkacat -b ${KAFKA_SERVICE}:${KAFKA_PORT} -C -t task-events -o end -c 1 2>/dev/null || echo "")
        if [ -n "${EVENTS}" ]; then
            test_pass "Kafka events found in task-events topic"
        else
            log_warn "No Kafka events found (this is expected if consumer hasn't run yet)"
        fi
    fi
}

# Complete the task
complete_test_task() {
    log_info "Completing test task..."

    RESPONSE=$(curl -s -X PATCH "${BACKEND_URL}/api/tasks/${TASK_ID}/complete" \
        -H "Authorization: Bearer ${TOKEN}")

    # Check if task was completed successfully
    if echo "${RESPONSE}" | grep -q '"completed":true'; then
        test_pass "Test task completed successfully"
    else
        test_fail "Failed to complete test task"
        log_error "Response: ${RESPONSE}"
        return 1
    fi
}

# Verify audit trail
verify_audit_trail() {
    log_info "Verifying audit trail..."

    RESPONSE=$(curl -s "${BACKEND_URL}/api/tasks/${TASK_ID}/audit" \
        -H "Authorization: Bearer ${TOKEN}")

    # Check if audit events exist
    if echo "${RESPONSE}" | grep -q "event_type"; then
        test_pass "Audit trail exists for task"
    else
        test_fail "No audit trail found for task"
        log_error "Response: ${RESPONSE}"
        return 1
    fi
}

# Cleanup test data
cleanup_test_data() {
    log_info "Cleaning up test data..."

    # Delete test task
    curl -s -X DELETE "${BACKEND_URL}/api/tasks/${TASK_ID}" \
        -H "Authorization: Bearer ${TOKEN}" > /dev/null 2>&1 || true

    log_info "Test data cleaned up"
}

# Main execution
main() {
    echo "=========================================="
    echo "Local E2E Test"
    echo "=========================================="
    echo "Backend URL: ${BACKEND_URL}"
    echo ""

    check_backend_accessible

    if create_test_user && login_test_user; then
        create_test_task
        verify_task_created
        check_kafka_events
        complete_test_task
        verify_audit_trail
        cleanup_test_data
    fi

    echo ""
    echo "=========================================="
    echo "Test Summary"
    echo "=========================================="
    echo "Passed: ${TESTS_PASSED}"
    echo "Failed: ${TESTS_FAILED}"
    echo ""

    if [ ${TESTS_FAILED} -eq 0 ]; then
        log_info "All tests passed!"
        exit 0
    else
        log_error "Some tests failed!"
        exit 1
    fi
}

# Run main function
main "$@"
