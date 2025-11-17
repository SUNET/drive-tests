"""
Auto-generated API tests from OpenAPI specification
Generated from: nextcloud
Version: 0.0.1
"""

import json
import pytest
import requests
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import os


# ============================================================================
# HELPER CLASSES
# ============================================================================


@dataclass
class RequestConfig:
    """Configuration for API requests"""

    base_url: str = "http://localhost"
    headers: Dict[str, str] = field(default_factory=dict)
    auth: Optional[tuple] = None
    bearer_token: Optional[str] = None
    verify_ssl: bool = True
    timeout: int = 30


@dataclass
class TestParameter:
    """Test parameter data"""

    name: str
    value: Any
    location: str  # path, query, header, body


@dataclass
class ResponseAssertion:
    """Response assertion rules"""

    status_code: Optional[int] = None
    json_schema: Optional[Dict] = None
    json_contains: Optional[Dict] = None
    headers_contain: Optional[Dict] = None


@dataclass
class TestCase:
    """Single test case data"""

    description: str
    parameters: List[TestParameter] = field(default_factory=list)
    assertions: ResponseAssertion = field(default_factory=ResponseAssertion)
    skip: bool = False
    skip_reason: str = ""


class ParameterHelper:
    """Helper class for managing parameters"""

    @staticmethod
    def extract_parameters(test_case: TestCase) -> tuple:
        """Extract parameters by location"""
        path_params = {}
        query_params = {}
        headers = {}
        body = None

        for param in test_case.parameters:
            if param.location == "path":
                path_params[param.name] = param.value
            elif param.location == "query":
                query_params[param.name] = param.value
            elif param.location == "header":
                headers[param.name] = param.value
            elif param.location == "body":
                body = param.value

        return path_params, query_params, headers, body

    @staticmethod
    def set_defaults(params: Dict, defaults: Dict) -> Dict:
        """Set default values for missing parameters"""
        result = params.copy()
        for key, value in defaults.items():
            if key not in result:
                result[key] = value
        return result


class ResponseHelper:
    """Helper class for response validation"""

    @staticmethod
    def assert_status(response: requests.Response, expected: int, test_desc: str):
        """Assert response status code"""
        assert response.status_code == expected, (
            f"{test_desc} - Expected status {expected}, got {response.status_code}. Body: {response.text[:200]}"
        )

    @staticmethod
    def assert_json_contains(
        response: requests.Response, expected: Dict, test_desc: str
    ):
        """Assert response JSON contains expected keys and values"""
        try:
            response_data = response.json()
            for key, value in expected.items():
                assert key in response_data, (
                    f'{test_desc} - Key "{key}" not in response'
                )
                if value is not None:
                    assert response_data[key] == value, (
                        f"{test_desc} - Expected {key}={value}, got {response_data[key]}"
                    )
        except json.JSONDecodeError:
            pytest.fail(
                f"{test_desc} - Response is not valid JSON: {response.text[:200]}"
            )

    @staticmethod
    def assert_headers(response: requests.Response, expected: Dict, test_desc: str):
        """Assert response headers"""
        for key, value in expected.items():
            assert key in response.headers, (
                f'{test_desc} - Header "{key}" not in response'
            )
            if value is not None:
                assert response.headers[key] == value, (
                    f"{test_desc} - Expected header {key}={value}, got {response.headers[key]}"
                )


