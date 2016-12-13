import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--site",
        action="store",
        default=None,
        help="add the name of an app"
    )

@pytest.fixture
def site(request):
    return request.config.getoption("--site")
