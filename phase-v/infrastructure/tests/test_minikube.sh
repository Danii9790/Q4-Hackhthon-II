#!/bin/bash
#
# test_minikube.sh - Infrastructure validation test for Minikube deployment
#
# T108: This test verifies that all services start correctly on Minikube
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="todo-app"
TIMEOUT=300  # 5 minutes
RETRY_INTERVAL=5

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

# Check if Minikube is running
check_minikube_running() {
    log_info "Checking if Minikube is running..."
    if minikube status | grep -q "Running"; then
        test_pass "Minikube is running"
    else
        test_fail "Minikube is not running"
        exit 1
    fi
}

# Check if namespace exists
check_namespace() {
    log_info "Checking namespace ${NAMESPACE}..."
    if kubectl get namespace ${NAMESPACE} &> /dev/null; then
        test_pass "Namespace ${NAMESPACE} exists"
    else
        test_fail "Namespace ${NAMESPACE} does not exist"
    fi
}

# Check if Dapr is installed
check_dapr() {
    log_info "Checking Dapr installation..."
    if kubectl get namespace dapr-system &> /dev/null; then
        test_pass "Dapr namespace exists"

        # Check Dapr pods
        DAPR_PODS=$(kubectl get pods -n dapr-system --no-headers | wc -l)
        if [ "${DAPR_PODS}" -gt 0 ]; then
            test_pass "Dapr pods are running (${DAPR_PODS} pods)"
        else
            test_fail "No Dapr pods found"
        fi
    else
        test_fail "Dapr is not installed"
    fi
}

# Check Kafka deployment
check_kafka() {
    log_info "Checking Kafka deployment..."

    # Wait for Kafka pods to be ready
    KAFKA_READY=0
    ELAPSED=0
    while [ ${ELAPSED} -lt ${TIMEOUT} ]; do
        KAFKA_PODS=$(kubectl get pods -n ${NAMESPACE} -l app=redpanda --no-headers 2>/dev/null || echo "")
        if [ -n "${KAFKA_PODS}" ]; then
            KAFKA_READY=$(echo "${KAFKA_PODS}" | grep -c "Running" || echo "0")
            if [ "${KAFKA_READY}" -gt 0 ]; then
                test_pass "Kafka is running (${KAFKA_READY} pods ready)"
                return
            fi
        fi
        sleep ${RETRY_INTERVAL}
        ELAPSED=$((ELAPSED + RETRY_INTERVAL))
        echo -n "."
    done

    test_fail "Kafka did not become ready within ${TIMEOUT} seconds"
}

# Check backend deployment
check_backend() {
    log_info "Checking backend deployment..."

    # Wait for backend pods to be ready
    BACKEND_READY=0
    ELAPSED=0
    while [ ${ELAPSED} -lt ${TIMEOUT} ]; do
        BACKEND_PODS=$(kubectl get pods -n ${NAMESPACE} -l component=backend --no-headers 2>/dev/null || echo "")
        if [ -n "${BACKEND_PODS}" ]; then
            BACKEND_READY=$(echo "${BACKEND_PODS}" | grep -c "Running" || echo "0")
            if [ "${BACKEND_READY}" -gt 0 ]; then
                test_pass "Backend is running (${BACKEND_READY} pods ready)"
                return
            fi
        fi
        sleep ${RETRY_INTERVAL}
        ELAPSED=$((ELAPSED + RETRY_INTERVAL))
        echo -n "."
    done

    test_fail "Backend did not become ready within ${TIMEOUT} seconds"
}

# Check frontend deployment
check_frontend() {
    log_info "Checking frontend deployment..."

    # Wait for frontend pods to be ready
    FRONTEND_READY=0
    ELAPSED=0
    while [ ${ELAPSED} -lt ${TIMEOUT} ]; do
        FRONTEND_PODS=$(kubectl get pods -n ${NAMESPACE} -l component=frontend --no-headers 2>/dev/null || echo "")
        if [ -n "${FRONTEND_PODS}" ]; then
            FRONTEND_READY=$(echo "${FRONTEND_PODS}" | grep -c "Running" || echo "0")
            if [ "${FRONTEND_READY}" -gt 0 ]; then
                test_pass "Frontend is running (${FRONTEND_READY} pods ready)"
                return
            fi
        fi
        sleep ${RETRY_INTERVAL}
        ELAPSED=$((ELAPSED + RETRY_INTERVAL))
        echo -n "."
    done

    test_fail "Frontend did not become ready within ${TIMEOUT} seconds"
}

# Check services
check_services() {
    log_info "Checking services..."

    # Check backend service
    if kubectl get service backend-service -n ${NAMESPACE} &> /dev/null; then
        test_pass "Backend service exists"
    else
        test_fail "Backend service does not exist"
    fi

    # Check frontend service
    if kubectl get service frontend-service -n ${NAMESPACE} &> /dev/null; then
        test_pass "Frontend service exists"
    else
        test_fail "Frontend service does not exist"
    fi

    # Check Kafka service
    if kubectl get service kafka-service -n ${NAMESPACE} &> /dev/null; then
        test_pass "Kafka service exists"
    else
        test_fail "Kafka service does not exist"
    fi
}

# Check ingress
check_ingress() {
    log_info "Checking ingress..."

    if kubectl get ingress frontend-ingress -n ${NAMESPACE} &> /dev/null; then
        test_pass "Frontend ingress exists"
    else
        test_fail "Frontend ingress does not exist"
    fi
}

# Check HPA
check_hpa() {
    log_info "Checking HorizontalPodAutoscalers..."

    # Check backend HPA
    if kubectl get hpa backend-hpa -n ${NAMESPACE} &> /dev/null; then
        test_pass "Backend HPA exists"
    else
        test_fail "Backend HPA does not exist"
    fi

    # Check frontend HPA
    if kubectl get hpa frontend-hpa -n ${NAMESPACE} &> /dev/null; then
        test_pass "Frontend HPA exists"
    else
        test_fail "Frontend HPA does not exist"
    fi
}

# Display pod status
display_pod_status() {
    log_info "Pod status in ${NAMESPACE} namespace:"
    kubectl get pods -n ${NAMESPACE}
}

# Main execution
main() {
    echo "=========================================="
    echo "Minikube Infrastructure Validation Test"
    echo "=========================================="
    echo ""

    check_minikube_running
    check_namespace
    check_dapr
    check_kafka
    check_backend
    check_frontend
    check_services
    check_ingress
    check_hpa

    echo ""
    display_pod_status

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