class APITestHelper:
    """Main helper class for API testing"""

    def __init__(self, config: RequestConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(config.headers)

        if config.bearer_token:
            self.session.headers["Authorization"] = f"Bearer {config.bearer_token}"
        elif config.auth:
            self.session.auth = config.auth

    def build_url(self, path: str, path_params: Dict[str, Any]) -> str:
        """Build URL with path parameters"""
        url = self.config.base_url + path
        for key, value in path_params.items():
            url = url.replace(f"{{{key}}}", str(value))
        return url

    def execute_request(
        self,
        method: str,
        path: str,
        path_params: Optional[Dict[str, Any]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        body: Any = None,
    ) -> requests.Response:
        """Execute an API request"""
        path_params = path_params or {}
        query_params = query_params or {}
        headers = headers or {}

        url = self.build_url(path, path_params)

        # Merge headers
        request_headers = {**self.session.headers, **headers}

        return self.session.request(
            method=method.upper(),
            url=url,
            params=query_params,
            headers=request_headers,
            json=body if isinstance(body, dict) else None,
            data=body if body and not isinstance(body, dict) else None,
            verify=self.config.verify_ssl,
            timeout=self.config.timeout,
        )

    @staticmethod
    def load_test_data(file_path: Union[str, Path]) -> Dict[str, List[TestCase]]:
        """Load test data from JSON file"""
        if not Path(file_path).exists():
            return {}

        with open(file_path, "r") as f:
            data = json.load(f)

        test_cases = {}
        for operation_id, cases in data.items():
            test_cases[operation_id] = []
            for case_data in cases:
                parameters = [
                    TestParameter(**p) for p in case_data.get("parameters", [])
                ]

                assertions_data = case_data.get("assertions", {})
                assertions = ResponseAssertion(
                    status_code=assertions_data.get("status_code", 200),
                    json_schema=assertions_data.get("json_schema"),
                    json_contains=assertions_data.get("json_contains"),
                    headers_contain=assertions_data.get("headers_contain"),
                )

                test_cases[operation_id].append(
                    TestCase(
                        description=case_data.get("description", ""),
                        parameters=parameters,
                        assertions=assertions,
                        skip=case_data.get("skip", False),
                        skip_reason=case_data.get("skip_reason", ""),
                    )
                )
        return test_cases


# ============================================================================
# CONFIGURATION
# ============================================================================

# Load test configuration
TEST_CONFIG = RequestConfig(
    base_url=os.environ.get("OPENAPI_URL"),
    headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
        "OCS-APIRequest": "true",
    },
    # headers={"OCS-APIRequest": "true"},
    verify_ssl=True,
    auth=(
        os.environ.get("OPENAPI_USER"),
        os.environ.get("OPENAPI_APP_PASSWORD"),
    ),
)

# Load test data
TEST_DATA_FILE = Path(__file__).parent / "test_api_data.json"
TEST_DATA = APITestHelper.load_test_data(TEST_DATA_FILE)


# ============================================================================
# TEST CLASSES
# ============================================================================


class TestGetSimplePaths:
    """GET endpoint tests"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test helper"""
        self.helper = APITestHelper(TEST_CONFIG)
        self.param_helper = ParameterHelper()
        self.response_helper = ResponseHelper()

    def test_core_app_password_get_app_password(self):
        """
        Test: core-app_password-get-app-password
        Method: GET
        Path: /ocs/v2.php/core/getapppassword
        """
        operation_id = "core-app_password-get-app-password"
        method = "get"
        path = "/ocs/v2.php/core/getapppassword"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_auto_complete_get(self):
        """
        Test: core-auto_complete-get
        Method: GET
        Path: /ocs/v2.php/core/autocomplete/get
        """
        operation_id = "core-auto_complete-get"
        method = "get"
        path = "/ocs/v2.php/core/autocomplete/get"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_navigation_get_apps_navigation(self):
        """
        Test: core-navigation-get-apps-navigation
        Method: GET
        Path: /ocs/v2.php/core/navigation/apps
        """
        operation_id = "core-navigation-get-apps-navigation"
        method = "get"
        path = "/ocs/v2.php/core/navigation/apps"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_navigation_get_settings_navigation(self):
        """
        Test: core-navigation-get-settings-navigation
        Method: GET
        Path: /ocs/v2.php/core/navigation/settings
        """
        operation_id = "core-navigation-get-settings-navigation"
        method = "get"
        path = "/ocs/v2.php/core/navigation/settings"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_ocs_get_capabilities(self):
        """
        Test: core-ocs-get-capabilities
        Method: GET
        Path: /ocs/v2.php/cloud/capabilities
        """
        operation_id = "core-ocs-get-capabilities"
        method = "get"
        path = "/ocs/v2.php/cloud/capabilities"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_reference_api_resolve_one(self):
        """
        Test: core-reference_api-resolve-one
        Method: GET
        Path: /ocs/v2.php/references/resolve
        """
        operation_id = "core-reference_api-resolve-one"
        method = "get"
        path = "/ocs/v2.php/references/resolve"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_reference_api_resolve_one_public(self):
        """
        Test: core-reference_api-resolve-one-public
        Method: GET
        Path: /ocs/v2.php/references/resolvePublic
        """
        operation_id = "core-reference_api-resolve-one-public"
        method = "get"
        path = "/ocs/v2.php/references/resolvePublic"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_reference_api_get_providers_info(self):
        """
        Test: core-reference_api-get-providers-info
        Method: GET
        Path: /ocs/v2.php/references/providers
        """
        operation_id = "core-reference_api-get-providers-info"
        method = "get"
        path = "/ocs/v2.php/references/providers"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_task_processing_api_task_types(self):
        """
        Test: core-task_processing_api-task-types
        Method: GET
        Path: /ocs/v2.php/taskprocessing/tasktypes
        """
        operation_id = "core-task_processing_api-task-types"
        method = "get"
        path = "/ocs/v2.php/taskprocessing/tasktypes"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_task_processing_api_list_tasks(self):
        """
        Test: core-task_processing_api-list-tasks
        Method: GET
        Path: /ocs/v2.php/taskprocessing/tasks
        """
        operation_id = "core-task_processing_api-list-tasks"
        method = "get"
        path = "/ocs/v2.php/taskprocessing/tasks"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_text_processing_api_task_types(self):
        """
        Test: core-text_processing_api-task-types
        Method: GET
        Path: /ocs/v2.php/textprocessing/tasktypes
        """
        operation_id = "core-text_processing_api-task-types"
        method = "get"
        path = "/ocs/v2.php/textprocessing/tasktypes"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_text_to_image_api_is_available(self):
        """
        Test: core-text_to_image_api-is-available
        Method: GET
        Path: /ocs/v2.php/text2image/is_available
        """
        operation_id = "core-text_to_image_api-is-available"
        method = "get"
        path = "/ocs/v2.php/text2image/is_available"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_translation_api_languages(self):
        """
        Test: core-translation_api-languages
        Method: GET
        Path: /ocs/v2.php/translation/languages
        """
        operation_id = "core-translation_api-languages"
        method = "get"
        path = "/ocs/v2.php/translation/languages"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_unified_search_get_providers(self):
        """
        Test: core-unified_search-get-providers
        Method: GET
        Path: /ocs/v2.php/search/providers
        """
        operation_id = "core-unified_search-get-providers"
        method = "get"
        path = "/ocs/v2.php/search/providers"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_whats_new_get(self):
        """
        Test: core-whats_new-get
        Method: GET
        Path: /ocs/v2.php/core/whatsnew
        """
        operation_id = "core-whats_new-get"
        method = "get"
        path = "/ocs/v2.php/core/whatsnew"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_csrf_token_index(self):
        """
        Test: core-csrf_token-index
        Method: GET
        Path: /index.php/csrftoken
        """
        operation_id = "core-csrf_token-index"
        method = "get"
        path = "/index.php/csrftoken"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_ocm_discovery(self):
        """
        Test: core-ocm-discovery
        Method: GET
        Path: /index.php/ocm-provider
        """
        operation_id = "core-ocm-discovery"
        method = "get"
        path = "/index.php/ocm-provider"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_preview_get_preview(self):
        """
        Test: core-preview-get-preview
        Method: GET
        Path: /index.php/core/preview.png
        """
        operation_id = "core-preview-get-preview"
        method = "get"
        path = "/index.php/core/preview.png"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_preview_get_preview_by_file_id(self):
        """
        Test: core-preview-get-preview-by-file-id
        Method: GET
        Path: /index.php/core/preview
        """
        operation_id = "core-preview-get-preview-by-file-id"
        method = "get"
        path = "/index.php/core/preview"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_preview_get_mime_icon_url(self):
        """
        Test: core-preview-get-mime-icon-url
        Method: GET
        Path: /index.php/core/mimeicon
        """
        operation_id = "core-preview-get-mime-icon-url"
        method = "get"
        path = "/index.php/core/mimeicon"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_get_status(self):
        """
        Test: core-get-status
        Method: GET
        Path: /status.php
        """
        operation_id = "core-get-status"
        method = "get"
        path = "/status.php"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_dashboard_dashboard_api_get_widget_items(self):
        """
        Test: dashboard-dashboard_api-get-widget-items
        Method: GET
        Path: /ocs/v2.php/apps/dashboard/api/v1/widget-items
        """
        operation_id = "dashboard-dashboard_api-get-widget-items"
        method = "get"
        path = "/ocs/v2.php/apps/dashboard/api/v1/widget-items"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_dashboard_dashboard_api_get_widget_items_v2(self):
        """
        Test: dashboard-dashboard_api-get-widget-items-v2
        Method: GET
        Path: /ocs/v2.php/apps/dashboard/api/v2/widget-items
        """
        operation_id = "dashboard-dashboard_api-get-widget-items-v2"
        method = "get"
        path = "/ocs/v2.php/apps/dashboard/api/v2/widget-items"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_dashboard_dashboard_api_get_widgets(self):
        """
        Test: dashboard-dashboard_api-get-widgets
        Method: GET
        Path: /ocs/v2.php/apps/dashboard/api/v1/widgets
        """
        operation_id = "dashboard-dashboard_api-get-widgets"
        method = "get"
        path = "/ocs/v2.php/apps/dashboard/api/v1/widgets"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_dashboard_dashboard_api_get_layout(self):
        """
        Test: dashboard-dashboard_api-get-layout
        Method: GET
        Path: /ocs/v2.php/apps/dashboard/api/v3/layout
        """
        operation_id = "dashboard-dashboard_api-get-layout"
        method = "get"
        path = "/ocs/v2.php/apps/dashboard/api/v3/layout"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_dashboard_dashboard_api_get_statuses(self):
        """
        Test: dashboard-dashboard_api-get-statuses
        Method: GET
        Path: /ocs/v2.php/apps/dashboard/api/v3/statuses
        """
        operation_id = "dashboard-dashboard_api-get-statuses"
        method = "get"
        path = "/ocs/v2.php/apps/dashboard/api/v3/statuses"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_dav_upcoming_events_get_events(self):
        """
        Test: dav-upcoming_events-get-events
        Method: GET
        Path: /ocs/v2.php/apps/dav/api/v1/events/upcoming
        """
        operation_id = "dav-upcoming_events-get-events"
        method = "get"
        path = "/ocs/v2.php/apps/dav/api/v1/events/upcoming"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_direct_editing_info(self):
        """
        Test: files-direct_editing-info
        Method: GET
        Path: /ocs/v2.php/apps/files/api/v1/directEditing
        """
        operation_id = "files-direct_editing-info"
        method = "get"
        path = "/ocs/v2.php/apps/files/api/v1/directEditing"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_template_list(self):
        """
        Test: files-template-list
        Method: GET
        Path: /ocs/v2.php/apps/files/api/v1/templates
        """
        operation_id = "files-template-list"
        method = "get"
        path = "/ocs/v2.php/apps/files/api/v1/templates"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_api_get_folder_tree(self):
        """
        Test: files-api-get-folder-tree
        Method: GET
        Path: /ocs/v2.php/apps/files/api/v1/folder-tree
        """
        operation_id = "files-api-get-folder-tree"
        method = "get"
        path = "/ocs/v2.php/apps/files/api/v1/folder-tree"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_external_api_get_user_mounts(self):
        """
        Test: files_external-api-get-user-mounts
        Method: GET
        Path: /ocs/v2.php/apps/files_external/api/v1/mounts
        """
        operation_id = "files_external-api-get-user-mounts"
        method = "get"
        path = "/ocs/v2.php/apps/files_external/api/v1/mounts"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_sharing_shareapi_get_shares(self):
        """
        Test: files_sharing-shareapi-get-shares
        Method: GET
        Path: /ocs/v2.php/apps/files_sharing/api/v1/shares
        """
        operation_id = "files_sharing-shareapi-get-shares"
        method = "get"
        path = "/ocs/v2.php/apps/files_sharing/api/v1/shares"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_sharing_shareapi_get_inherited_shares(self):
        """
        Test: files_sharing-shareapi-get-inherited-shares
        Method: GET
        Path: /ocs/v2.php/apps/files_sharing/api/v1/shares/inherited
        """
        operation_id = "files_sharing-shareapi-get-inherited-shares"
        method = "get"
        path = "/ocs/v2.php/apps/files_sharing/api/v1/shares/inherited"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_sharing_shareapi_pending_shares(self):
        """
        Test: files_sharing-shareapi-pending-shares
        Method: GET
        Path: /ocs/v2.php/apps/files_sharing/api/v1/shares/pending
        """
        operation_id = "files_sharing-shareapi-pending-shares"
        method = "get"
        path = "/ocs/v2.php/apps/files_sharing/api/v1/shares/pending"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_sharing_deleted_shareapi_index(self):
        """
        Test: files_sharing-deleted_shareapi-index
        Method: GET
        Path: /ocs/v2.php/apps/files_sharing/api/v1/deletedshares
        """
        operation_id = "files_sharing-deleted_shareapi-index"
        method = "get"
        path = "/ocs/v2.php/apps/files_sharing/api/v1/deletedshares"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_sharing_shareesapi_search(self):
        """
        Test: files_sharing-shareesapi-search
        Method: GET
        Path: /ocs/v2.php/apps/files_sharing/api/v1/sharees
        """
        operation_id = "files_sharing-shareesapi-search"
        method = "get"
        path = "/ocs/v2.php/apps/files_sharing/api/v1/sharees"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_sharing_shareesapi_find_recommended(self):
        """
        Test: files_sharing-shareesapi-find-recommended
        Method: GET
        Path: /ocs/v2.php/apps/files_sharing/api/v1/sharees_recommended
        """
        operation_id = "files_sharing-shareesapi-find-recommended"
        method = "get"
        path = "/ocs/v2.php/apps/files_sharing/api/v1/sharees_recommended"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_sharing_remote_get_shares(self):
        """
        Test: files_sharing-remote-get-shares
        Method: GET
        Path: /ocs/v2.php/apps/files_sharing/api/v1/remote_shares
        """
        operation_id = "files_sharing-remote-get-shares"
        method = "get"
        path = "/ocs/v2.php/apps/files_sharing/api/v1/remote_shares"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_sharing_remote_get_open_shares(self):
        """
        Test: files_sharing-remote-get-open-shares
        Method: GET
        Path: /ocs/v2.php/apps/files_sharing/api/v1/remote_shares/pending
        """
        operation_id = "files_sharing-remote-get-open-shares"
        method = "get"
        path = "/ocs/v2.php/apps/files_sharing/api/v1/remote_shares/pending"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_sharing_shareapi_generate_token(self):
        """
        Test: files_sharing-shareapi-generate-token
        Method: GET
        Path: /ocs/v2.php/apps/files_sharing/api/v1/token
        """
        operation_id = "files_sharing-shareapi-generate-token"
        method = "get"
        path = "/ocs/v2.php/apps/files_sharing/api/v1/token"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_trashbin_preview_get_preview(self):
        """
        Test: files_trashbin-preview-get-preview
        Method: GET
        Path: /index.php/apps/files_trashbin/preview
        """
        operation_id = "files_trashbin-preview-get-preview"
        method = "get"
        path = "/index.php/apps/files_trashbin/preview"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_versions_preview_get_preview(self):
        """
        Test: files_versions-preview-get-preview
        Method: GET
        Path: /index.php/apps/files_versions/preview
        """
        operation_id = "files_versions-preview-get-preview"
        method = "get"
        path = "/index.php/apps/files_versions/preview"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_oauth2_login_redirector_authorize(self):
        """
        Test: oauth2-login_redirector-authorize
        Method: GET
        Path: /index.php/apps/oauth2/authorize
        """
        operation_id = "oauth2-login_redirector-authorize"
        method = "get"
        path = "/index.php/apps/oauth2/authorize"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_groups_get_groups(self):
        """
        Test: provisioning_api-groups-get-groups
        Method: GET
        Path: /ocs/v2.php/cloud/groups
        """
        operation_id = "provisioning_api-groups-get-groups"
        method = "get"
        path = "/ocs/v2.php/cloud/groups"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_groups_get_groups_details(self):
        """
        Test: provisioning_api-groups-get-groups-details
        Method: GET
        Path: /ocs/v2.php/cloud/groups/details
        """
        operation_id = "provisioning_api-groups-get-groups-details"
        method = "get"
        path = "/ocs/v2.php/cloud/groups/details"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_users_get_users(self):
        """
        Test: provisioning_api-users-get-users
        Method: GET
        Path: /ocs/v2.php/cloud/users
        """
        operation_id = "provisioning_api-users-get-users"
        method = "get"
        path = "/ocs/v2.php/cloud/users"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_users_get_users_details(self):
        """
        Test: provisioning_api-users-get-users-details
        Method: GET
        Path: /ocs/v2.php/cloud/users/details
        """
        operation_id = "provisioning_api-users-get-users-details"
        method = "get"
        path = "/ocs/v2.php/cloud/users/details"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_users_get_disabled_users_details(self):
        """
        Test: provisioning_api-users-get-disabled-users-details
        Method: GET
        Path: /ocs/v2.php/cloud/users/disabled
        """
        operation_id = "provisioning_api-users-get-disabled-users-details"
        method = "get"
        path = "/ocs/v2.php/cloud/users/disabled"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_users_get_current_user(self):
        """
        Test: provisioning_api-users-get-current-user
        Method: GET
        Path: /ocs/v2.php/cloud/user
        """
        operation_id = "provisioning_api-users-get-current-user"
        method = "get"
        path = "/ocs/v2.php/cloud/user"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_users_get_editable_fields(self):
        """
        Test: provisioning_api-users-get-editable-fields
        Method: GET
        Path: /ocs/v2.php/cloud/user/fields
        """
        operation_id = "provisioning_api-users-get-editable-fields"
        method = "get"
        path = "/ocs/v2.php/cloud/user/fields"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_users_get_enabled_apps(self):
        """
        Test: provisioning_api-users-get-enabled-apps
        Method: GET
        Path: /ocs/v2.php/cloud/user/apps
        """
        operation_id = "provisioning_api-users-get-enabled-apps"
        method = "get"
        path = "/ocs/v2.php/cloud/user/apps"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_settings_declarative_settings_get_forms(self):
        """
        Test: settings-declarative_settings-get-forms
        Method: GET
        Path: /ocs/v2.php/settings/api/declarative/forms
        """
        operation_id = "settings-declarative_settings-get-forms"
        method = "get"
        path = "/ocs/v2.php/settings/api/declarative/forms"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_theming_user_theme_get_background(self):
        """
        Test: theming-user_theme-get-background
        Method: GET
        Path: /index.php/apps/theming/background
        """
        operation_id = "theming-user_theme-get-background"
        method = "get"
        path = "/index.php/apps/theming/background"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_user_status_predefined_status_find_all(self):
        """
        Test: user_status-predefined_status-find-all
        Method: GET
        Path: /ocs/v2.php/apps/user_status/api/v1/predefined_statuses
        """
        operation_id = "user_status-predefined_status-find-all"
        method = "get"
        path = "/ocs/v2.php/apps/user_status/api/v1/predefined_statuses"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_user_status_statuses_find_all(self):
        """
        Test: user_status-statuses-find-all
        Method: GET
        Path: /ocs/v2.php/apps/user_status/api/v1/statuses
        """
        operation_id = "user_status-statuses-find-all"
        method = "get"
        path = "/ocs/v2.php/apps/user_status/api/v1/statuses"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_user_status_user_status_get_status(self):
        """
        Test: user_status-user_status-get-status
        Method: GET
        Path: /ocs/v2.php/apps/user_status/api/v1/user_status
        """
        operation_id = "user_status-user_status-get-status"
        method = "get"
        path = "/ocs/v2.php/apps/user_status/api/v1/user_status"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_weather_status_weather_status_get_location(self):
        """
        Test: weather_status-weather_status-get-location
        Method: GET
        Path: /ocs/v2.php/apps/weather_status/api/v1/location
        """
        operation_id = "weather_status-weather_status-get-location"
        method = "get"
        path = "/ocs/v2.php/apps/weather_status/api/v1/location"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_weather_status_weather_status_get_forecast(self):
        """
        Test: weather_status-weather_status-get-forecast
        Method: GET
        Path: /ocs/v2.php/apps/weather_status/api/v1/forecast
        """
        operation_id = "weather_status-weather_status-get-forecast"
        method = "get"
        path = "/ocs/v2.php/apps/weather_status/api/v1/forecast"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_weather_status_weather_status_get_favorites(self):
        """
        Test: weather_status-weather_status-get-favorites
        Method: GET
        Path: /ocs/v2.php/apps/weather_status/api/v1/favorites
        """
        operation_id = "weather_status-weather_status-get-favorites"
        method = "get"
        path = "/ocs/v2.php/apps/weather_status/api/v1/favorites"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_webhook_listeners_webhooks_index(self):
        """
        Test: webhook_listeners-webhooks-index
        Method: GET
        Path: /ocs/v2.php/apps/webhook_listeners/api/v1/webhooks
        """
        operation_id = "webhook_listeners-webhooks-index"
        method = "get"
        path = "/ocs/v2.php/apps/webhook_listeners/api/v1/webhooks"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )


