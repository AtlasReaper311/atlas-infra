package main

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"net/http"
	"os"
	"time"
)

const (
	defaultCAPath = "/run/qdrant-tls/ca.pem"
	defaultHost   = "qdrant"
)

func main() {
	caPath := os.Getenv("QDRANT_HEALTHCHECK_CA")
	if caPath == "" {
		caPath = defaultCAPath
	}
	caBytes, err := os.ReadFile(caPath)
	if err != nil {
		fail(err)
	}
	roots := x509.NewCertPool()
	if !roots.AppendCertsFromPEM(caBytes) {
		fail(fmt.Errorf("could not parse CA certificate"))
	}

	host := os.Getenv("QDRANT_HEALTHCHECK_HOST")
	if host == "" {
		host = defaultHost
	}
	transport := &http.Transport{
		TLSClientConfig: &tls.Config{
			MinVersion: tls.VersionTLS13,
			RootCAs:    roots,
			ServerName: host,
		},
	}
	client := &http.Client{Timeout: 2 * time.Second, Transport: transport}
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	request, err := http.NewRequestWithContext(ctx, http.MethodGet, "https://"+host+":6333/healthz", nil)
	if err != nil {
		fail(err)
	}
	response, err := client.Do(request)
	if err != nil {
		fail(err)
	}
	defer response.Body.Close()
	if response.StatusCode != http.StatusOK {
		fail(fmt.Errorf("health endpoint returned %s", response.Status))
	}
}

func fail(err error) {
	_, _ = fmt.Fprintln(os.Stderr, err)
	os.Exit(1)
}
