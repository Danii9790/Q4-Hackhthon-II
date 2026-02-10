#!/bin/bash
#
# test_production.sh - Production deployment validation test
#
# T131: This test verifies that all services are healthy in production
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="${NAMESPACE:-todo-app}"
TIMEOUT=600  # 10 minutes (production may take longer to start)
RETRY_INTERVAL=10

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

# Check if kubectl is configured
check_kubectl() {
    log_info "Checking kubectl configuration..."
    if ! kubectl cluster-info &> /dev/null; then
        test_fail "kubectl is not configured or cluster is not accessible"
        exit 1
    fi
    test_pass "kubectl is configured"
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

# Check Dapr installation
check_dapr() {
    log_info "Checking Dapr installation..."
    if kubectl get namespace dapr-system &> /dev/null; then
        test_pass "Dapr namespace exists"

        # Check Dapr system pods
        DAPR_READY=$(kubectl get pods -n dapr-system --no-headers | grep -c "Running" || echo "0")
        DAPR_TOTAL=$(kubectl get pods -n dapr-system --no-headers | wc -l)
        if [ "${DAPR_READY}" -eq "${DAPR_TOTAL}" ] && [ "${DAPR_READY}" -gt 0 ]; then
            test_pass "All Dapr pods are running (${DAPR_READY}/${DAPR_TOTAL})"
        else
            test_fail "Some Dapr pods are not ready (${DAPR_READY}/${DAPR_TOTAL} running)"
        fi
    else
        test_fail "Dapr is not installed"
    fi
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
            BACKEND_TOTAL=$(echo "${BACKEND_PODS}" | wc -l)
            if [ "${BACKEND_READY}" -eq "${BACKEND_TOTAL}" ] && [ "${BACKEND_READY}" -gt 0 ]; then
                test_pass "Backend is running (${BACKEND_READY}/${BACKEND_TOTAL} pods ready)"
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
            FRONTEND_TOTAL=$(echo "${FRONTEND_PODS}" | wc -l)
            if [ "${FRONTEND_READY}" -eq "${FRONTEND_TOTAL}" ] && [ "${FRONTEND_READY}" -gt 0 ]; then
                test_pass "Frontend is running (${FRONTEND_READY}/${FRONTEND_TOTAL} pods ready)"
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
    if kubectl get service -n ${NAMESPACE} -l component=backend &> /dev/null; then
        test_pass "Backend service exists"
    else
        test_fail "Backend service does not exist"
    fi

    # Check frontend service
    if kubectl get service -n ${NAMESPACE} -l component=frontend &> /dev/null; then
        test_pass "Frontend service exists"
    else
        test_fail "Frontend service does not exist"
    fi
}

# Check ingress
check_ingress() {
    log_info "Checking ingress..."

    if kubectl get ingress -n ${NAMESPACE} &> /dev/null; then
        INGRESS_COUNT=$(kubectl get ingress -n ${NAMESPACE} --no-headers | wc -l)
        if [ "${INGRESS_COUNT}" -gt 0 ]; then
            test_pass "Ingress resources exist (${INGRESS_COUNT} found)"
        else
            test_fail "No ingress resources found"
        fi
    else
        test_fail "No ingress resources found"
    fi
}

# Check HPA
check_hpa() {
    log_info "Checking HorizontalPodAutoscalers..."

    HPA_COUNT=0

    # Check backend HPA
    if kubectl get hpa -n ${NAMESPACE} -l component=backend &> /dev/null; then
        test_pass "Backend HPA exists"
        HPA_COUNT=$((HPA_COUNT + 1))
    else
        log_warn "Backend HPA does not exist (autoscaling may be disabled)"
    fi

    # Check frontend HPA
    if kubectl get hpa -n ${NAMESPACE} -l component=frontend &> /dev/null; then
        test_pass "Frontend HPA exists"
        HPA_COUNT=$((HPA_COUNT + 1))
    else
        log_warn "Frontend HPA does not exist (autoscaling may be disabled)"
    fi

    if [ "${HPA_COUNT}" -gt 0 ]; then
        test_pass "HPA configuration is valid"
    fi
}

# Check Pod Disruption Budgets
check_pdb() {
    log_info "Checking PodDisruptionBudgets..."

    PDB_COUNT=$(kubectl get pdb -n ${NAMESPACE} --no-headers 2>/dev/null | wc -l)
    if [ "${PDB_COUNT}" -gt 0 ]; then
        test_pass "PodDisruptionBudgets exist (${PDB_COUNT} found)"
    else
        log_warn "No PodDisruptionBudgets found (recommended for production HA)"
    fi
}

# Check secrets
check_secrets() {
    log_info "Checking secrets..."

    # Check for required secrets
    REQUIRED_SECRETS=(
        "backend-secrets"
        "kafka-secrets"
    )

    for secret in "${REQUIRED_SECRETS[@]}"; do
        if kubectl get secret -n ${NAMESPACE} ${secret} &> /dev/null; then
            test_pass "Secret ${secret} exists"
        else
            test_fail "Secret ${secret} does not exist"
        fi
    done
}

# Display resource usage
display_resource_usage() {
    log_info "Resource usage in ${NAMESPACE} namespace:"

    echo "Pods:"
    kubectl top pods -n ${NAMESPACE} 2>/dev/null || log_warn "Metrics server not available"

    echo ""
    echo "Nodes:"
    kubectl top nodes 2>/dev/null || log_warn "Metrics server not available"
}

# Display pod status
display_pod_status() {
    log_info "Pod status in ${NAMESPACE} namespace:"
    kubectl get pods -n ${NAMESPACE} -o wide
}

# Main execution
main() {
    echo "=========================================="
    echo "Production Deployment Validation Test"
    echo "=========================================="
    echo ""

    check_kubectl
    check_namespace
    check_dapr
    check_backend
    check_frontend
    check_services
    check_ingress
    check_hpa
    check_pdb
    check_secrets

    echo ""
    display_pod_status

    echo ""
    display_resource_usage

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