class TestGetParameterizedPaths:
    """GET endpoint tests"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test helper"""
        self.helper = APITestHelper(TEST_CONFIG)
        self.param_helper = ParameterHelper()
        self.response_helper = ResponseHelper()

    def test_core_collaboration_resources_list_collection(self):
        """
        Test: core-collaboration_resources-list-collection
        Method: GET
        Path: /ocs/v2.php/collaboration/resources/collections/{collectionId}
        """
        operation_id = "core-collaboration_resources-list-collection"
        method = "get"
        path = "/ocs/v2.php/collaboration/resources/collections/{collectionId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "collectionId": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_collaboration_resources_search_collections(self):
        """
        Test: core-collaboration_resources-search-collections
        Method: GET
        Path: /ocs/v2.php/collaboration/resources/collections/search/{filter}
        """
        operation_id = "core-collaboration_resources-search-collections"
        method = "get"
        path = "/ocs/v2.php/collaboration/resources/collections/search/{filter}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "filter": "example_filter",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_collaboration_resources_get_collections_by_resource(self):
        """
        Test: core-collaboration_resources-get-collections-by-resource
        Method: GET
        Path: /ocs/v2.php/collaboration/resources/{resourceType}/{resourceId}
        """
        operation_id = "core-collaboration_resources-get-collections-by-resource"
        method = "get"
        path = "/ocs/v2.php/collaboration/resources/{resourceType}/{resourceId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "resourceType": "example_resourceType",
                "resourceId": "example_resourceId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_hover_card_get_user(self):
        """
        Test: core-hover_card-get-user
        Method: GET
        Path: /ocs/v2.php/hovercard/v1/{userId}
        """
        operation_id = "core-hover_card-get-user"
        method = "get"
        path = "/ocs/v2.php/hovercard/v1/{userId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "userId": "example_userId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_profile_api_get_profile_fields(self):
        """
        Test: core-profile_api-get-profile-fields
        Method: GET
        Path: /ocs/v2.php/profile/{targetUserId}
        """
        operation_id = "core-profile_api-get-profile-fields"
        method = "get"
        path = "/ocs/v2.php/profile/{targetUserId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "targetUserId": "example_targetUserId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_task_processing_api_get_task(self):
        """
        Test: core-task_processing_api-get-task
        Method: GET
        Path: /ocs/v2.php/taskprocessing/task/{id}
        """
        operation_id = "core-task_processing_api-get-task"
        method = "get"
        path = "/ocs/v2.php/taskprocessing/task/{id}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_task_processing_api_list_tasks_by_app(self):
        """
        Test: core-task_processing_api-list-tasks-by-app
        Method: GET
        Path: /ocs/v2.php/taskprocessing/tasks/app/{appId}
        """
        operation_id = "core-task_processing_api-list-tasks-by-app"
        method = "get"
        path = "/ocs/v2.php/taskprocessing/tasks/app/{appId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "appId": "example_appId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_task_processing_api_get_file_contents(self):
        """
        Test: core-task_processing_api-get-file-contents
        Method: GET
        Path: /ocs/v2.php/taskprocessing/tasks/{taskId}/file/{fileId}
        """
        operation_id = "core-task_processing_api-get-file-contents"
        method = "get"
        path = "/ocs/v2.php/taskprocessing/tasks/{taskId}/file/{fileId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "taskId": 1,
                "fileId": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_teams_api_resolve_one(self):
        """
        Test: core-teams_api-resolve-one
        Method: GET
        Path: /ocs/v2.php/teams/{teamId}/resources
        """
        operation_id = "core-teams_api-resolve-one"
        method = "get"
        path = "/ocs/v2.php/teams/{teamId}/resources"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "teamId": "example_teamId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_teams_api_list_teams(self):
        """
        Test: core-teams_api-list-teams
        Method: GET
        Path: /ocs/v2.php/teams/resources/{providerId}/{resourceId}
        """
        operation_id = "core-teams_api-list-teams"
        method = "get"
        path = "/ocs/v2.php/teams/resources/{providerId}/{resourceId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "providerId": "example_providerId",
                "resourceId": "example_resourceId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_text_processing_api_get_task(self):
        """
        Test: core-text_processing_api-get-task
        Method: GET
        Path: /ocs/v2.php/textprocessing/task/{id}
        """
        operation_id = "core-text_processing_api-get-task"
        method = "get"
        path = "/ocs/v2.php/textprocessing/task/{id}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_text_processing_api_list_tasks_by_app(self):
        """
        Test: core-text_processing_api-list-tasks-by-app
        Method: GET
        Path: /ocs/v2.php/textprocessing/tasks/app/{appId}
        """
        operation_id = "core-text_processing_api-list-tasks-by-app"
        method = "get"
        path = "/ocs/v2.php/textprocessing/tasks/app/{appId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "appId": "example_appId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_text_to_image_api_get_task(self):
        """
        Test: core-text_to_image_api-get-task
        Method: GET
        Path: /ocs/v2.php/text2image/task/{id}
        """
        operation_id = "core-text_to_image_api-get-task"
        method = "get"
        path = "/ocs/v2.php/text2image/task/{id}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_text_to_image_api_get_image(self):
        """
        Test: core-text_to_image_api-get-image
        Method: GET
        Path: /ocs/v2.php/text2image/task/{id}/image/{index}
        """
        operation_id = "core-text_to_image_api-get-image"
        method = "get"
        path = "/ocs/v2.php/text2image/task/{id}/image/{index}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": 1,
                "index": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_text_to_image_api_list_tasks_by_app(self):
        """
        Test: core-text_to_image_api-list-tasks-by-app
        Method: GET
        Path: /ocs/v2.php/text2image/tasks/app/{appId}
        """
        operation_id = "core-text_to_image_api-list-tasks-by-app"
        method = "get"
        path = "/ocs/v2.php/text2image/tasks/app/{appId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "appId": "example_appId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_unified_search_search(self):
        """
        Test: core-unified_search-search
        Method: GET
        Path: /ocs/v2.php/search/providers/{providerId}/search
        """
        operation_id = "core-unified_search-search"
        method = "get"
        path = "/ocs/v2.php/search/providers/{providerId}/search"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "providerId": "example_providerId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_avatar_get_avatar_dark(self):
        """
        Test: core-avatar-get-avatar-dark
        Method: GET
        Path: /index.php/avatar/{userId}/{size}/dark
        """
        operation_id = "core-avatar-get-avatar-dark"
        method = "get"
        path = "/index.php/avatar/{userId}/{size}/dark"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "userId": "example_userId",
                "size": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_avatar_get_avatar(self):
        """
        Test: core-avatar-get-avatar
        Method: GET
        Path: /index.php/avatar/{userId}/{size}
        """
        operation_id = "core-avatar-get-avatar"
        method = "get"
        path = "/index.php/avatar/{userId}/{size}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "userId": "example_userId",
                "size": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_guest_avatar_get_avatar(self):
        """
        Test: core-guest_avatar-get-avatar
        Method: GET
        Path: /index.php/avatar/guest/{guestName}/{size}
        """
        operation_id = "core-guest_avatar-get-avatar"
        method = "get"
        path = "/index.php/avatar/guest/{guestName}/{size}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "guestName": "example_guestName",
                "size": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_guest_avatar_get_avatar_dark(self):
        """
        Test: core-guest_avatar-get-avatar-dark
        Method: GET
        Path: /index.php/avatar/guest/{guestName}/{size}/dark
        """
        operation_id = "core-guest_avatar-get-avatar-dark"
        method = "get"
        path = "/index.php/avatar/guest/{guestName}/{size}/dark"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "guestName": "example_guestName",
                "size": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_reference_preview(self):
        """
        Test: core-reference-preview
        Method: GET
        Path: /index.php/core/references/preview/{referenceId}
        """
        operation_id = "core-reference-preview"
        method = "get"
        path = "/index.php/core/references/preview/{referenceId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "referenceId": "example_referenceId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_dav_out_of_office_get_current_out_of_office_data(self):
        """
        Test: dav-out_of_office-get-current-out-of-office-data
        Method: GET
        Path: /ocs/v2.php/apps/dav/api/v1/outOfOffice/{userId}/now
        """
        operation_id = "dav-out_of_office-get-current-out-of-office-data"
        method = "get"
        path = "/ocs/v2.php/apps/dav/api/v1/outOfOffice/{userId}/now"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "userId": "example_userId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_dav_out_of_office_get_out_of_office(self):
        """
        Test: dav-out_of_office-get-out-of-office
        Method: GET
        Path: /ocs/v2.php/apps/dav/api/v1/outOfOffice/{userId}
        """
        operation_id = "dav-out_of_office-get-out-of-office"
        method = "get"
        path = "/ocs/v2.php/apps/dav/api/v1/outOfOffice/{userId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "userId": "example_userId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_api_get_thumbnail(self):
        """
        Test: files-api-get-thumbnail
        Method: GET
        Path: /index.php/apps/files/api/v1/thumbnail/{x}/{y}/{file}
        """
        operation_id = "files-api-get-thumbnail"
        method = "get"
        path = "/index.php/apps/files/api/v1/thumbnail/{x}/{y}/{file}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "x": 1,
                "y": 1,
                "file": "example_file",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_direct_editing_templates(self):
        """
        Test: files-direct_editing-templates
        Method: GET
        Path: /ocs/v2.php/apps/files/api/v1/directEditing/templates/{editorId}/{creatorId}
        """
        operation_id = "files-direct_editing-templates"
        method = "get"
        path = "/ocs/v2.php/apps/files/api/v1/directEditing/templates/{editorId}/{creatorId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "editorId": "example_editorId",
                "creatorId": "example_creatorId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_template_list_template_fields(self):
        """
        Test: files-template-list-template-fields
        Method: GET
        Path: /ocs/v2.php/apps/files/api/v1/templates/fields/{fileId}
        """
        operation_id = "files-template-list-template-fields"
        method = "get"
        path = "/ocs/v2.php/apps/files/api/v1/templates/fields/{fileId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "fileId": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_reminders_api_get(self):
        """
        Test: files_reminders-api-get
        Method: GET
        Path: /ocs/v2.php/apps/files_reminders/api/v{version}/{fileId}
        """
        operation_id = "files_reminders-api-get"
        method = "get"
        path = "/ocs/v2.php/apps/files_reminders/api/v{version}/{fileId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "version": "example_version",
                "fileId": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_sharing_public_preview_direct_link(self):
        """
        Test: files_sharing-public_preview-direct-link
        Method: GET
        Path: /index.php/s/{token}/preview
        """
        operation_id = "files_sharing-public_preview-direct-link"
        method = "get"
        path = "/index.php/s/{token}/preview"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "token": "example_token",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_sharing_public_preview_get_preview(self):
        """
        Test: files_sharing-public_preview-get-preview
        Method: GET
        Path: /index.php/apps/files_sharing/publicpreview/{token}
        """
        operation_id = "files_sharing-public_preview-get-preview"
        method = "get"
        path = "/index.php/apps/files_sharing/publicpreview/{token}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "token": "example_token",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_sharing_shareapi_get_share(self):
        """
        Test: files_sharing-shareapi-get-share
        Method: GET
        Path: /ocs/v2.php/apps/files_sharing/api/v1/shares/{id}
        """
        operation_id = "files_sharing-shareapi-get-share"
        method = "get"
        path = "/ocs/v2.php/apps/files_sharing/api/v1/shares/{id}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": "example_id",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_sharing_remote_get_share(self):
        """
        Test: files_sharing-remote-get-share
        Method: GET
        Path: /ocs/v2.php/apps/files_sharing/api/v1/remote_shares/{id}
        """
        operation_id = "files_sharing-remote-get-share"
        method = "get"
        path = "/ocs/v2.php/apps/files_sharing/api/v1/remote_shares/{id}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_groups_get_group_users(self):
        """
        Test: provisioning_api-groups-get-group-users
        Method: GET
        Path: /ocs/v2.php/cloud/groups/{groupId}/users
        """
        operation_id = "provisioning_api-groups-get-group-users"
        method = "get"
        path = "/ocs/v2.php/cloud/groups/{groupId}/users"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "groupId": "example_groupId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_groups_get_group_users_details(self):
        """
        Test: provisioning_api-groups-get-group-users-details
        Method: GET
        Path: /ocs/v2.php/cloud/groups/{groupId}/users/details
        """
        operation_id = "provisioning_api-groups-get-group-users-details"
        method = "get"
        path = "/ocs/v2.php/cloud/groups/{groupId}/users/details"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "groupId": "example_groupId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_groups_get_group(self):
        """
        Test: provisioning_api-groups-get-group
        Method: GET
        Path: /ocs/v2.php/cloud/groups/{groupId}
        """
        operation_id = "provisioning_api-groups-get-group"
        method = "get"
        path = "/ocs/v2.php/cloud/groups/{groupId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "groupId": "example_groupId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_users_get_user(self):
        """
        Test: provisioning_api-users-get-user
        Method: GET
        Path: /ocs/v2.php/cloud/users/{userId}
        """
        operation_id = "provisioning_api-users-get-user"
        method = "get"
        path = "/ocs/v2.php/cloud/users/{userId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "userId": "example_userId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_users_get_editable_fields_for_user(self):
        """
        Test: provisioning_api-users-get-editable-fields-for-user
        Method: GET
        Path: /ocs/v2.php/cloud/user/fields/{userId}
        """
        operation_id = "provisioning_api-users-get-editable-fields-for-user"
        method = "get"
        path = "/ocs/v2.php/cloud/user/fields/{userId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "userId": "example_userId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_users_get_users_groups(self):
        """
        Test: provisioning_api-users-get-users-groups
        Method: GET
        Path: /ocs/v2.php/cloud/users/{userId}/groups
        """
        operation_id = "provisioning_api-users-get-users-groups"
        method = "get"
        path = "/ocs/v2.php/cloud/users/{userId}/groups"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "userId": "example_userId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_users_get_users_groups_details(self):
        """
        Test: provisioning_api-users-get-users-groups-details
        Method: GET
        Path: /ocs/v2.php/cloud/users/{userId}/groups/details
        """
        operation_id = "provisioning_api-users-get-users-groups-details"
        method = "get"
        path = "/ocs/v2.php/cloud/users/{userId}/groups/details"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "userId": "example_userId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_users_get_user_sub_admin_groups_details(self):
        """
        Test: provisioning_api-users-get-user-sub-admin-groups-details
        Method: GET
        Path: /ocs/v2.php/cloud/users/{userId}/subadmins/details
        """
        operation_id = "provisioning_api-users-get-user-sub-admin-groups-details"
        method = "get"
        path = "/ocs/v2.php/cloud/users/{userId}/subadmins/details"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "userId": "example_userId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_theming_theming_get_theme_stylesheet(self):
        """
        Test: theming-theming-get-theme-stylesheet
        Method: GET
        Path: /index.php/apps/theming/theme/{themeId}.css
        """
        operation_id = "theming-theming-get-theme-stylesheet"
        method = "get"
        path = "/index.php/apps/theming/theme/{themeId}.css"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "themeId": "example_themeId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_theming_theming_get_image(self):
        """
        Test: theming-theming-get-image
        Method: GET
        Path: /index.php/apps/theming/image/{key}
        """
        operation_id = "theming-theming-get-image"
        method = "get"
        path = "/index.php/apps/theming/image/{key}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "key": "example_key",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_theming_theming_get_manifest(self):
        """
        Test: theming-theming-get-manifest
        Method: GET
        Path: /index.php/apps/theming/manifest/{app}
        """
        operation_id = "theming-theming-get-manifest"
        method = "get"
        path = "/index.php/apps/theming/manifest/{app}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "app": "core",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_theming_icon_get_favicon(self):
        """
        Test: theming-icon-get-favicon
        Method: GET
        Path: /index.php/apps/theming/favicon/{app}
        """
        operation_id = "theming-icon-get-favicon"
        method = "get"
        path = "/index.php/apps/theming/favicon/{app}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "app": "core",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_theming_icon_get_touch_icon(self):
        """
        Test: theming-icon-get-touch-icon
        Method: GET
        Path: /index.php/apps/theming/icon/{app}
        """
        operation_id = "theming-icon-get-touch-icon"
        method = "get"
        path = "/index.php/apps/theming/icon/{app}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "app": "core",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_theming_icon_get_themed_icon(self):
        """
        Test: theming-icon-get-themed-icon
        Method: GET
        Path: /index.php/apps/theming/img/{app}/{image}
        """
        operation_id = "theming-icon-get-themed-icon"
        method = "get"
        path = "/index.php/apps/theming/img/{app}/{image}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "app": "example_app",
                "image": "example_image",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_updatenotification_api_get_app_list(self):
        """
        Test: updatenotification-api-get-app-list
        Method: GET
        Path: /ocs/v2.php/apps/updatenotification/api/{apiVersion}/applist/{newVersion}
        """
        operation_id = "updatenotification-api-get-app-list"
        method = "get"
        path = (
            "/ocs/v2.php/apps/updatenotification/api/{apiVersion}/applist/{newVersion}"
        )

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "apiVersion": "v1",
                "newVersion": "example_newVersion",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_updatenotification_api_get_app_changelog_entry(self):
        """
        Test: updatenotification-api-get-app-changelog-entry
        Method: GET
        Path: /ocs/v2.php/apps/updatenotification/api/{apiVersion}/changelog/{appId}
        """
        operation_id = "updatenotification-api-get-app-changelog-entry"
        method = "get"
        path = "/ocs/v2.php/apps/updatenotification/api/{apiVersion}/changelog/{appId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "apiVersion": "v1",
                "appId": "example_appId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_user_ldap_configapi_show(self):
        """
        Test: user_ldap-configapi-show
        Method: GET
        Path: /ocs/v2.php/apps/user_ldap/api/v1/config/{configID}
        """
        operation_id = "user_ldap-configapi-show"
        method = "get"
        path = "/ocs/v2.php/apps/user_ldap/api/v1/config/{configID}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "configID": "example_configID",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_user_status_statuses_find(self):
        """
        Test: user_status-statuses-find
        Method: GET
        Path: /ocs/v2.php/apps/user_status/api/v1/statuses/{userId}
        """
        operation_id = "user_status-statuses-find"
        method = "get"
        path = "/ocs/v2.php/apps/user_status/api/v1/statuses/{userId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "userId": "example_userId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_webhook_listeners_webhooks_show(self):
        """
        Test: webhook_listeners-webhooks-show
        Method: GET
        Path: /ocs/v2.php/apps/webhook_listeners/api/v1/webhooks/{id}
        """
        operation_id = "webhook_listeners-webhooks-show"
        method = "get"
        path = "/ocs/v2.php/apps/webhook_listeners/api/v1/webhooks/{id}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )


