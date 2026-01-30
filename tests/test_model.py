from core.model import AuthConfig, AuthType

def test_auth_config_factories():
    # Test none factory
    auth_none = AuthConfig.none()
    assert auth_none.auth_type == AuthType.NONE
    assert auth_none.username == ""
    assert auth_none.password == ""
    assert auth_none.token == ""

    # Test basic factory
    auth_basic = AuthConfig.basic("user", "pass")
    assert auth_basic.auth_type == AuthType.BASIC
    assert auth_basic.username == "user"
    assert auth_basic.password == "pass"
    assert auth_basic.token == ""

    # Test bearer factory
    auth_bearer = AuthConfig.bearer("xyz_token")
    assert auth_bearer.auth_type == AuthType.BEARER
    assert auth_bearer.username == ""
    assert auth_bearer.password == ""
    assert auth_bearer.token == "xyz_token"
