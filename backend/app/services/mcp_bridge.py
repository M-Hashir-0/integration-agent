import requests
import re
import yaml
import json
from pydantic import BaseModel, create_model
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from langchain_core.tools import StructuredTool

from app.services.security import get_auth_headers
from app.utils.logger import get_logger

logger = get_logger("MCP_Bridge")


class OpenAPIMCPBridge:
    def __init__(self, api_name: str, spec_url: str, connection_name: str):
        self.api_name = api_name
        self.spec_url = spec_url
        self.connection_name = connection_name

        self.mcp = FastMCP(api_name)

        self._generated_tools: List[StructuredTool] = []

        logger.info(
            f"Initialized Bridge for {api_name} (Connection: {connection_name})")

    def fetch_spec(self) -> Dict[str, Any]:
        """Fetches and parses the OpenAPI spec."""
        try:
            logger.info(f"Fetching spec from: {self.spec_url}")
            response = requests.get(self.spec_url)
            response.raise_for_status()

            # check if accidentally downloaded HTML
            content_type = response.headers.get("Content-Type", "")
            if "text/html" in content_type:
                logger.error(
                    "URL returned HTML instead of JSON/YAML.")
                raise ValueError(
                    "The URL returned an HTML page. Please use the 'Raw' URL.")

            try:
                return response.json()
            except json.JSONDecodeError:
                return yaml.safe_load(response.text)

        except Exception as e:
            logger.error(f"Spec fetch failed: {e}")
            raise RuntimeError(f"Could not fetch spec: {e}")

    def register_tools(self):
        """
        Parses the spec and dynamically registers tools to the MCP server.
        """
        spec = self.fetch_spec()

        base_url = "https://api.example.com"

        # OpenAPI 3.0 'servers' array
        if "servers" in spec and spec["servers"]:
            base_url = spec["servers"][0].get("url", "")

        # Strategy B: Swagger 2.0 'host' + 'basePath'
        elif "host" in spec:
            scheme = spec.get("schemes", ["https"])[0]
            host = spec["host"]
            base_path = spec.get("basePath", "")
            base_url = f"{scheme}://{host}{base_path}"

        else:
            logger.warning(
                "Could not determine Base URL. Defaulting to example.com")

        if base_url.endswith("/"):
            base_url = base_url[:-1]

        paths = spec.get("paths", {})
        tool_count = 0

        for path, methods in paths.items():
            for method, details in methods.items():
                if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                    continue

                op_id = details.get("operationId")
                if not op_id:
                    clean_path = path.replace(
                        "/", "_").replace("{", "").replace("}", "")
                    op_id = f"{method.lower()}{clean_path}"

                # building a rich description for better semantic search
                base_description = details.get("summary") or details.get(
                    "description") or "No description."

                # extracting parameter information to enhance description
                params_info = []
                parameters = details.get("parameters", [])
                for param in parameters:
                    param_name = param.get("name", "")
                    param_desc = param.get("description", "")
                    param_in = param.get("in", "")
                    if param_name and param_in == "path":
                        params_info.append(
                            f"Uses {param_name} parameter ({param_desc})")

                description = base_description
                if params_info:
                    description = f"{base_description}. {'. '.join(params_info)}."

                # We use a closure to capture the specific path, method, and base_url
                # Build a Pydantic args schema for better typing/validation
                # Map OpenAPI basic types to Python types
                def _map_openapi_type(t: str):
                    t = (t or "").lower()
                    if t == "integer":
                        return int
                    if t == "number":
                        return float
                    if t == "boolean":
                        return bool
                    if t == "array":
                        return List[Any]
                    if t == "object":
                        return Dict[str, Any]
                    return str

                args_fields: Dict[str, Any] = {}
                for param in parameters:
                    name = param.get("name")
                    if not name:
                        continue
                    required = bool(param.get("required", False))
                    schema = param.get("schema", {}) or {}
                    inferred_type = _map_openapi_type(schema.get("type"))
                    if param.get("in") == "path" and (name.lower().endswith("id") or inferred_type is int):
                        inferred_type = int

                    default = ... if required else None
                    if not required and inferred_type is not Any and inferred_type is not List[Any] and inferred_type is not Dict[str, Any]:
                        args_fields[name] = (
                            Optional[inferred_type], default)
                    else:
                        args_fields[name] = (inferred_type, default)

                ArgsModel: BaseModel
                if args_fields:
                    model_name = f"{self.api_name}_{op_id}_Args"
                    # pydantic create_model will handle Optional/required semantics via default
                    ArgsModel = create_model(
                        model_name, **args_fields)  # type: ignore
                else:
                    # Fallback empty model
                    ArgsModel = create_model(
                        f"{self.api_name}_{op_id}_Args")  # type: ignore

                def make_handler(p=path, m=method, b=base_url, c_name=self.connection_name):
                    def handler(**kwargs):
                        """
                        Dynamic handler that forwards the request to the real API.
                        accepts **kwargs for dynamic arguments.
                        """
                        # Unwrap if the arguments are nested in a 'kwargs' key
                        if len(kwargs) == 1 and 'kwargs' in kwargs:
                            kwargs = kwargs['kwargs']

                        # auth injection
                        try:
                            headers = get_auth_headers(c_name)
                        except ValueError:
                            logger.warning(
                                f"No credentials found for {c_name}, proceeding without auth.")
                            headers = {}

                        # URL Construction
                        url = f"{b}{p}"

                        # Track which kwargs are used for path params
                        path_params_used = set()
                        for key, value in list(kwargs.items()):
                            placeholder = f"{{{key}}}"
                            if placeholder in url:
                                if isinstance(value, float):
                                    if value.is_integer():
                                        value = int(value)
                                        kwargs[key] = value
                                    else:
                                        return f"Invalid value for path parameter '{key}': non-integer float {value}"

                                url = url.replace(placeholder, str(value))
                                path_params_used.add(key)

                        logger.info(f"Executing {m.upper()} {url}")

                        try:
                            if m.lower() == "get":
                                # For GET, remaining kwargs (not used in path) go to Query Params
                                query_params = {
                                    k: v for k, v in kwargs.items() if k not in path_params_used}
                                resp = requests.get(
                                    url, params=query_params, headers=headers)
                            else:
                                # For POST/PUT, kwargs go to Body (JSON)
                                resp = requests.post(
                                    url, json=kwargs, headers=headers)

                            if resp.status_code >= 400:
                                logger.error(
                                    f"API Error {resp.status_code}: {resp.text}")
                                return f"Error {resp.status_code}: {resp.text}"

                            return resp.json()
                        except Exception as e:
                            return f"Connection Failed: {str(e)}"

                    return handler

                func = make_handler(path, method, base_url)
                func.__name__ = op_id
                func.__doc__ = description

                # converting the python function into a StructuredTool for the Agent
                lc_tool = StructuredTool.from_function(
                    func=func,
                    name=op_id,
                    description=description,
                    args_schema=ArgsModel
                )
                self._generated_tools.append(lc_tool)

                self.mcp.tool()(func)
                tool_count += 1

        logger.info(
            f"Successfully registered {tool_count} tools for {self.api_name}")

    def get_tools(self) -> List[StructuredTool]:
        """Returns the list of LangChain-compatible tools."""
        return self._generated_tools

    def start(self):
        """Starts the MCP server."""
        logger.info(f"Starting MCP Server for {self.api_name}...")
        self.mcp.run()