class TestPost:
    """POST endpoint tests"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test helper"""
        self.helper = APITestHelper(TEST_CONFIG)
        self.param_helper = ParameterHelper()
        self.response_helper = ResponseHelper()

    # def test_core_app_password_rotate_app_password(self):
    #     """
    #     Test: core-app_password-rotate-app-password
    #     Method: POST
    #     Path: /ocs/v2.php/core/apppassword/rotate
    #     """
    #     operation_id = "core-app_password-rotate-app-password"
    #     method = "post"
    #     path = "/ocs/v2.php/core/apppassword/rotate"

    #     # Load test cases
    #     test_cases = TEST_DATA.get(
    #         operation_id,
    #         [
    #             TestCase(
    #                 description="Default test case",
    #                 assertions=ResponseAssertion(status_code=200),
    #             )
    #         ],
    #     )

    #     for i, test_case in enumerate(test_cases):
    #         # Skip if needed
    #         if test_case.skip:
    #             pytest.skip(test_case.skip_reason)

    #         # Extract parameters
    #         path_params, query_params, headers, body = (
    #             self.param_helper.extract_parameters(test_case)
    #         )

    #         # Execute request
    #         try:
    #             response = self.helper.execute_request(
    #                 method=method,
    #                 path=path,
    #                 path_params=path_params,
    #                 query_params=query_params,
    #                 headers=headers,
    #                 body=body,
    #             )
    #         except Exception as e:
    #             pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

    #         # Assertions
    #         test_desc = f"Test {i}: {test_case.description}"

    #         if test_case.assertions.status_code:
    #             self.response_helper.assert_status(
    #                 response, test_case.assertions.status_code, test_desc
    #             )

    #         if test_case.assertions.json_contains:
    #             self.response_helper.assert_json_contains(
    #                 response, test_case.assertions.json_contains, test_desc
    #             )

    #         if test_case.assertions.headers_contain:
    #             self.response_helper.assert_headers(
    #                 response, test_case.assertions.headers_contain, test_desc
    #             )

    def test_core_collaboration_resources_add_resource(self):
        """
        Test: core-collaboration_resources-add-resource
        Method: POST
        Path: /ocs/v2.php/collaboration/resources/collections/{collectionId}
        """
        operation_id = "core-collaboration_resources-add-resource"
        method = "post"
        path = "/ocs/v2.php/collaboration/resources/collections/{collectionId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "collectionId": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_collaboration_resources_create_collection_on_resource(self):
        """
        Test: core-collaboration_resources-create-collection-on-resource
        Method: POST
        Path: /ocs/v2.php/collaboration/resources/{baseResourceType}/{baseResourceId}
        """
        operation_id = "core-collaboration_resources-create-collection-on-resource"
        method = "post"
        path = "/ocs/v2.php/collaboration/resources/{baseResourceType}/{baseResourceId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "baseResourceType": "example_baseResourceType",
                "baseResourceId": "example_baseResourceId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_reference_api_extract(self):
        """
        Test: core-reference_api-extract
        Method: POST
        Path: /ocs/v2.php/references/extract
        """
        operation_id = "core-reference_api-extract"
        method = "post"
        path = "/ocs/v2.php/references/extract"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_reference_api_extract_public(self):
        """
        Test: core-reference_api-extract-public
        Method: POST
        Path: /ocs/v2.php/references/extractPublic
        """
        operation_id = "core-reference_api-extract-public"
        method = "post"
        path = "/ocs/v2.php/references/extractPublic"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_reference_api_resolve(self):
        """
        Test: core-reference_api-resolve
        Method: POST
        Path: /ocs/v2.php/references/resolve
        """
        operation_id = "core-reference_api-resolve"
        method = "post"
        path = "/ocs/v2.php/references/resolve"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_reference_api_resolve_public(self):
        """
        Test: core-reference_api-resolve-public
        Method: POST
        Path: /ocs/v2.php/references/resolvePublic
        """
        operation_id = "core-reference_api-resolve-public"
        method = "post"
        path = "/ocs/v2.php/references/resolvePublic"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_task_processing_api_schedule(self):
        """
        Test: core-task_processing_api-schedule
        Method: POST
        Path: /ocs/v2.php/taskprocessing/schedule
        """
        operation_id = "core-task_processing_api-schedule"
        method = "post"
        path = "/ocs/v2.php/taskprocessing/schedule"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_task_processing_api_cancel_task(self):
        """
        Test: core-task_processing_api-cancel-task
        Method: POST
        Path: /ocs/v2.php/taskprocessing/tasks/{taskId}/cancel
        """
        operation_id = "core-task_processing_api-cancel-task"
        method = "post"
        path = "/ocs/v2.php/taskprocessing/tasks/{taskId}/cancel"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "taskId": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_text_processing_api_schedule(self):
        """
        Test: core-text_processing_api-schedule
        Method: POST
        Path: /ocs/v2.php/textprocessing/schedule
        """
        operation_id = "core-text_processing_api-schedule"
        method = "post"
        path = "/ocs/v2.php/textprocessing/schedule"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_text_to_image_api_schedule(self):
        """
        Test: core-text_to_image_api-schedule
        Method: POST
        Path: /ocs/v2.php/text2image/schedule
        """
        operation_id = "core-text_to_image_api-schedule"
        method = "post"
        path = "/ocs/v2.php/text2image/schedule"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_translation_api_translate(self):
        """
        Test: core-translation_api-translate
        Method: POST
        Path: /ocs/v2.php/translation/translate
        """
        operation_id = "core-translation_api-translate"
        method = "post"
        path = "/ocs/v2.php/translation/translate"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_whats_new_dismiss(self):
        """
        Test: core-whats_new-dismiss
        Method: POST
        Path: /ocs/v2.php/core/whatsnew
        """
        operation_id = "core-whats_new-dismiss"
        method = "post"
        path = "/ocs/v2.php/core/whatsnew"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_client_flow_login_v2_poll(self):
        """
        Test: core-client_flow_login_v2-poll
        Method: POST
        Path: /index.php/login/v2/poll
        """
        operation_id = "core-client_flow_login_v2-poll"
        method = "post"
        path = "/index.php/login/v2/poll"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_client_flow_login_v2_init(self):
        """
        Test: core-client_flow_login_v2-init
        Method: POST
        Path: /index.php/login/v2
        """
        operation_id = "core-client_flow_login_v2-init"
        method = "post"
        path = "/index.php/login/v2"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_login_confirm_password(self):
        """
        Test: core-login-confirm-password
        Method: POST
        Path: /index.php/login/confirm
        """
        operation_id = "core-login-confirm-password"
        method = "post"
        path = "/index.php/login/confirm"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_wipe_check_wipe(self):
        """
        Test: core-wipe-check-wipe
        Method: POST
        Path: /index.php/core/wipe/check
        """
        operation_id = "core-wipe-check-wipe"
        method = "post"
        path = "/index.php/core/wipe/check"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_wipe_wipe_done(self):
        """
        Test: core-wipe-wipe-done
        Method: POST
        Path: /index.php/core/wipe/success
        """
        operation_id = "core-wipe-wipe-done"
        method = "post"
        path = "/index.php/core/wipe/success"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_cloud_federation_api_request_handler_add_share(self):
        """
        Test: cloud_federation_api-request_handler-add-share
        Method: POST
        Path: /index.php/ocm/shares
        """
        operation_id = "cloud_federation_api-request_handler-add-share"
        method = "post"
        path = "/index.php/ocm/shares"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_cloud_federation_api_request_handler_receive_notification(self):
        """
        Test: cloud_federation_api-request_handler-receive-notification
        Method: POST
        Path: /index.php/ocm/notifications
        """
        operation_id = "cloud_federation_api-request_handler-receive-notification"
        method = "post"
        path = "/index.php/ocm/notifications"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_cloud_federation_api_request_handler_invite_accepted(self):
        """
        Test: cloud_federation_api-request_handler-invite-accepted
        Method: POST
        Path: /index.php/ocm/invite-accepted
        """
        operation_id = "cloud_federation_api-request_handler-invite-accepted"
        method = "post"
        path = "/index.php/ocm/invite-accepted"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_dashboard_dashboard_api_update_layout(self):
        """
        Test: dashboard-dashboard_api-update-layout
        Method: POST
        Path: /ocs/v2.php/apps/dashboard/api/v3/layout
        """
        operation_id = "dashboard-dashboard_api-update-layout"
        method = "post"
        path = "/ocs/v2.php/apps/dashboard/api/v3/layout"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_dashboard_dashboard_api_update_statuses(self):
        """
        Test: dashboard-dashboard_api-update-statuses
        Method: POST
        Path: /ocs/v2.php/apps/dashboard/api/v3/statuses
        """
        operation_id = "dashboard-dashboard_api-update-statuses"
        method = "post"
        path = "/ocs/v2.php/apps/dashboard/api/v3/statuses"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_dav_direct_get_url(self):
        """
        Test: dav-direct-get-url
        Method: POST
        Path: /ocs/v2.php/apps/dav/api/v1/direct
        """
        operation_id = "dav-direct-get-url"
        method = "post"
        path = "/ocs/v2.php/apps/dav/api/v1/direct"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_dav_out_of_office_set_out_of_office(self):
        """
        Test: dav-out_of_office-set-out-of-office
        Method: POST
        Path: /ocs/v2.php/apps/dav/api/v1/outOfOffice/{userId}
        """
        operation_id = "dav-out_of_office-set-out-of-office"
        method = "post"
        path = "/ocs/v2.php/apps/dav/api/v1/outOfOffice/{userId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "userId": "example_userId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_federatedfilesharing_mount_public_link_create_federated_share(self):
        """
        Test: federatedfilesharing-mount_public_link-create-federated-share
        Method: POST
        Path: /index.php/apps/federatedfilesharing/createFederatedShare
        """
        operation_id = "federatedfilesharing-mount_public_link-create-federated-share"
        method = "post"
        path = "/index.php/apps/federatedfilesharing/createFederatedShare"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_federatedfilesharing_request_handler_create_share(self):
        """
        Test: federatedfilesharing-request_handler-create-share
        Method: POST
        Path: /ocs/v2.php/cloud/shares
        """
        operation_id = "federatedfilesharing-request_handler-create-share"
        method = "post"
        path = "/ocs/v2.php/cloud/shares"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_federatedfilesharing_request_handler_re_share(self):
        """
        Test: federatedfilesharing-request_handler-re-share
        Method: POST
        Path: /ocs/v2.php/cloud/shares/{id}/reshare
        """
        operation_id = "federatedfilesharing-request_handler-re-share"
        method = "post"
        path = "/ocs/v2.php/cloud/shares/{id}/reshare"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_federatedfilesharing_request_handler_update_permissions(self):
        """
        Test: federatedfilesharing-request_handler-update-permissions
        Method: POST
        Path: /ocs/v2.php/cloud/shares/{id}/permissions
        """
        operation_id = "federatedfilesharing-request_handler-update-permissions"
        method = "post"
        path = "/ocs/v2.php/cloud/shares/{id}/permissions"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_federatedfilesharing_request_handler_accept_share(self):
        """
        Test: federatedfilesharing-request_handler-accept-share
        Method: POST
        Path: /ocs/v2.php/cloud/shares/{id}/accept
        """
        operation_id = "federatedfilesharing-request_handler-accept-share"
        method = "post"
        path = "/ocs/v2.php/cloud/shares/{id}/accept"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_federatedfilesharing_request_handler_decline_share(self):
        """
        Test: federatedfilesharing-request_handler-decline-share
        Method: POST
        Path: /ocs/v2.php/cloud/shares/{id}/decline
        """
        operation_id = "federatedfilesharing-request_handler-decline-share"
        method = "post"
        path = "/ocs/v2.php/cloud/shares/{id}/decline"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_federatedfilesharing_request_handler_unshare(self):
        """
        Test: federatedfilesharing-request_handler-unshare
        Method: POST
        Path: /ocs/v2.php/cloud/shares/{id}/unshare
        """
        operation_id = "federatedfilesharing-request_handler-unshare"
        method = "post"
        path = "/ocs/v2.php/cloud/shares/{id}/unshare"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_federatedfilesharing_request_handler_revoke(self):
        """
        Test: federatedfilesharing-request_handler-revoke
        Method: POST
        Path: /ocs/v2.php/cloud/shares/{id}/revoke
        """
        operation_id = "federatedfilesharing-request_handler-revoke"
        method = "post"
        path = "/ocs/v2.php/cloud/shares/{id}/revoke"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_federatedfilesharing_request_handler_move(self):
        """
        Test: federatedfilesharing-request_handler-move
        Method: POST
        Path: /ocs/v2.php/cloud/shares/{id}/move
        """
        operation_id = "federatedfilesharing-request_handler-move"
        method = "post"
        path = "/ocs/v2.php/cloud/shares/{id}/move"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_direct_editing_open(self):
        """
        Test: files-direct_editing-open
        Method: POST
        Path: /ocs/v2.php/apps/files/api/v1/directEditing/open
        """
        operation_id = "files-direct_editing-open"
        method = "post"
        path = "/ocs/v2.php/apps/files/api/v1/directEditing/open"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_direct_editing_create(self):
        """
        Test: files-direct_editing-create
        Method: POST
        Path: /ocs/v2.php/apps/files/api/v1/directEditing/create
        """
        operation_id = "files-direct_editing-create"
        method = "post"
        path = "/ocs/v2.php/apps/files/api/v1/directEditing/create"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_template_create(self):
        """
        Test: files-template-create
        Method: POST
        Path: /ocs/v2.php/apps/files/api/v1/templates/create
        """
        operation_id = "files-template-create"
        method = "post"
        path = "/ocs/v2.php/apps/files/api/v1/templates/create"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_template_path(self):
        """
        Test: files-template-path
        Method: POST
        Path: /ocs/v2.php/apps/files/api/v1/templates/path
        """
        operation_id = "files-template-path"
        method = "post"
        path = "/ocs/v2.php/apps/files/api/v1/templates/path"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_transfer_ownership_transfer(self):
        """
        Test: files-transfer_ownership-transfer
        Method: POST
        Path: /ocs/v2.php/apps/files/api/v1/transferownership
        """
        operation_id = "files-transfer_ownership-transfer"
        method = "post"
        path = "/ocs/v2.php/apps/files/api/v1/transferownership"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_transfer_ownership_accept(self):
        """
        Test: files-transfer_ownership-accept
        Method: POST
        Path: /ocs/v2.php/apps/files/api/v1/transferownership/{id}
        """
        operation_id = "files-transfer_ownership-accept"
        method = "post"
        path = "/ocs/v2.php/apps/files/api/v1/transferownership/{id}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_open_local_editor_create(self):
        """
        Test: files-open_local_editor-create
        Method: POST
        Path: /ocs/v2.php/apps/files/api/v1/openlocaleditor
        """
        operation_id = "files-open_local_editor-create"
        method = "post"
        path = "/ocs/v2.php/apps/files/api/v1/openlocaleditor"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_open_local_editor_validate(self):
        """
        Test: files-open_local_editor-validate
        Method: POST
        Path: /ocs/v2.php/apps/files/api/v1/openlocaleditor/{token}
        """
        operation_id = "files-open_local_editor-validate"
        method = "post"
        path = "/ocs/v2.php/apps/files/api/v1/openlocaleditor/{token}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "token": "example_token",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_conversion_api_convert(self):
        """
        Test: files-conversion_api-convert
        Method: POST
        Path: /ocs/v2.php/apps/files/api/v1/convert
        """
        operation_id = "files-conversion_api-convert"
        method = "post"
        path = "/ocs/v2.php/apps/files/api/v1/convert"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_sharing_share_info_info(self):
        """
        Test: files_sharing-share_info-info
        Method: POST
        Path: /index.php/apps/files_sharing/shareinfo
        """
        operation_id = "files_sharing-share_info-info"
        method = "post"
        path = "/index.php/apps/files_sharing/shareinfo"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_sharing_shareapi_create_share(self):
        """
        Test: files_sharing-shareapi-create-share
        Method: POST
        Path: /ocs/v2.php/apps/files_sharing/api/v1/shares
        """
        operation_id = "files_sharing-shareapi-create-share"
        method = "post"
        path = "/ocs/v2.php/apps/files_sharing/api/v1/shares"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_sharing_shareapi_send_share_email(self):
        """
        Test: files_sharing-shareapi-send-share-email
        Method: POST
        Path: /ocs/v2.php/apps/files_sharing/api/v1/shares/{id}/send-email
        """
        operation_id = "files_sharing-shareapi-send-share-email"
        method = "post"
        path = "/ocs/v2.php/apps/files_sharing/api/v1/shares/{id}/send-email"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": "example_id",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_sharing_shareapi_accept_share(self):
        """
        Test: files_sharing-shareapi-accept-share
        Method: POST
        Path: /ocs/v2.php/apps/files_sharing/api/v1/shares/pending/{id}
        """
        operation_id = "files_sharing-shareapi-accept-share"
        method = "post"
        path = "/ocs/v2.php/apps/files_sharing/api/v1/shares/pending/{id}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": "example_id",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_sharing_deleted_shareapi_undelete(self):
        """
        Test: files_sharing-deleted_shareapi-undelete
        Method: POST
        Path: /ocs/v2.php/apps/files_sharing/api/v1/deletedshares/{id}
        """
        operation_id = "files_sharing-deleted_shareapi-undelete"
        method = "post"
        path = "/ocs/v2.php/apps/files_sharing/api/v1/deletedshares/{id}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": "example_id",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_sharing_remote_accept_share(self):
        """
        Test: files_sharing-remote-accept-share
        Method: POST
        Path: /ocs/v2.php/apps/files_sharing/api/v1/remote_shares/pending/{id}
        """
        operation_id = "files_sharing-remote-accept-share"
        method = "post"
        path = "/ocs/v2.php/apps/files_sharing/api/v1/remote_shares/pending/{id}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_oauth2_oauth_api_get_token(self):
        """
        Test: oauth2-oauth_api-get-token
        Method: POST
        Path: /index.php/apps/oauth2/api/v1/token
        """
        operation_id = "oauth2-oauth_api-get-token"
        method = "post"
        path = "/index.php/apps/oauth2/api/v1/token"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_users_add_user(self):
        """
        Test: provisioning_api-users-add-user
        Method: POST
        Path: /ocs/v2.php/cloud/users
        """
        operation_id = "provisioning_api-users-add-user"
        method = "post"
        path = "/ocs/v2.php/cloud/users"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_users_search_by_phone_numbers(self):
        """
        Test: provisioning_api-users-search-by-phone-numbers
        Method: POST
        Path: /ocs/v2.php/cloud/users/search/by-phone
        """
        operation_id = "provisioning_api-users-search-by-phone-numbers"
        method = "post"
        path = "/ocs/v2.php/cloud/users/search/by-phone"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_users_wipe_user_devices(self):
        """
        Test: provisioning_api-users-wipe-user-devices
        Method: POST
        Path: /ocs/v2.php/cloud/users/{userId}/wipe
        """
        operation_id = "provisioning_api-users-wipe-user-devices"
        method = "post"
        path = "/ocs/v2.php/cloud/users/{userId}/wipe"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "userId": "example_userId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_users_add_to_group(self):
        """
        Test: provisioning_api-users-add-to-group
        Method: POST
        Path: /ocs/v2.php/cloud/users/{userId}/groups
        """
        operation_id = "provisioning_api-users-add-to-group"
        method = "post"
        path = "/ocs/v2.php/cloud/users/{userId}/groups"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "userId": "example_userId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_users_resend_welcome_message(self):
        """
        Test: provisioning_api-users-resend-welcome-message
        Method: POST
        Path: /ocs/v2.php/cloud/users/{userId}/welcome
        """
        operation_id = "provisioning_api-users-resend-welcome-message"
        method = "post"
        path = "/ocs/v2.php/cloud/users/{userId}/welcome"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "userId": "example_userId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_app_config_set_value(self):
        """
        Test: provisioning_api-app_config-set-value
        Method: POST
        Path: /ocs/v2.php/apps/provisioning_api/api/v1/config/apps/{app}/{key}
        """
        operation_id = "provisioning_api-app_config-set-value"
        method = "post"
        path = "/ocs/v2.php/apps/provisioning_api/api/v1/config/apps/{app}/{key}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "app": "example_app",
                "key": "example_key",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_preferences_set_preference(self):
        """
        Test: provisioning_api-preferences-set-preference
        Method: POST
        Path: /ocs/v2.php/apps/provisioning_api/api/v1/config/users/{appId}/{configKey}
        """
        operation_id = "provisioning_api-preferences-set-preference"
        method = "post"
        path = (
            "/ocs/v2.php/apps/provisioning_api/api/v1/config/users/{appId}/{configKey}"
        )

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "appId": "example_appId",
                "configKey": "example_configKey",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_preferences_set_multiple_preferences(self):
        """
        Test: provisioning_api-preferences-set-multiple-preferences
        Method: POST
        Path: /ocs/v2.php/apps/provisioning_api/api/v1/config/users/{appId}
        """
        operation_id = "provisioning_api-preferences-set-multiple-preferences"
        method = "post"
        path = "/ocs/v2.php/apps/provisioning_api/api/v1/config/users/{appId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "appId": "example_appId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_settings_declarative_settings_set_value(self):
        """
        Test: settings-declarative_settings-set-value
        Method: POST
        Path: /ocs/v2.php/settings/api/declarative/value
        """
        operation_id = "settings-declarative_settings-set-value"
        method = "post"
        path = "/ocs/v2.php/settings/api/declarative/value"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_settings_declarative_settings_set_sensitive_value(self):
        """
        Test: settings-declarative_settings-set-sensitive-value
        Method: POST
        Path: /ocs/v2.php/settings/api/declarative/value-sensitive
        """
        operation_id = "settings-declarative_settings-set-sensitive-value"
        method = "post"
        path = "/ocs/v2.php/settings/api/declarative/value-sensitive"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_theming_user_theme_set_background(self):
        """
        Test: theming-user_theme-set-background
        Method: POST
        Path: /index.php/apps/theming/background/{type}
        """
        operation_id = "theming-user_theme-set-background"
        method = "post"
        path = "/index.php/apps/theming/background/{type}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "type": "example_type",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_user_ldap_configapi_create(self):
        """
        Test: user_ldap-configapi-create
        Method: POST
        Path: /ocs/v2.php/apps/user_ldap/api/v1/config
        """
        operation_id = "user_ldap-configapi-create"
        method = "post"
        path = "/ocs/v2.php/apps/user_ldap/api/v1/config"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_webhook_listeners_webhooks_create(self):
        """
        Test: webhook_listeners-webhooks-create
        Method: POST
        Path: /ocs/v2.php/apps/webhook_listeners/api/v1/webhooks
        """
        operation_id = "webhook_listeners-webhooks-create"
        method = "post"
        path = "/ocs/v2.php/apps/webhook_listeners/api/v1/webhooks"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_webhook_listeners_webhooks_update(self):
        """
        Test: webhook_listeners-webhooks-update
        Method: POST
        Path: /ocs/v2.php/apps/webhook_listeners/api/v1/webhooks/{id}
        """
        operation_id = "webhook_listeners-webhooks-update"
        method = "post"
        path = "/ocs/v2.php/apps/webhook_listeners/api/v1/webhooks/{id}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )


