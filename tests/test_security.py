import pytest
from src.security.secret_scanner import SecretScanner
from pathlib import Path

def test_ignore_env_files():
    scanner = SecretScanner()
    assert scanner.is_file_allowed(Path(".env")) == False
    assert scanner.is_file_allowed(Path(".env.local")) == False
    assert scanner.is_file_allowed(Path(".env.production")) == False
    assert scanner.is_file_allowed(Path("src/.env")) == False

def test_ignore_secrets_files():
    scanner = SecretScanner()
    assert scanner.is_file_allowed(Path("credentials")) == False
    assert scanner.is_file_allowed(Path("secrets.json")) == False
    assert scanner.is_file_allowed(Path("id_rsa")) == False
    assert scanner.is_file_allowed(Path("cert.pem")) == False
    assert scanner.is_file_allowed(Path("key.key")) == False
    
def test_allow_normal_files():
    scanner = SecretScanner()
    assert scanner.is_file_allowed(Path("app.py")) == True
    assert scanner.is_file_allowed(Path("src/components/Button.jsx")) == True
    assert scanner.is_file_allowed(Path("README.md")) == True
    
def test_scan_content_aws_keys():
    scanner = SecretScanner()
    assert scanner.scan_content("export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE") == True
    
def test_scan_content_gcp_keys():
    scanner = SecretScanner()
    assert scanner.scan_content("const key = 'AIzaSyA-bC1dE2fG3hI4jK5lM6nO7pQ8rS9tU0v'") == True

def test_scan_content_generic_secrets():
    scanner = SecretScanner()
    assert scanner.scan_content('api_key = "sk-1234567890abcdef1234567890abcdef1234567890abcdef"') == True
    assert scanner.scan_content('password: "supersecret"') == True
    assert scanner.scan_content('TOKEN = "xyz"') == True

def test_scan_content_safe():
    scanner = SecretScanner()
    assert scanner.scan_content("const a = 1;") == False
    assert scanner.scan_content('console.log("hello world")') == False
    assert scanner.scan_content("def is_valid_password(password):") == False
