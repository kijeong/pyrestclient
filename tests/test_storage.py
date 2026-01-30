import tempfile
from pathlib import Path
from core.model import WorkspaceRequest, AuthConfig, AuthType, NetworkConfig
from core.storage.json_storage import JsonWorkspaceStorage, save_workspace, load_workspace, WorkspaceData

def test_workspace_request_persistence_multipart():
    # Create a temporary file for the workspace
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    
    try:
        # Create a workspace with a multipart request
        request = WorkspaceRequest(
            id="req-1",
            folder_id="folder-1",
            name="Upload File",
            method="POST",
            url="https://example.com/upload",
            body_type="multipart",
            form_fields=[("username", "testuser"), ("description", "file upload")],
            files=[("document", "/path/to/file.txt")],
            body="", # Should be ignored or empty for multipart
            auth=AuthConfig.none(),
            timeout_ms=5000,
            network=NetworkConfig()
        )
        
        workspace = WorkspaceData(
            schema_version=1,
            requests=[request]
        )
        
        # Save
        save_workspace(tmp_path, workspace)
        
        # Load
        loaded_workspace = load_workspace(tmp_path)
        
        assert len(loaded_workspace.requests) == 1
        loaded_req = loaded_workspace.requests[0]
        
        assert loaded_req.id == "req-1"
        assert loaded_req.body_type == "multipart"
        assert loaded_req.form_fields == [("username", "testuser"), ("description", "file upload")]
        assert loaded_req.files == [("document", "/path/to/file.txt")]
        assert loaded_req.body == ""

    finally:
        if tmp_path.exists():
            tmp_path.unlink()