class TestPut:
    """PUT endpoint tests"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test helper"""
        self.helper = APITestHelper(TEST_CONFIG)
        self.param_helper = ParameterHelper()
        self.response_helper = ResponseHelper()

    def test_core_app_password_confirm_user_password(self):
        """
        Test: core-app_password-confirm-user-password
        Method: PUT
        Path: /ocs/v2.php/core/apppassword/confirm
        """
        operation_id = "core-app_password-confirm-user-password"
        method = "put"
        path = "/ocs/v2.php/core/apppassword/confirm"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_collaboration_resources_rename_collection(self):
        """
        Test: core-collaboration_resources-rename-collection
        Method: PUT
        Path: /ocs/v2.php/collaboration/resources/collections/{collectionId}
        """
        operation_id = "core-collaboration_resources-rename-collection"
        method = "put"
        path = "/ocs/v2.php/collaboration/resources/collections/{collectionId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "collectionId": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_profile_api_set_visibility(self):
        """
        Test: core-profile_api-set-visibility
        Method: PUT
        Path: /ocs/v2.php/profile/{targetUserId}
        """
        operation_id = "core-profile_api-set-visibility"
        method = "put"
        path = "/ocs/v2.php/profile/{targetUserId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "targetUserId": "example_targetUserId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_reference_api_touch_provider(self):
        """
        Test: core-reference_api-touch-provider
        Method: PUT
        Path: /ocs/v2.php/references/provider/{providerId}
        """
        operation_id = "core-reference_api-touch-provider"
        method = "put"
        path = "/ocs/v2.php/references/provider/{providerId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "providerId": "example_providerId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_reminders_api_set(self):
        """
        Test: files_reminders-api-set
        Method: PUT
        Path: /ocs/v2.php/apps/files_reminders/api/v{version}/{fileId}
        """
        operation_id = "files_reminders-api-set"
        method = "put"
        path = "/ocs/v2.php/apps/files_reminders/api/v{version}/{fileId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "version": "example_version",
                "fileId": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_sharing_shareapi_update_share(self):
        """
        Test: files_sharing-shareapi-update-share
        Method: PUT
        Path: /ocs/v2.php/apps/files_sharing/api/v1/shares/{id}
        """
        operation_id = "files_sharing-shareapi-update-share"
        method = "put"
        path = "/ocs/v2.php/apps/files_sharing/api/v1/shares/{id}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": "example_id",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_users_edit_user(self):
        """
        Test: provisioning_api-users-edit-user
        Method: PUT
        Path: /ocs/v2.php/cloud/users/{userId}
        """
        operation_id = "provisioning_api-users-edit-user"
        method = "put"
        path = "/ocs/v2.php/cloud/users/{userId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "userId": "example_userId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_users_edit_user_multi_value(self):
        """
        Test: provisioning_api-users-edit-user-multi-value
        Method: PUT
        Path: /ocs/v2.php/cloud/users/{userId}/{collectionName}
        """
        operation_id = "provisioning_api-users-edit-user-multi-value"
        method = "put"
        path = "/ocs/v2.php/cloud/users/{userId}/{collectionName}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "userId": "example_userId",
                "collectionName": "example_collectionName",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_users_enable_user(self):
        """
        Test: provisioning_api-users-enable-user
        Method: PUT
        Path: /ocs/v2.php/cloud/users/{userId}/enable
        """
        operation_id = "provisioning_api-users-enable-user"
        method = "put"
        path = "/ocs/v2.php/cloud/users/{userId}/enable"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "userId": "example_userId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_users_disable_user(self):
        """
        Test: provisioning_api-users-disable-user
        Method: PUT
        Path: /ocs/v2.php/cloud/users/{userId}/disable
        """
        operation_id = "provisioning_api-users-disable-user"
        method = "put"
        path = "/ocs/v2.php/cloud/users/{userId}/disable"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "userId": "example_userId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_theming_user_theme_enable_theme(self):
        """
        Test: theming-user_theme-enable-theme
        Method: PUT
        Path: /ocs/v2.php/apps/theming/api/v1/theme/{themeId}/enable
        """
        operation_id = "theming-user_theme-enable-theme"
        method = "put"
        path = "/ocs/v2.php/apps/theming/api/v1/theme/{themeId}/enable"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "themeId": "example_themeId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_user_ldap_configapi_modify(self):
        """
        Test: user_ldap-configapi-modify
        Method: PUT
        Path: /ocs/v2.php/apps/user_ldap/api/v1/config/{configID}
        """
        operation_id = "user_ldap-configapi-modify"
        method = "put"
        path = "/ocs/v2.php/apps/user_ldap/api/v1/config/{configID}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "configID": "example_configID",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_user_status_heartbeat_heartbeat(self):
        """
        Test: user_status-heartbeat-heartbeat
        Method: PUT
        Path: /ocs/v2.php/apps/user_status/api/v1/heartbeat
        """
        operation_id = "user_status-heartbeat-heartbeat"
        method = "put"
        path = "/ocs/v2.php/apps/user_status/api/v1/heartbeat"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_user_status_user_status_set_status(self):
        """
        Test: user_status-user_status-set-status
        Method: PUT
        Path: /ocs/v2.php/apps/user_status/api/v1/user_status/status
        """
        operation_id = "user_status-user_status-set-status"
        method = "put"
        path = "/ocs/v2.php/apps/user_status/api/v1/user_status/status"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_user_status_user_status_set_predefined_message(self):
        """
        Test: user_status-user_status-set-predefined-message
        Method: PUT
        Path: /ocs/v2.php/apps/user_status/api/v1/user_status/message/predefined
        """
        operation_id = "user_status-user_status-set-predefined-message"
        method = "put"
        path = "/ocs/v2.php/apps/user_status/api/v1/user_status/message/predefined"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_user_status_user_status_set_custom_message(self):
        """
        Test: user_status-user_status-set-custom-message
        Method: PUT
        Path: /ocs/v2.php/apps/user_status/api/v1/user_status/message/custom
        """
        operation_id = "user_status-user_status-set-custom-message"
        method = "put"
        path = "/ocs/v2.php/apps/user_status/api/v1/user_status/message/custom"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_weather_status_weather_status_set_mode(self):
        """
        Test: weather_status-weather_status-set-mode
        Method: PUT
        Path: /ocs/v2.php/apps/weather_status/api/v1/mode
        """
        operation_id = "weather_status-weather_status-set-mode"
        method = "put"
        path = "/ocs/v2.php/apps/weather_status/api/v1/mode"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_weather_status_weather_status_use_personal_address(self):
        """
        Test: weather_status-weather_status-use-personal-address
        Method: PUT
        Path: /ocs/v2.php/apps/weather_status/api/v1/use-personal
        """
        operation_id = "weather_status-weather_status-use-personal-address"
        method = "put"
        path = "/ocs/v2.php/apps/weather_status/api/v1/use-personal"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_weather_status_weather_status_set_location(self):
        """
        Test: weather_status-weather_status-set-location
        Method: PUT
        Path: /ocs/v2.php/apps/weather_status/api/v1/location
        """
        operation_id = "weather_status-weather_status-set-location"
        method = "put"
        path = "/ocs/v2.php/apps/weather_status/api/v1/location"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_weather_status_weather_status_set_favorites(self):
        """
        Test: weather_status-weather_status-set-favorites
        Method: PUT
        Path: /ocs/v2.php/apps/weather_status/api/v1/favorites
        """
        operation_id = "weather_status-weather_status-set-favorites"
        method = "put"
        path = "/ocs/v2.php/apps/weather_status/api/v1/favorites"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )


