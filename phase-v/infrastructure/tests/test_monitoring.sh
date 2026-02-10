#!/bin/bash
#
# test_monitoring.sh - Monitoring stack validation test
#
# T154: Verify Prometheus, Grafana, and Loki are running correctly
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
MONITORING_NAMESPACE="monitoring"
APP_NAMESPACE="todo-app"
TIMEOUT=300  # 5 minutes
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

# Check if monitoring namespace exists
check_monitoring_namespace() {
    log_info "Checking monitoring namespace..."
    if kubectl get namespace ${MONITORING_NAMESPACE} &> /dev/null; then
        test_pass "Monitoring namespace exists"
    else
        test_fail "Monitoring namespace does not exist"
    fi
}

# Check Prometheus deployment
check_prometheus() {
    log_info "Checking Prometheus deployment..."

    # Wait for Prometheus pods to be ready
    PROMETHEUS_READY=0
    ELAPSED=0
    while [ ${ELAPSED} -lt ${TIMEOUT} ]; do
        PROMETHEUS_PODS=$(kubectl get pods -n ${MONITORING_NAMESPACE} -l app=prometheus --no-headers 2>/dev/null || echo "")
        if [ -n "${PROMETHEUS_PODS}" ]; then
            PROMETHEUS_READY=$(echo "${PROMETHEUS_PODS}" | grep -c "Running" || echo "0")
            PROMETHEUS_TOTAL=$(echo "${PROMETHEUS_PODS}" | wc -l)
            if [ "${PROMETHEUS_READY}" -eq "${PROMETHEUS_TOTAL}" ] && [ "${PROMETHEUS_READY}" -gt 0 ]; then
                test_pass "Prometheus is running (${PROMETHEUS_READY}/${PROMETHEUS_TOTAL} pods ready)"
                break
            fi
        fi
        sleep ${RETRY_INTERVAL}
        ELAPSED=$((ELAPSED + RETRY_INTERVAL))
        echo -n "."
    done

    if [ ${ELAPSED} -ge ${TIMEOUT} ]; then
        test_fail "Prometheus did not become ready within ${TIMEOUT} seconds"
        return
    fi

    # Check Prometheus service
    if kubectl get service -n ${MONITORING_NAMESPACE} prometheus &> /dev/null; then
        test_pass "Prometheus service exists"
    else
        test_fail "Prometheus service does not exist"
    fi

    # Check Prometheus is scraping metrics
    log_info "Checking Prometheus metrics..."
    PROMETHEUS_POD=$(kubectl get pods -n ${MONITORING_NAMESPACE} -l app=prometheus -o jsonpath='{.items[0].metadata.name}')
    METRICS_COUNT=$(kubectl exec -n ${MONITORING_NAMESPACE} ${PROMETHEUS_POD} -- wget -qO- http://localhost:9090/api/v1/label/__name__/values 2>/dev/null | grep -o "http_requests_total" | wc -l || echo "0")

    if [ "${METRICS_COUNT}" -gt 0 ]; then
        test_pass "Prometheus is collecting metrics (found http_requests_total)"
    else
        log_warn "Prometheus may not be collecting metrics yet"
    fi
}

# Check Grafana deployment
check_grafana() {
    log_info "Checking Grafana deployment..."

    # Wait for Grafana pods to be ready
    GRAFANA_READY=0
    ELAPSED=0
    while [ ${ELAPSED} -lt ${TIMEOUT} ]; do
        GRAFANA_PODS=$(kubectl get pods -n ${MONITORING_NAMESPACE} -l app=grafana --no-headers 2>/dev/null || echo "")
        if [ -n "${GRAFANA_PODS}" ]; then
            GRAFANA_READY=$(echo "${GRAFANA_PODS}" | grep -c "Running" || echo "0")
            GRAFANA_TOTAL=$(echo "${GRAFANA_PODS}" | wc -l)
            if [ "${GRAFANA_READY}" -eq "${GRAFANA_TOTAL}" ] && [ "${GRAFANA_READY}" -gt 0 ]; then
                test_pass "Grafana is running (${GRAFANA_READY}/${GRAFANA_TOTAL} pods ready)"
                break
            fi
        fi
        sleep ${RETRY_INTERVAL}
        ELAPSED=$((ELAPSED + RETRY_INTERVAL))
        echo -n "."
    done

    if [ ${ELAPSED} -ge ${TIMEOUT} ]; then
        test_fail "Grafana did not become ready within ${TIMEOUT} seconds"
        return
    fi

    # Check Grafana service
    if kubectl get service -n ${MONITORING_NAMESPACE} grafana &> /dev/null; then
        test_pass "Grafana service exists"
    else
        test_fail "Grafana service does not exist"
    fi

    # Check Grafana datasources
    log_info "Checking Grafana datasources..."
    GRAFANA_POD=$(kubectl get pods -n ${MONITORING_NAMESPACE} -l app=grafana -o jsonpath='{.items[0].metadata.name}')

    # Check if Prometheus datasource is configured
    DATASOURCES=$(kubectl exec -n ${MONITORING_NAMESPACE} ${GRAFANA_POD} -- wget -qO- http://localhost:3000/api/datasources --header="Content-Type: application/json" 2>/dev/null || echo "")

    if echo "${DATASOURCES}" | grep -q "Prometheus"; then
        test_pass "Grafana Prometheus datasource is configured"
    else
        log_warn "Grafana Prometheus datasource may not be configured"
    fi
}

# Check Loki deployment
check_loki() {
    log_info "Checking Loki deployment..."

    # Wait for Loki pods to be ready
    LOKI_READY=0
    ELAPSED=0
    while [ ${ELAPSED} -lt ${TIMEOUT} ]; do
        LOKI_PODS=$(kubectl get pods -n ${MONITORING_NAMESPACE} -l app=loki --no-headers 2>/dev/null || echo "")
        if [ -n "${LOKI_PODS}" ]; then
            LOKI_READY=$(echo "${LOKI_PODS}" | grep -c "Running" || echo "0")
            LOKI_TOTAL=$(echo "${LOKI_PODS}" | wc -l)
            if [ "${LOKI_READY}" -eq "${LOKI_TOTAL}" ] && [ "${LOKI_READY}" -gt 0 ]; then
                test_pass "Loki is running (${LOKI_READY}/${LOKI_TOTAL} pods ready)"
                break
            fi
        fi
        sleep ${RETRY_INTERVAL}
        ELAPSED=$((ELAPSED + RETRY_INTERVAL))
        echo -n "."
    done

    if [ ${ELAPSED} -ge ${TIMEOUT} ]; then
        test_fail "Loki did not become ready within ${TIMEOUT} seconds"
        return
    fi

    # Check Loki service
    if kubectl get service -n ${MONITORING_NAMESPACE} loki &> /dev/null; then
        test_pass "Loki service exists"
    else
        test_fail "Loki service does not exist"
    fi
}

# Check application metrics endpoint
check_application_metrics() {
    log_info "Checking application metrics endpoint..."

    # Check if backend service has metrics endpoint
    if kubectl get service -n ${APP_NAMESPACE} backend-service &> /dev/null; then
        test_pass "Backend service exists"

        # Port forward to check metrics endpoint
        log_info "Checking /metrics endpoint on backend..."
        kubectl port-forward -n ${APP_NAMESPACE} svc/backend-service 8000:8000 > /dev/null 2>&1 &
        PF_PID=$!
        sleep 5

        METRICS_RESPONSE=$(curl -s http://localhost:8000/metrics 2>/dev/null || echo "")
        kill ${PF_PID} 2>/dev/null || true

        if echo "${METRICS_RESPONSE}" | grep -q "http_requests_total"; then
            test_pass "Backend /metrics endpoint is working"
        else
            test_fail "Backend /metrics endpoint is not returning metrics"
        fi
    else
        test_fail "Backend service does not exist"
    fi
}

# Check Prometheus alerts
check_prometheus_alerts() {
    log_info "Checking Prometheus alerting rules..."

    # Check if alert rules ConfigMap exists
    if kubectl get configmap -n ${MONITORING_NAMESPACE} prometheus-rules &> /dev/null; then
        test_pass "Prometheus alert rules ConfigMap exists"
    else
        log_warn "Prometheus alert rules ConfigMap does not exist"
    fi
}

# Display monitoring stack status
display_monitoring_status() {
    log_info "Monitoring stack status:"
    kubectl get pods -n ${MONITORING_NAMESPACE}

    log_info "Services:"
    kubectl get services -n ${MONITORING_NAMESPACE}
}

# Main execution
main() {
    echo "=========================================="
    echo "Monitoring Stack Validation Test"
    echo "=========================================="
    echo ""

    check_monitoring_namespace
    check_prometheus
    check_grafana
    check_loki
    check_application_metrics
    check_prometheus_alerts

    echo ""
    display_monitoring_status

    echo ""
    echo "=========================================="
    echo "Test Summary"
    echo "=========================================="
    echo "Passed: ${TESTS_PASSED}"
    echo "Failed: ${TESTS_FAILED}"
    echo ""

    if [ ${TESTS_FAILED} -eq 0 ]; then
        log_info "All tests passed!"
        log_info "Access Grafana: kubectl port-forward -n ${MONITORING_NAMESPACE} svc/grafana 3000:80"
        log_info "Access Prometheus: kubectl port-forward -n ${MONITORING_NAMESPACE} svc/prometheus 9090:9090"
        exit 0
    else
        log_error "Some tests failed!"
        exit 1
    fi
}

# Run main function
main "$@"
