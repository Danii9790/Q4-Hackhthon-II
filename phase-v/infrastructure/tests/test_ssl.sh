#!/bin/bash
#
# test_ssl.sh - SSL/TLS validation test
#
# T132: This test verifies that SSL/TLS is properly configured
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="${NAMESPACE:-todo-app}"
INGRESS_NAME="${INGRESS_NAME:-todo-chatbot-frontend-ingress}"

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

# Check if ingress has TLS configured
check_ingress_tls() {
    log_info "Checking ingress TLS configuration..."

    if ! kubectl get ingress -n ${NAMESPACE} ${INGRESS_NAME} &> /dev/null; then
        test_fail "Ingress ${INGRESS_NAME} not found"
        return 1
    fi

    TLS_CONFIG=$(kubectl get ingress -n ${NAMESPACE} ${INGRESS_NAME} -o jsonpath='{.spec.tls}')

    if [ -n "${TLS_CONFIG}" ]; then
        test_pass "Ingress has TLS configuration"

        # Extract TLS secret name
        TLS_SECRET=$(kubectl get ingress -n ${NAMESPACE} ${INGRESS_NAME} -o jsonpath='{.spec.tls[0].secretName}')
        log_info "TLS Secret: ${TLS_SECRET}"

        # Check if TLS secret exists
        if kubectl get secret -n ${NAMESPACE} ${TLS_SECRET} &> /dev/null; then
            test_pass "TLS secret ${TLS_SECRET} exists"
        else
            test_fail "TLS secret ${TLS_SECRET} does not exist"
        fi
    else
        test_fail "Ingress does not have TLS configuration"
    fi
}

# Check if cert-manager is installed
check_cert_manager() {
    log_info "Checking cert-manager installation..."

    if kubectl get namespace cert-manager &> /dev/null; then
        test_pass "cert-manager namespace exists"

        # Check cert-manager pods
        CERT_MANAGER_PODS=$(kubectl get pods -n cert-manager --no-headers 2>/dev/null | wc -l)
        if [ "${CERT_MANAGER_PODS}" -gt 0 ]; then
            test_pass "cert-manager pods are running (${CERT_MANAGER_PODS} pods)"
        else
            log_warn "No cert-manager pods found"
        fi

        # Check for ClusterIssuer
        if kubectl get clusterissuer letsencrypt-prod &> /dev/null; then
            test_pass "Let's Encrypt ClusterIssuer exists"
        else
            log_warn "Let's Encrypt ClusterIssuer not found (may be using custom TLS)"
        fi
    else
        log_warn "cert-manager is not installed (using manual TLS)"
    fi
}

# Check certificate validity
check_certificate() {
    log_info "Checking certificate validity..."

    # Get TLS secret from ingress
    TLS_SECRET=$(kubectl get ingress -n ${NAMESPACE} ${INGRESS_NAME} -o jsonpath='{.spec.tls[0].secretName}' 2>/dev/null)

    if [ -z "${TLS_SECRET}" ]; then
        test_fail "No TLS secret found in ingress"
        return 1
    fi

    # Extract certificate
    CERT=$(kubectl get secret -n ${NAMESPACE} ${TLS_SECRET} -o jsonpath='{.data.tls\.crt}' 2>/dev/null)

    if [ -z "${CERT}" ]; then
        test_fail "No certificate found in secret ${TLS_SECRET}"
        return 1
    fi

    # Decode and check certificate
    CERT_INFO=$(echo "${CERT}" | base64 -d | openssl x509 -noout -text 2>/dev/null || echo "")

    if [ -z "${CERT_INFO}" ]; then
        test_fail "Failed to parse certificate"
        return 1
    fi

    # Extract expiration date
    EXPIRATION=$(echo "${CERT_INFO}" | grep "Not After" | cut -d':' -f2- | awk '{print $1, $2, $4}')
    log_info "Certificate expires: ${EXPIRATION}"

    # Check if certificate is expired
    EXPIRATION_EPOCH=$(date -d "${EXPIRATION}" +%s 2>/dev/null || echo "0")
    CURRENT_EPOCH=$(date +%s)

    if [ "${EXPIRATION_EPOCH}" -gt "${CURRENT_EPOCH}" ]; then
        test_pass "Certificate is valid and not expired"

        # Check if certificate expires within 30 days
        DAYS_UNTIL_EXPIRATION=$(( (${EXPIRATION_EPOCH} - ${CURRENT_EPOCH}) / 86400 ))
        if [ "${DAYS_UNTIL_EXPIRATION}" -lt 30 ]; then
            log_warn "Certificate expires in ${DAYS_UNTIL_EXPIRATION} days (renewal needed soon)"
        else
            log_info "Certificate expires in ${DAYS_UNTIL_EXPIRATION} days"
        fi
    else
        test_fail "Certificate is expired!"
    fi
}

# Test HTTPS connectivity
test_https_connectivity() {
    log_info "Testing HTTPS connectivity..."

    # Get ingress host
    INGRESS_HOST=$(kubectl get ingress -n ${NAMESPACE} ${INGRESS_NAME} -o jsonpath='{.spec.rules[0].host}' 2>/dev/null)

    if [ -z "${INGRESS_HOST}" ]; then
        log_warn "No ingress host found, skipping connectivity test"
        return
    fi

    log_info "Testing connectivity to: https://${INGRESS_HOST}"

    # Test with curl (if available)
    if command -v curl &> /dev/null; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://${INGRESS_HOST}" 2>/dev/null || echo "000")

        if [ "${HTTP_CODE}" = "000" ]; then
            log_warn "Could not connect to ${INGRESS_HOST} (DNS or network issue)"
        elif [ "${HTTP_CODE}" -ge 200 ] && [ "${HTTP_CODE}" -lt 500 ]; then
            test_pass "HTTPS connectivity successful (HTTP ${HTTP_CODE})"
        else
            test_fail "HTTPS connection failed (HTTP ${HTTP_CODE})"
        fi
    else
        log_warn "curl not available, skipping connectivity test"
    fi
}

# Display certificate details
display_certificate_details() {
    log_info "Certificate details:"

    TLS_SECRET=$(kubectl get ingress -n ${NAMESPACE} ${INGRESS_NAME} -o jsonpath='{.spec.tls[0].secretName}' 2>/dev/null)

    if [ -n "${TLS_SECRET}" ]; then
        CERT=$(kubectl get secret -n ${NAMESPACE} ${TLS_SECRET} -o jsonpath='{.data.tls\.crt}' 2>/dev/null)
        if [ -n "${CERT}" ]; then
            echo "${CERT}" | base64 -d | openssl x509 -noout -text | grep -E "(Subject:|Issuer:|Not Before|Not After|DNS:)"
        fi
    fi
}

# Main execution
main() {
    echo "=========================================="
    echo "SSL/TLS Validation Test"
    echo "=========================================="
    echo ""

    check_ingress_tls
    check_cert_manager
    check_certificate
    test_https_connectivity

    echo ""
    display_certificate_details

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