class TestDelete:
    """DELETE endpoint tests"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test helper"""
        self.helper = APITestHelper(TEST_CONFIG)
        self.param_helper = ParameterHelper()
        self.response_helper = ResponseHelper()

    # def test_core_app_password_delete_app_password(self):
    #     """
    #     Test: core-app_password-delete-app-password
    #     Method: DELETE
    #     Path: /ocs/v2.php/core/apppassword
    #     """
    #     operation_id = "core-app_password-delete-app-password"
    #     method = "delete"
    #     path = "/ocs/v2.php/core/apppassword"

    #     # Load test cases
    #     test_cases = TEST_DATA.get(
    #         operation_id,
    #         [
    #             TestCase(
    #                 description="Default test case",
    #                 assertions=ResponseAssertion(status_code=200),
    #             )
    #         ],
    #     )

    #     for i, test_case in enumerate(test_cases):
    #         # Skip if needed
    #         if test_case.skip:
    #             pytest.skip(test_case.skip_reason)

    #         # Extract parameters
    #         path_params, query_params, headers, body = (
    #             self.param_helper.extract_parameters(test_case)
    #         )

    #         # Execute request
    #         try:
    #             response = self.helper.execute_request(
    #                 method=method,
    #                 path=path,
    #                 path_params=path_params,
    #                 query_params=query_params,
    #                 headers=headers,
    #                 body=body,
    #             )
    #         except Exception as e:
    #             pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

    #         # Assertions
    #         test_desc = f"Test {i}: {test_case.description}"

    #         if test_case.assertions.status_code:
    #             self.response_helper.assert_status(
    #                 response, test_case.assertions.status_code, test_desc
    #             )

    #         if test_case.assertions.json_contains:
    #             self.response_helper.assert_json_contains(
    #                 response, test_case.assertions.json_contains, test_desc
    #             )

    #         if test_case.assertions.headers_contain:
    #             self.response_helper.assert_headers(
    #                 response, test_case.assertions.headers_contain, test_desc
    #             )

    def test_core_collaboration_resources_remove_resource(self):
        """
        Test: core-collaboration_resources-remove-resource
        Method: DELETE
        Path: /ocs/v2.php/collaboration/resources/collections/{collectionId}
        """
        operation_id = "core-collaboration_resources-remove-resource"
        method = "delete"
        path = "/ocs/v2.php/collaboration/resources/collections/{collectionId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "collectionId": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_task_processing_api_delete_task(self):
        """
        Test: core-task_processing_api-delete-task
        Method: DELETE
        Path: /ocs/v2.php/taskprocessing/task/{id}
        """
        operation_id = "core-task_processing_api-delete-task"
        method = "delete"
        path = "/ocs/v2.php/taskprocessing/task/{id}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_text_processing_api_delete_task(self):
        """
        Test: core-text_processing_api-delete-task
        Method: DELETE
        Path: /ocs/v2.php/textprocessing/task/{id}
        """
        operation_id = "core-text_processing_api-delete-task"
        method = "delete"
        path = "/ocs/v2.php/textprocessing/task/{id}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_core_text_to_image_api_delete_task(self):
        """
        Test: core-text_to_image_api-delete-task
        Method: DELETE
        Path: /ocs/v2.php/text2image/task/{id}
        """
        operation_id = "core-text_to_image_api-delete-task"
        method = "delete"
        path = "/ocs/v2.php/text2image/task/{id}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_dav_out_of_office_clear_out_of_office(self):
        """
        Test: dav-out_of_office-clear-out-of-office
        Method: DELETE
        Path: /ocs/v2.php/apps/dav/api/v1/outOfOffice/{userId}
        """
        operation_id = "dav-out_of_office-clear-out-of-office"
        method = "delete"
        path = "/ocs/v2.php/apps/dav/api/v1/outOfOffice/{userId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "userId": "example_userId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_transfer_ownership_reject(self):
        """
        Test: files-transfer_ownership-reject
        Method: DELETE
        Path: /ocs/v2.php/apps/files/api/v1/transferownership/{id}
        """
        operation_id = "files-transfer_ownership-reject"
        method = "delete"
        path = "/ocs/v2.php/apps/files/api/v1/transferownership/{id}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_reminders_api_remove(self):
        """
        Test: files_reminders-api-remove
        Method: DELETE
        Path: /ocs/v2.php/apps/files_reminders/api/v{version}/{fileId}
        """
        operation_id = "files_reminders-api-remove"
        method = "delete"
        path = "/ocs/v2.php/apps/files_reminders/api/v{version}/{fileId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "version": "example_version",
                "fileId": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_sharing_shareapi_delete_share(self):
        """
        Test: files_sharing-shareapi-delete-share
        Method: DELETE
        Path: /ocs/v2.php/apps/files_sharing/api/v1/shares/{id}
        """
        operation_id = "files_sharing-shareapi-delete-share"
        method = "delete"
        path = "/ocs/v2.php/apps/files_sharing/api/v1/shares/{id}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": "example_id",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_sharing_remote_decline_share(self):
        """
        Test: files_sharing-remote-decline-share
        Method: DELETE
        Path: /ocs/v2.php/apps/files_sharing/api/v1/remote_shares/pending/{id}
        """
        operation_id = "files_sharing-remote-decline-share"
        method = "delete"
        path = "/ocs/v2.php/apps/files_sharing/api/v1/remote_shares/pending/{id}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_files_sharing_remote_unshare(self):
        """
        Test: files_sharing-remote-unshare
        Method: DELETE
        Path: /ocs/v2.php/apps/files_sharing/api/v1/remote_shares/{id}
        """
        operation_id = "files_sharing-remote-unshare"
        method = "delete"
        path = "/ocs/v2.php/apps/files_sharing/api/v1/remote_shares/{id}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_users_delete_user(self):
        """
        Test: provisioning_api-users-delete-user
        Method: DELETE
        Path: /ocs/v2.php/cloud/users/{userId}
        """
        operation_id = "provisioning_api-users-delete-user"
        method = "delete"
        path = "/ocs/v2.php/cloud/users/{userId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "userId": "example_userId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_users_remove_from_group(self):
        """
        Test: provisioning_api-users-remove-from-group
        Method: DELETE
        Path: /ocs/v2.php/cloud/users/{userId}/groups
        """
        operation_id = "provisioning_api-users-remove-from-group"
        method = "delete"
        path = "/ocs/v2.php/cloud/users/{userId}/groups"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "userId": "example_userId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_preferences_delete_preference(self):
        """
        Test: provisioning_api-preferences-delete-preference
        Method: DELETE
        Path: /ocs/v2.php/apps/provisioning_api/api/v1/config/users/{appId}/{configKey}
        """
        operation_id = "provisioning_api-preferences-delete-preference"
        method = "delete"
        path = (
            "/ocs/v2.php/apps/provisioning_api/api/v1/config/users/{appId}/{configKey}"
        )

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "appId": "example_appId",
                "configKey": "example_configKey",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_provisioning_api_preferences_delete_multiple_preference(self):
        """
        Test: provisioning_api-preferences-delete-multiple-preference
        Method: DELETE
        Path: /ocs/v2.php/apps/provisioning_api/api/v1/config/users/{appId}
        """
        operation_id = "provisioning_api-preferences-delete-multiple-preference"
        method = "delete"
        path = "/ocs/v2.php/apps/provisioning_api/api/v1/config/users/{appId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "appId": "example_appId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_theming_user_theme_delete_background(self):
        """
        Test: theming-user_theme-delete-background
        Method: DELETE
        Path: /index.php/apps/theming/background/custom
        """
        operation_id = "theming-user_theme-delete-background"
        method = "delete"
        path = "/index.php/apps/theming/background/custom"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_theming_user_theme_disable_theme(self):
        """
        Test: theming-user_theme-disable-theme
        Method: DELETE
        Path: /ocs/v2.php/apps/theming/api/v1/theme/{themeId}
        """
        operation_id = "theming-user_theme-disable-theme"
        method = "delete"
        path = "/ocs/v2.php/apps/theming/api/v1/theme/{themeId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "themeId": "example_themeId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_user_ldap_configapi_delete(self):
        """
        Test: user_ldap-configapi-delete
        Method: DELETE
        Path: /ocs/v2.php/apps/user_ldap/api/v1/config/{configID}
        """
        operation_id = "user_ldap-configapi-delete"
        method = "delete"
        path = "/ocs/v2.php/apps/user_ldap/api/v1/config/{configID}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "configID": "example_configID",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_user_status_user_status_clear_message(self):
        """
        Test: user_status-user_status-clear-message
        Method: DELETE
        Path: /ocs/v2.php/apps/user_status/api/v1/user_status/message
        """
        operation_id = "user_status-user_status-clear-message"
        method = "delete"
        path = "/ocs/v2.php/apps/user_status/api/v1/user_status/message"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_user_status_user_status_revert_status(self):
        """
        Test: user_status-user_status-revert-status
        Method: DELETE
        Path: /ocs/v2.php/apps/user_status/api/v1/user_status/revert/{messageId}
        """
        operation_id = "user_status-user_status-revert-status"
        method = "delete"
        path = "/ocs/v2.php/apps/user_status/api/v1/user_status/revert/{messageId}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "messageId": "example_messageId",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_webhook_listeners_webhooks_destroy(self):
        """
        Test: webhook_listeners-webhooks-destroy
        Method: DELETE
        Path: /ocs/v2.php/apps/webhook_listeners/api/v1/webhooks/{id}
        """
        operation_id = "webhook_listeners-webhooks-destroy"
        method = "delete"
        path = "/ocs/v2.php/apps/webhook_listeners/api/v1/webhooks/{id}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "id": 1,
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )

    def test_webhook_listeners_webhooks_delete_by_app_id(self):
        """
        Test: webhook_listeners-webhooks-delete-by-app-id
        Method: DELETE
        Path: /ocs/v2.php/apps/webhook_listeners/api/v1/webhooks/byappid/{appid}
        """
        operation_id = "webhook_listeners-webhooks-delete-by-app-id"
        method = "delete"
        path = "/ocs/v2.php/apps/webhook_listeners/api/v1/webhooks/byappid/{appid}"

        # Load test cases
        test_cases = TEST_DATA.get(
            operation_id,
            [
                TestCase(
                    description="Default test case",
                    assertions=ResponseAssertion(status_code=200),
                )
            ],
        )

        for i, test_case in enumerate(test_cases):
            # Skip if needed
            if test_case.skip:
                pytest.skip(test_case.skip_reason)

            # Extract parameters
            path_params, query_params, headers, body = (
                self.param_helper.extract_parameters(test_case)
            )

            # Set default path parameters if not provided
            path_defaults = {
                "appid": "example_appid",
            }
            path_params = self.param_helper.set_defaults(path_params, path_defaults)

            # Execute request
            try:
                response = self.helper.execute_request(
                    method=method,
                    path=path,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    body=body,
                )
            except Exception as e:
                pytest.fail(f"Request failed: {test_case.description} - {str(e)}")

            # Assertions
            test_desc = f"Test {i}: {test_case.description}"

            if test_case.assertions.status_code:
                self.response_helper.assert_status(
                    response, test_case.assertions.status_code, test_desc
                )

            if test_case.assertions.json_contains:
                self.response_helper.assert_json_contains(
                    response, test_case.assertions.json_contains, test_desc
                )

            if test_case.assertions.headers_contain:
                self.response_helper.assert_headers(
                    response, test_case.assertions.headers_contain, test_desc
                )
