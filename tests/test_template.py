from core.model import RequestData, AuthConfig, AuthType
from core.template import render_request, render_text

def test_render_text_basic():
    variables = {"base_url": "https://api.example.com", "id": "123"}
    text = "{{base_url}}/users/{{id}}"
    rendered = render_text(text, variables)
    assert rendered == "https://api.example.com/users/123"

def test_render_text_missing_variable():
    variables = {"id": "123"}
    text = "{{base_url}}/users/{{id}}"
    rendered = render_text(text, variables)
    # Missing variable should be left as is (or empty string? implementation keeps it as matches if not found? 
    # Checking implementation: variables.get(key, match.group(0)) -> keeps original if not found)
    assert rendered == "{{base_url}}/users/123"

def test_render_request():
    variables = {
        "host": "api.test.com",
        "token": "secret_token",
        "user_id": "42"
    }
    
    request = RequestData(
        name="Get User",
        method="GET",
        url="https://{{host}}/users/{{user_id}}",
        headers=[("Authorization", "Bearer {{token}}"), ("X-Custom", "Fixed")],
        body='{"id": {{user_id}}}',
        auth=AuthConfig.bearer("{{token}}")
    )
    
    rendered = render_request(request, variables)
    
    assert rendered.url == "https://api.test.com/users/42"
    assert rendered.headers == [("Authorization", "Bearer secret_token"), ("X-Custom", "Fixed")]
    assert rendered.body == '{"id": 42}'
    assert rendered.auth.token == "secret_token"
    assert rendered.auth.auth_type == AuthType.BEARER

def test_render_text_whitespace_handling():
    # Test whitespace around variable names
    variables = {"var": "value"}
    
    assert render_text("{{var}}", variables) == "value"
    assert render_text("{{ var }}", variables) == "value"
    assert render_text("{{   var   }}", variables) == "value"
    assert render_text("Prefix {{ var }} Suffix", variables) == "Prefix value Suffix"

def test_render_text_multiple_variables():
    variables = {"a": "A", "b": "B", "c": "C"}
    text = "{{a}}-{{ b }}-{{c}}"
    assert render_text(text, variables) == "A-B-C"

def test_render_text_special_char_keys():
    # Regex allows [A-Za-z0-9_.-]+
    variables = {
        "user.name": "alice",
        "api-key": "12345",
        "underscore_var": "found"
    }
    
    assert render_text("{{user.name}}", variables) == "alice"
    assert render_text("{{api-key}}", variables) == "12345"
    assert render_text("{{underscore_var}}", variables) == "found"

def test_render_text_values_with_special_chars():
    variables = {"url": "https://example.com?q=1&f=2"}
    assert render_text("Go to {{url}}", variables) == "Go to https://example.com?q=1&f=2"

def test_render_text_no_recursive_substitution():
    # Ensure it's a single pass substitution to prevent infinite loops
    variables = {
        "first": "{{second}}",
        "second": "final"
    }
    
    # Should resolve "first" to "{{second}}", not "final"
    assert render_text("Result: {{first}}", variables) == "Result: {{second}}"

def test_render_text_undefined_variables_preserved():
    variables = {"a": "A"}
    text = "{{a}} {{b}} {{ c }}"
    # {{b}} and {{ c }} should be preserved exactly as input if not found
    assert render_text(text, variables) == "A {{b}} {{ c }}"

def test_render_request_multipart():
    variables = {
        "user": "alice",
        "filename": "report.pdf"
    }
    
    request = RequestData(
        name="Upload",
        method="POST",
        url="https://api.com/upload",
        body_type="multipart",
        form_fields=[("user", "{{user}}"), ("type", "daily")],
        files=[("doc", "/tmp/{{filename}}")]
    )
    
    rendered = render_request(request, variables)
    
    assert rendered.body_type == "multipart"
    assert rendered.form_fields == [("user", "alice"), ("type", "daily")]
    assert rendered.files == [("doc", "/tmp/report.pdf")]
